# -*- coding: utf-8 -*-
"""方法①数据直读：按真实块名（BlockTableRecord）和图层统计图块数量。

用法:
  python 02_count.py 图.dxf                          # 块名 × 图层 直方图
  python 02_count.py 图.dxf --by layer               # 只按图层汇总
  python 02_count.py 图.dxf --layers EM-强电,RC-LIGHT  # 只统计这些图层
  python 02_count.py 图.dxf --map types.json         # {"块名": "类型"}，汇总到设备类型
  python 02_count.py 图.dxf --out count.txt          # 同时保存报告
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import block_refs, emit, load, setup_stdout  # noqa: E402


def main():
    setup_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dxf", help="DXF 文件（DWG 先用 00_dwg_to_dxf.py 转换）")
    ap.add_argument("--by", choices=["name", "layer", "both"], default="both")
    ap.add_argument("--layers", help="逗号分隔的图层名，只统计这些图层")
    ap.add_argument("--map", help="JSON 文件：{块名: 类型}")
    ap.add_argument("--out", help="同时把报告保存到此文件")
    a = ap.parse_args()

    br = block_refs(load(a.dxf))
    if a.layers:
        br = br[br["_layer"].isin(set(a.layers.split(",")))]

    out = []
    if a.map:
        with open(a.map, encoding="utf-8") as f:
            m = json.load(f)
        cnt = collections.Counter(m[nm] for nm in br["_name"] if nm in m)
        out.append("=== 按类型（map）汇总 ===")
        for t, c in cnt.most_common():
            out.append("  %5d  %s" % (c, t))
        unmapped = collections.Counter(nm for nm in br["_name"] if nm not in m)
        out.append("\n--- 未映射块名（前 30，可补进 map） ---")
        for nm, c in unmapped.most_common(30):
            out.append("  %5d  %s" % (c, nm))
    else:
        if a.by in ("layer", "both"):
            out.append("=== 按图层 ===")
            for layer, c in br["_layer"].value_counts().items():
                out.append("  %5d  %s" % (c, layer))
        if a.by in ("name", "both"):
            out.append("\n=== 按真实块名（BlockTableRecord） ===")
            for nm, c in br["_name"].value_counts().head(80).items():
                out.append("  %5d  %s" % (c, nm))
    emit("\n".join(out), a.out)


if __name__ == "__main__":
    main()
