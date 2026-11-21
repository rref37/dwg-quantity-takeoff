# -*- coding: utf-8 -*-
"""方法④(给排水/天正专用): 从 DXF 里把代理对象(AcDbProxyEntity / ACAD_PROXY_ENTITY)
缓存的"proxy graphics"炸成真实几何(线/弧/圆/多段线/文字),用来:
  - 按图层汇总管线长度(给排水 PIPE-* 等,DwgExporter 读不到的几何)
  - 渲染真实平面(代理对象在 DDC 导出里只是一行,渲不出来)

为什么需要: DDC DwgExporter 把每个天正自定义对象导成一行 <AcDbProxyEntity>,不展开缓存图形,
所以管线长度量不到、04_render 画不出平面。ezdxf 能直接读代理对象缓存的显示几何,不需要原插件。
DwgExporter 与 ODA File Converter 不是同一个程序,本仓库都不附带。

前置: DWG 或 DXF。本脚本可直接吃 DWG(用 ezdxf 的 odafc 插件调用本机 ODA File Converter,不要求同时安装 AutoCAD)。
  ODA 程序需自行下载并遵守其条款,非会员仅限非商业用途,见仓库 README。
  也可先手动转 DXF:
  1. ODA File Converter: DWG→DXF, 选 "ACAD2018 ASCII DXF"。
  2. 已获授权的天正/AutoCAD: 原图 `另存为 → AutoCAD DXF`(是另存原图,不是转T3——转T3会炸开就没代理了)。

⚠️⚠️ 成败关键:代理对象里**必须有缓存的 proxy graphics(显示几何快照)**,本脚本才能取出几何。
  - 若原 DWG 保存时 PROXYGRAPHICS=0(天正常见默认),代理只存自定义数据、不存几何快照 →
    没有原插件(天正 ARX)谁也解不出, `virtual_entities()` 返回空。脚本会明确报"N 个空代理"。
  - 这种情况**只能回到天正**: "图形导出→T3" 炸开成普通实体后再 DwgExporter/本脚本。
  - 这种情况下管长无法从图中取得，只能回到天正处理。设备/洁具个数不受影响(是正常块)。

用法:
  python 08_proxy_to_geom.py 图.dwg                      # DWG直接吃(odafc自动转)
  python 08_proxy_to_geom.py 图.dxf --layers PIPE-给水,PIPE-污水
  python 08_proxy_to_geom.py 图.dxf --xlsx 管长.xlsx
  python 08_proxy_to_geom.py 图.dxf --render area.png --window x0 x1 y0 y1
"""
import argparse, math, sys, collections

def _need_ezdxf():
    try:
        import ezdxf  # noqa
    except ImportError:
        sys.exit("缺 ezdxf: pip install ezdxf")
    return __import__("ezdxf")

def iter_virtual(msp):
    """遍历模型空间,把代理对象展开为虚拟实体;普通实体原样产出。
    产出 (dxftype, layer, entity)。代理无缓存几何时产出 PROXY_EMPTY,异常时 PROXY_FAIL。"""
    for e in msp:
        t = e.dxftype()
        if t in ("ACAD_PROXY_ENTITY", "ACAD_PROXY_OBJECT"):
            player = getattr(e.dxf, "layer", "?")
            try:
                ves = list(e.virtual_entities())
            except Exception:
                yield "PROXY_FAIL", player, e; continue
            if not ves:
                yield "PROXY_EMPTY", player, e; continue
            for ve in ves:
                lay = getattr(ve.dxf, "layer", "0")
                if lay in ("0", "BYBLOCK"):
                    lay = player  # 子实体常 BYBLOCK,继承代理图层
                yield ve.dxftype(), lay, ve
        else:
            yield t, getattr(e.dxf, "layer", "0"), e

def load_any(path):
    """DWG 经 odafc 自动转 DXF;DXF 直接读。"""
    ezdxf = _need_ezdxf()
    if path.lower().endswith(".dwg"):
        from ezdxf.addons import odafc
        if not odafc.is_installed():
            sys.exit("DWG 输入需使用者自行安装的 ODA File Converter"
                     "（非会员仅限非商业用途）: https://www.opendesign.com/guestfiles/oda_file_converter\n"
                     "装好后若仍找不到,设 ezdxf.options['odafc-addon']['win_exec_path']=exe 路径。")
        return odafc.readfile(path)
    return ezdxf.readfile(path)

