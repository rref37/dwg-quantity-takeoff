# -*- coding: utf-8 -*-
"""方法②几何指纹：按块定义的几何组成，归类匿名块（A$C...）并匹配已知命名块。

用法:
  python 03_fingerprint.py 图.dxf                              # 列出各块的指纹和归类
  python 03_fingerprint.py 图.dxf --layers RC-LIGHT,EQUIP-照明   # 只看这些图层的块
  python 03_fingerprint.py 图.dxf --known known.json            # {"块名": "类型"}，把指纹传给同型匿名块
  python 03_fingerprint.py 图.dxf --out fp.txt                  # 同时保存报告

逻辑：几何签名相同 = 同一符号。已知命名块的签名会传给签名相同的匿名块。
没有命名对应的匿名块会单独列出，再用 04_render.py 渲染定名。
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import block_def_signatures, block_refs, emit, load, setup_stdout  # noqa: E402


def main():
    setup_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dxf", help="DXF 文件")
    ap.add_argument("--layers", help="逗号分隔的图层名过滤")
    ap.add_argument("--known", help="JSON 文件：{块名: 类型}")
    ap.add_argument("--out", help="同时把报告保存到此文件")
    a = ap.parse_args()

    df = load(a.dxf)
    sig = block_def_signatures(df)
    br = block_refs(df)
    if a.layers:
        br = br[br["_layer"].isin(set(a.layers.split(",")))]
    cnt = br["_name"].value_counts()

    known = {}
    if a.known:
        with open(a.known, encoding="utf-8") as f:
            known = json.load(f)
    sig2type = {}
    for nm, typ in known.items():
        s = sig.get(nm)
        if s:
            sig2type.setdefault(s, typ)

    out = ["=== 块名 计数 / 指纹 / 归类 ==="]
    result = collections.Counter()
    for nm, c in cnt.items():
        s = sig.get(nm, ("?",))
        if nm in known:
            typ = known[nm]
        elif s in sig2type:
            typ = sig2type[s] + "（指纹匹配）"
        else:
            typ = "未识别（需渲染定名）"
        result[typ] += c
        out.append("  %5d  %-16s %-22s %s" % (c, nm, str(s)[:40], typ))
    out.append("\n=== 归类汇总 ===")
    for typ, c in result.most_common():
        out.append("  %5d  %s" % (c, typ))
    emit("\n".join(out), a.out)


if __name__ == "__main__":
    main()
