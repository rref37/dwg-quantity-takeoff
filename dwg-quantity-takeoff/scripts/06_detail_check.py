# -*- coding: utf-8 -*-
"""详图陷阱检测：某类部件是“每个房间都画”，还是“只画一个典型房间（详图）”？
把块的 X 坐标按开间宽分箱，看它散布在几个开间里。

用法:
  python 06_detail_check.py 图.dxf --name "块名" --bin 3600
  python 06_detail_check.py 图.dxf --layer EM-强电 --bin 3600
  python 06_detail_check.py 图.dxf --name "块名" --out detail.txt   # 同时保存报告

判读:
  有部件的开间数 ≈ 房间或商铺数  -> 全平面布点，总数即真实总数
  只集中在 1 到 2 个开间          -> 是详图，真实总数 = 详图数 × 房间数
"""
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import block_refs, emit, load, setup_stdout, xy  # noqa: E402


def main():
    setup_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dxf", help="DXF 文件")
    ap.add_argument("--name", help="按真实块名筛选")
    ap.add_argument("--layer", help="按图层筛选")
    ap.add_argument("--bin", type=float, default=3600, help="开间宽度（模型单位，常为 3600 mm）")
    ap.add_argument("--out", help="同时把报告保存到此文件")
    a = ap.parse_args()

    br = block_refs(load(a.dxf))
    if a.name:
        br = br[br["_name"] == a.name]
    if a.layer:
        br = br[br["_layer"] == a.layer]
    xs = sorted(p[0] for p in (xy(v) for v in br["Position"]) if p)

    out = []
    if not xs:
        out.append("没有匹配的块。")
    else:
        out.append("匹配 %d 个；X 跨度 %.1f 米（%.0f 到 %.0f）" %
                   (len(xs), (xs[-1] - xs[0]) / 1000, xs[0], xs[-1]))
        hist = collections.Counter(int((x - xs[0]) // a.bin) for x in xs)
        out.append("\n按 %.0f 分箱:" % a.bin)
        for k in sorted(hist):
            out.append("  开间%3d : %3d  %s" % (k, hist[k], "#" * min(hist[k], 60)))
        out.append("\n有部件的开间数: %d" % len(hist))
        out.append("=> 若接近房间数：全平面布点，总数即真实数量。"
                   "若只有 1 到 2 个：是详图，真实数量 = 详图数 × 房间数。")
    emit("\n".join(out), a.out)


if __name__ == "__main__":
    main()
