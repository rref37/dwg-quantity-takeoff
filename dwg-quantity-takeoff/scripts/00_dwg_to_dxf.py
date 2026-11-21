# -*- coding: utf-8 -*-
"""DWG → DXF 批量转换。调用使用者本机已安装的 ODA File Converter。这是流程第一步，后续脚本都读 DXF。

用法:
    python 00_dwg_to_dxf.py <图.dwg 或目录> <输出目录> [--recursive] [--oda <ODAFileConverter>]

ODA 程序查找顺序: --oda 参数 > 环境变量 ODA_FILE_CONVERTER > PATH 里的 ODAFileConverter。
请自行从官网下载，本脚本不附带安装包，也不提供其许可。非 ODA 会员按官方条款仅限非商业用途：
https://www.opendesign.com/guestfiles/oda_file_converter
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_oda(explicit):
    for cand in (explicit, os.environ.get("ODA_FILE_CONVERTER"), shutil.which("ODAFileConverter")):
        if cand and Path(cand).is_file():
            return Path(cand)
    sys.exit("找不到 ODAFileConverter。请用 --oda 指定路径，或设置环境变量 ODA_FILE_CONVERTER。\n"
             "请自行下载并遵守 ODA 条款（非会员仅限非商业用途）: "
             "https://www.opendesign.com/guestfiles/oda_file_converter")


def convert(dwgs, outdir, oda):
    """调用 ODA 转换一批 DWG，返回 {文件名: 是否成功}。ODA 只接受目录，所以先复制到临时目录。"""
    outdir.mkdir(parents=True, exist_ok=True)
    result = {}
    with tempfile.TemporaryDirectory(prefix="odain_") as td:
        indir = Path(td)
        for p in dwgs:
            shutil.copy2(p, indir / p.name)
        cmd = [str(oda), str(indir), str(outdir.resolve()), "ACAD2018", "DXF", "0", "1"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            status = "返回码 %d" % proc.returncode
        except subprocess.TimeoutExpired:
            status = "超时"
    # ODA 有时返回非零但仍然成功，所以以输出文件为准
    for p in dwgs:
        dxf = outdir / (p.stem + ".dxf")
        ok = dxf.exists() and dxf.stat().st_size > 0
        result[p.name] = ok
        if ok:
            print("OK    %s -> %s (%.1f MB)" % (p.name, dxf.name, dxf.stat().st_size / 1e6))
        else:
            print("FAIL  %s（ODA %s）" % (p.name, status), file=sys.stderr)
    return result


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="单个 .dwg 文件或包含图纸的目录")
    ap.add_argument("outdir", help="DXF 输出目录")
    ap.add_argument("--recursive", action="store_true", help="递归查找子目录中的 DWG")
    ap.add_argument("--oda", help="ODAFileConverter.exe 路径")
    a = ap.parse_args()

    inp = Path(a.input)
    if inp.is_file():
        files = [inp]
    else:
        files = sorted(inp.rglob("*.dwg") if a.recursive else inp.glob("*.dwg"))
    files = [f for f in files if f.suffix.lower() == ".dwg"]
    if not files:
        sys.exit("没有找到 .dwg 文件")

    names = [f.name.lower() for f in files]
    if len(set(names)) != len(names):
        sys.exit("存在同名的 DWG（来自不同子目录），请分开转换。")

    oda = find_oda(a.oda)
    result = convert(files, Path(a.outdir), oda)
    print("\n完成: %d/%d 个转换成功。下一步: python 02_count.py <dxf>" % (sum(result.values()), len(files)))


if __name__ == "__main__":
    main()
