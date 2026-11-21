# -*- coding: utf-8 -*-
"""共享工具：读取 DXF，把每个实体展开成一行 DataFrame。各统计脚本都 import 它。

输入是 DXF 文件（DWG 先用 00_dwg_to_dxf.py 转换）。load() 返回的表，列名如下：

  Description        实体类型，如 "<AcDbBlockReference>"、"<AcDbLine>"
  Layer              图层名
  BlockId            所属块定义的名字；模型空间为 ""
  Space              "model"（模型空间）、"block"（块定义内）、"paper"（图纸空间，仅视口）
  BlockTableRecord   块引用的真实块名（INSERT）
  Position           插入点，"x, y, z" 字符串（块引用、文字）
  Text String        文字内容（TEXT、MTEXT）
  StartPoint, EndPoint, Center   "x, y, z" 字符串
  Radius             半径（浮点）
  StartAngle, EndAngle           弧度（ARC）
  ViewCenter, ViewHeight, Width, Height, Number   视口参数（VIEWPORT）
"""
import collections
import math
import re
import sys

import pandas as pd

GEOM_TYPES = {
    "<AcDbLine>", "<AcDbPolyline>", "<AcDbArc>", "<AcDbCircle>", "<AcDbEllipse>",
    "<AcDbSpline>", "<AcDbText>", "<AcDbMText>", "<AcDbHatch>", "<AcDbSolid>",
    "<AcDbPoint>", "<AcDbAttributeDefinition>",
}

DXF_TO_DESC = {
    "LINE": "<AcDbLine>",
    "LWPOLYLINE": "<AcDbPolyline>",
    "POLYLINE": "<AcDbPolyline>",
    "ARC": "<AcDbArc>",
    "CIRCLE": "<AcDbCircle>",
    "ELLIPSE": "<AcDbEllipse>",
    "SPLINE": "<AcDbSpline>",
    "TEXT": "<AcDbText>",
    "MTEXT": "<AcDbMText>",
    "HATCH": "<AcDbHatch>",
    "SOLID": "<AcDbSolid>",
    "POINT": "<AcDbPoint>",
    "ATTDEF": "<AcDbAttributeDefinition>",
    "INSERT": "<AcDbBlockReference>",
    "VIEWPORT": "<AcDbViewport>",
    "ACAD_PROXY_ENTITY": "<AcDbProxyEntity>",
}


def setup_stdout():
    """控制台输出改为 UTF-8，避免 GBK 终端显示乱码。"""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def emit(text, out=None):
    """打印报告；给了 out 就同时保存到文件。"""
    print(text)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print("\n已保存:", out)


def _xyz(v):
    return "%.6f, %.6f, %.6f" % (float(v.x), float(v.y), float(getattr(v, "z", 0.0)))


def _row(e, block_id, space):
    """把一个 ezdxf 实体转成一行字典；不关心的类型返回 None。"""
    t = e.dxftype()
    desc = DXF_TO_DESC.get(t)
    if desc is None:
        return None
    d = e.dxf
    r = {"Description": desc, "Layer": d.layer, "BlockId": block_id, "Space": space}
    if t == "INSERT":
        r["BlockTableRecord"] = d.name
        r["Position"] = _xyz(d.insert)
    elif t == "LINE":
        r["StartPoint"] = _xyz(d.start)
        r["EndPoint"] = _xyz(d.end)
    elif t == "CIRCLE":
        r["Center"] = _xyz(d.center)
        r["Radius"] = float(d.radius)
    elif t == "ARC":
        r["Center"] = _xyz(d.center)
        r["Radius"] = float(d.radius)
        r["StartAngle"] = math.radians(d.start_angle)  # DXF 存的是角度，统一成弧度
        r["EndAngle"] = math.radians(d.end_angle)
    elif t in ("TEXT", "ATTDEF"):
        r["Position"] = _xyz(d.insert)
        if t == "TEXT":
            r["Text String"] = d.text
    elif t == "MTEXT":
        r["Position"] = _xyz(d.insert)
        r["Text String"] = e.plain_text()
    elif t == "VIEWPORT":
        r["ViewCenter"] = _xyz(d.view_center_point)
        r["ViewHeight"] = float(d.view_height)
        r["Width"] = float(d.width)
        r["Height"] = float(d.height)
        r["Number"] = int(d.id)
    return r


def load(path):
    """读取 DXF，返回每个实体一行的 DataFrame（列说明见文件头）。"""
    import ezdxf
    try:
        doc = ezdxf.readfile(path)
    except ezdxf.DXFStructureError:
        # 文件结构有损坏时，用 recover 模式尽量读出来
        from ezdxf import recover
        doc, _ = recover.readfile(path)
    rows = []
    for e in doc.modelspace():
        r = _row(e, "", "model")
        if r:
            rows.append(r)
    for blk in doc.blocks:
        # 跳过布局的占位块，保留其他块定义（包括匿名块 A$C... 等）
        if blk.name.upper().startswith(("*MODEL_SPACE", "*PAPER_SPACE")):
            continue
        for e in blk:
            r = _row(e, blk.name, "block")
            if r:
                rows.append(r)
    for layout in doc.layouts:
        if layout.name == "Model":
            continue
        for e in layout.query("VIEWPORT"):
            r = _row(e, "", "paper")
            if r:
                rows.append(r)
    return pd.DataFrame(rows)


def xy(v):
    """'x, y, z' -> (x, y)；不是坐标字符串则返回 None。"""
    if not isinstance(v, str):
        return None
    n = re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", v)
    return (float(n[0]), float(n[1])) if len(n) >= 2 else None


def pt2(v):
    """同 xy，但返回 list，给绘图用。"""
    try:
        return [float(x) for x in str(v).split(",")[:2]]
    except Exception:
        return None


def gettext(row):
    """取一行的文字内容；没有则返回空字符串。"""
    val = row.get("Text String")
    if isinstance(val, str) and val.strip():
        return val.strip()
    return ""


def block_refs(df):
    """返回块引用子表，附带 _name（真实块名）和 _layer（图层）两列。"""
    br = df[df["Description"] == "<AcDbBlockReference>"].copy()
    br["_name"] = br["BlockTableRecord"].astype(str)
    br["_layer"] = br["Layer"].astype(str)
    return br


def block_def_signatures(df):
    """按 BlockId 把每个块定义的子实体几何聚成指纹签名。
    返回 {块名: 签名元组}，签名如 (('Arc', 16), ('Circle', 1), ('Line', 4))。"""
    fp = collections.defaultdict(collections.Counter)
    for d, b in zip(df["Description"], df["BlockId"]):
        if d in GEOM_TYPES:
            fp[b][d] += 1
    return {
        name: tuple(sorted((k.strip("<>").replace("AcDb", ""), v) for k, v in c.items()))
        for name, c in fp.items()
    }
