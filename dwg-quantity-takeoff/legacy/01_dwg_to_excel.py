# -*- coding: utf-8 -*-
"""旧路线：调用本机已安装的 DDC DwgExporter，把 DWG 批量转成 Excel。中文路径安全(Python 读 UTF-8)。

本仓库不附带 DwgExporter。它是第三方软件，需自行取得授权；本项目 MIT 不覆盖它。
下面路径只是占位，不是某台电脑上的真实路径。

用法:
  python 01_dwg_to_excel.py --exe "D:\\path\\to\\DwgExporter.exe" --out D:\\out 图1.dwg 图2.dwg
  python 01_dwg_to_excel.py --exe "D:\\path\\to\\DwgExporter.exe" --out D:\\out --dir "D:\\drawings"
"""
import argparse, os, glob, shutil, subprocess, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True, help="DwgExporter.exe 路径")
    ap.add_argument("--out", required=True, help="输出目录")
    ap.add_argument("--dir", help="若给定,转该目录下所有 *.dwg")
    ap.add_argument("--pdf", action="store_true", help="同时导布局PDF(--sheets-to-pdf)")
    ap.add_argument("files", nargs="*", help="单独指定的 dwg 文件")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    files = list(a.files)
    if a.dir:
        files += glob.glob(os.path.join(a.dir, "**", "*.dwg"), recursive=True)
    if not files:
        print("没有找到 dwg。用 files 参数或 --dir。"); sys.exit(1)
    for i, src in enumerate(files):
        if not os.path.exists(src):
            print("缺失:", src); continue
        # 复制成 ASCII 名避免某些环境的中文 stdout 问题(Exporter本身支持中文路径,这步只为日志清爽)
        tag = "dwg%02d" % i
        dst = os.path.join(a.out, tag + ".dwg")
        shutil.copyfile(src, dst)
        args = [a.exe]
        if a.pdf: args += ["--sheets-to-pdf"]
        args += [dst]
        try:
            subprocess.run(args, cwd=a.out, timeout=600,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            print("超时:", os.path.basename(src)); continue
        outx = os.path.join(a.out, tag + "_dwg.xlsx")
        ok = os.path.exists(outx)
        print("OK" if ok else "FAIL", tag, "<-", os.path.basename(src),
              ("(%d KB)" % round(os.path.getsize(outx)/1024) if ok else ""), flush=True)
    # 记录映射,方便回查
    with open(os.path.join(a.out, "_filemap.txt"), "w", encoding="utf-8") as f:
        for i, src in enumerate(files):
            f.write("dwg%02d\t%s\n" % (i, src))
    print("完成。映射见 _filemap.txt")

if __name__ == "__main__":
    main()
