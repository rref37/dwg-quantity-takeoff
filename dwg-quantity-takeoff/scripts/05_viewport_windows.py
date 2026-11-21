# -*- coding: utf-8 -*-
"""图框窗口去重：用图纸视口的 ViewCenter 和 ViewHeight 框出真实平面区，
统计窗内与窗外（图例、详图副本）的数量。

用法:
  python 05_viewport_windows.py 图.dxf                       # 只列出各视口窗口
  python 05_viewport_windows.py 图.dxf --layers EM-强电        # 再统计该图层的块，分窗内、窗外
  python 05_viewport_windows.py a.dxf b.dxf c.dxf --layers RC-LIGHT
        # 多个文件（如各栋）合并窗口，看设备落在哪个文件的窗内
  python 05_viewport_windows.py 图.dxf --out win.txt          # 同时保存报告

注意：视口参数取自 DXF 的 VIEWPORT 实体，窗口坐标是模型空间坐标。
视口 1 是整张图纸的概览视口，不计入窗口。
"""
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import block_refs, emit, load, setup_stdout, xy  # noqa: E402


def windows(df):
    """返回 [(x0, x1, y0, y1), ...]，即模型空间中的视口窗口。"""
    wins = []
    vp = df[df["Description"] == "<AcDbViewport>"]
    for _, r in vp.iterrows():
        if int(r["Number"]) == 1:
            continue
        center = xy(r["ViewCenter"])
        vh, pw, ph = float(r["ViewHeight"]), float(r["Width"]), float(r["Height"])
        if center and vh > 0 and pw > 0 and ph > 0:
            mw = vh * pw / ph  # 模型空间宽度 = 高度 × 视口宽高比
            wins.append((center[0] - mw / 2, center[0] + mw / 2,
                         center[1] - vh / 2, center[1] + vh / 2))
    return wins


def in_windows(p, wins):
    return bool(p) and any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for x0, x1, y0, y1 in wins)


def main():
    setup_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dxf", nargs="+", help="一个或多个 DXF 文件")
    ap.add_argument("--layers", help="逗号分隔的图层名；统计第一个文件中这些图层的块")
    ap.add_argument("--out", help="同时把报告保存到此文件")
    a = ap.parse_args()

    out = []
    all_wins = []
    for path in a.dxf:
        wins = windows(load(path))
        out.append("%s : %d 个窗口" % (os.path.basename(path), len(wins)))
        out.extend("   X[%.0f, %.0f]  Y[%.0f, %.0f]" % w for w in wins)
        all_wins.extend(wins)

    if a.layers:
        br = block_refs(load(a.dxf[0]))
        br = br[br["_layer"].isin(set(a.layers.split(",")))]
        per = collections.Counter(
            "窗内" if in_windows(xy(p), all_wins) else "窗外" for p in br["Position"])
        out.append("\n按窗口统计（图层 %s）: 窗内=%d  窗外（图例/详图）=%d  总计=%d" %
                   (a.layers, per["窗内"], per["窗外"], sum(per.values())))
    emit("\n".join(out), a.out)


if __name__ == "__main__":
    main()
