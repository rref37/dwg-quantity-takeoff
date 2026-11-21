# -*- coding: utf-8 -*-
"""方法③渲染：把块符号、图例区或任意区域，从几何重绘成 PNG（带文字），用图片人工认部件。

用法:
  python 04_render.py 图.dxf block "块名" -o sym.png            # 单个块符号
  python 04_render.py 图.dxf legend "图例" -o legend.png         # 按关键字框出图例区
  python 04_render.py 图.dxf region -18000 60000 -18000 8000 -o area.png
        # 区域参数依次为 x0 x1 y0 y1，负数直接写即可

说明：块符号按块定义的几何，平移到插入点重绘。中文字体默认用 Microsoft YaHei，
Windows 之外的系统请先安装同名字体或改 FONT_CANDIDATES。
"""
import argparse
import collections
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Arc, Circle  # noqa: E402

from _common import emit, gettext, load, pt2, setup_stdout, xy  # noqa: E402

FONT_CANDIDATES = ["Microsoft YaHei", "SimHei", "SimSun", "DejaVu Sans"]
plt.rcParams["font.sans-serif"] = FONT_CANDIDATES
plt.rcParams["axes.unicode_minus"] = False

TEXT_TYPES = ("<AcDbText>", "<AcDbMText>")


def block_local_geom(df):
    """{块名: [('L', 起点, 终点) | ('C', 圆心, 半径) | ('A', 圆心, 半径, 起角, 止角)]}，局部坐标。"""
    g = collections.defaultdict(list)
    for i, d, b in zip(df.index, df["Description"], df["BlockId"]):
        if not b:
            continue
        if d == "<AcDbLine>":
            p1, p2 = pt2(df.at[i, "StartPoint"]), pt2(df.at[i, "EndPoint"])
            if p1 and p2:
                g[b].append(("L", p1, p2))
        elif d == "<AcDbCircle>":
            c, r = pt2(df.at[i, "Center"]), df.at[i, "Radius"]
            if c and pd.notna(r):
                g[b].append(("C", c, float(r)))
        elif d == "<AcDbArc>":
            c, r = pt2(df.at[i, "Center"]), df.at[i, "Radius"]
            sa, ea = df.at[i, "StartAngle"], df.at[i, "EndAngle"]
            if c and pd.notna(r) and pd.notna(sa) and pd.notna(ea):
                g[b].append(("A", c, float(r), float(sa), float(ea)))
    return g


def draw_geom(ax, geom, ox, oy):
    for e in geom:
        if e[0] == "L":
            (ax1, ay1), (ax2, ay2) = e[1], e[2]
            ax.plot([ax1 + ox, ax2 + ox], [ay1 + oy, ay2 + oy], "k-", lw=0.6)
        elif e[0] == "C":
            (cx, cy), r = e[1], e[2]
            ax.add_patch(Circle((cx + ox, cy + oy), r, fill=False, lw=0.6))
        elif e[0] == "A":
            (cx, cy), r, sa, ea = e[1], e[2], e[3], e[4]
            ax.add_patch(Arc((cx + ox, cy + oy), 2 * r, 2 * r, angle=0,
                             theta1=math.degrees(sa), theta2=math.degrees(ea), lw=0.6))


def render_region(df, defs, x0, x1, y0, y1, out, title, figsize=(13, 9)):
    fig, ax = plt.subplots(figsize=figsize)

    def inside(p):
        return p and x0 <= p[0] <= x1 and y0 <= p[1] <= y1

    for idx in df.index[df["Description"] == "<AcDbBlockReference>"]:
        p = xy(df.at[idx, "Position"])
        geom = defs.get(df.at[idx, "BlockTableRecord"])
        if geom and inside(p):
            draw_geom(ax, geom, p[0], p[1])
    for idx in df.index[df["Description"].isin(TEXT_TYPES)]:
        p = xy(df.at[idx, "Position"])
        t = gettext(df.loc[idx])
        if t and inside(p):
            ax.text(p[0], p[1], t[:18], fontsize=5, va="bottom")
    ax.set_aspect("equal")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_title(title, fontsize=12)
    ax.axis("off")
    plt.savefig(out, dpi=155, bbox_inches="tight")
    plt.close()
    print("已保存", out)


def main():
    setup_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dxf", help="DXF 文件")
    ap.add_argument("mode", choices=["block", "legend", "region"])
    ap.add_argument("args", nargs="*",
                    help="block: 块名 | legend: 关键字 | region: x0 x1 y0 y1")
    ap.add_argument("-o", "--out", default="render.png", help="输出 PNG 路径")
    a = ap.parse_args()

    df = load(a.dxf)
    defs = block_local_geom(df)

    if a.mode == "block":
        if not a.args:
            sys.exit("block 模式需要块名")
        name = a.args[0]
        geom = defs.get(name)
        if not geom:
            sys.exit("块无几何或不存在: %s" % name)
        fig, ax = plt.subplots(figsize=(3, 3))
        draw_geom(ax, geom, 0, 0)
        ax.set_aspect("equal")
        ax.autoscale_view()
        ax.set_title(name, fontsize=9)
        ax.axis("off")
        plt.savefig(a.out, dpi=140, bbox_inches="tight")
        plt.close()
        print("已保存", a.out)

    elif a.mode == "region":
        if len(a.args) != 4:
            sys.exit("region 模式需要 4 个数: x0 x1 y0 y1")
        x0, x1, y0, y1 = (float(v) for v in a.args)
        render_region(df, defs, x0, x1, y0, y1, a.out, "region")

    elif a.mode == "legend":
        if not a.args:
            sys.exit("legend 模式需要关键字")
        kw = a.args[0]
        pts = []
        for idx in df.index[df["Description"].isin(TEXT_TYPES)]:
            p = xy(df.at[idx, "Position"])
            if p and kw in gettext(df.loc[idx]):
                pts.append(p)
        if not pts:
            sys.exit("没找到含 '%s' 的文字。可改用 region 模式。" % kw)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        # 图例表一般在锚点右下方，外扩一个范围
        x0, x1 = min(xs) - 3000, max(xs) + 25000
        y0, y1 = min(ys) - 22000, max(ys) + 3000
        render_region(df, defs, x0, x1, y0, y1, a.out, "图例: " + kw)


if __name__ == "__main__":
    main()