def seg_length(t, e):
    """线/多段线/弧 的长度;其它返回 0。"""
    try:
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            return math.dist((a.x, a.y), (b.x, b.y))
        if t in ("LWPOLYLINE", "POLYLINE"):
            pts = [(p[0], p[1]) for p in e.get_points("xy")] if t == "LWPOLYLINE" \
                  else [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
            L = sum(math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1))
            if getattr(e, "closed", False) and len(pts) > 2:
                L += math.dist(pts[-1], pts[0])
            return L
        if t == "ARC":
            r = e.dxf.radius
            sweep = (e.dxf.end_angle - e.dxf.start_angle) % 360
            return math.radians(sweep) * r
    except Exception:
        return 0.0
    return 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf", help="DWG 或 DXF 文件")
    ap.add_argument("--layers", help="逗号分隔,只统计这些图层")
    ap.add_argument("--xlsx", help="导出每段几何到此 Excel")
    ap.add_argument("--render", help="渲染到此 PNG")
    ap.add_argument("--window", nargs=4, type=float, metavar=("X0","X1","Y0","Y1"))
    a = ap.parse_args()
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # GBK 控制台兼容
    except Exception: pass
    doc = load_any(a.dxf)
    msp = doc.modelspace()
    only = set(a.layers.split(",")) if a.layers else None

    length_by_layer = collections.defaultdict(float)
    count_by_layer_type = collections.Counter()
    proxy_fail = 0; proxy_empty = 0
    rows = []
    for t, layer, e in iter_virtual(msp):
        if t == "PROXY_FAIL":
            proxy_fail += 1; continue
        if t == "PROXY_EMPTY":
            proxy_empty += 1; continue
        if only and layer not in only:
            continue
        L = seg_length(t, e)
        length_by_layer[layer] += L
        count_by_layer_type[(layer, t)] += 1
        if a.xlsx:
            rows.append({"Layer": layer, "Description": f"<{t}>", "Length": round(L, 1)})

    print("=== 按图层管线长度(图上平面长,mm;非实际敷设量) ===")
    for lay, L in sorted(length_by_layer.items(), key=lambda kv: -kv[1]):
        if L > 0:
            print(f"  {lay:<18} {L/1000:>12.2f} m")
    if proxy_fail:
        print(f"\n[!] {proxy_fail} 个代理图形解析失败(未计入)")
    if proxy_empty:
        print(f"\n[X] {proxy_empty} 个代理对象无缓存几何(virtual_entities 为空)。")
        print("   原 DWG 保存时未存 proxy graphics → 没有原插件(如天正 ARX)解不出。")
        print("   解法:回天正『图形导出→T3』炸开成普通实体后,再跑 DwgExporter / 本脚本。")
        print("   注:设备/洁具等正常块引用不受影响,可照常计数。")
    print("\n=== 图层×类型 计数(前30) ===")
    for (lay, t), n in count_by_layer_type.most_common(30):
        print(f"  {lay:<18} {t:<14} {n}")

    if a.xlsx:
        import pandas as pd
        with pd.ExcelWriter(a.xlsx, engine="xlsxwriter") as xw:
            pd.DataFrame(rows).to_excel(xw, index=False, sheet_name="proxy_geom")
        print("\nsaved", a.xlsx)

    if a.render:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Arc as MArc, Circle as MCircle
        plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
        x0, x1, y0, y1 = a.window if a.window else (-1e12, 1e12, -1e12, 1e12)
        fig, ax = plt.subplots(figsize=(13, 9))
        for t, layer, e in iter_virtual(msp):
            if only and layer not in only:
                continue
            try:
                if t == "LINE":
                    s, en = e.dxf.start, e.dxf.end
                    if x0 <= s.x <= x1 and y0 <= s.y <= y1:
                        ax.plot([s.x, en.x], [s.y, en.y], "k-", lw=0.5)
                elif t == "LWPOLYLINE":
                    pts = [(p[0], p[1]) for p in e.get_points("xy")]
                    if pts and x0 <= pts[0][0] <= x1 and y0 <= pts[0][1] <= y1:
                        xs, ys = zip(*pts); ax.plot(xs, ys, "k-", lw=0.5)
                elif t == "CIRCLE":
                    c = e.dxf.center
                    if x0 <= c.x <= x1 and y0 <= c.y <= y1:
                        ax.add_patch(MCircle((c.x, c.y), e.dxf.radius, fill=False, lw=0.5))
                elif t == "ARC":
                    c = e.dxf.center
                    if x0 <= c.x <= x1 and y0 <= c.y <= y1:
                        ax.add_patch(MArc((c.x, c.y), 2*e.dxf.radius, 2*e.dxf.radius,
                                          theta1=e.dxf.start_angle, theta2=e.dxf.end_angle, lw=0.5))
                elif t in ("TEXT", "MTEXT"):
                    p = e.dxf.insert
                    if x0 <= p.x <= x1 and y0 <= p.y <= y1:
                        ax.text(p.x, p.y, (e.dxf.text if t == "TEXT" else e.text)[:18], fontsize=4)
            except Exception:
                continue
        ax.set_aspect("equal"); ax.axis("off")
        if a.window: ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
        plt.savefig(a.render, dpi=155, bbox_inches="tight"); plt.close()
        print("saved", a.render)

if __name__ == "__main__":
    main()
