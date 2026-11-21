# -*- coding: utf-8 -*-
"""出材料清单 Excel（xlsxwriter）。每项带“精确度”和“取证依据”两列。

用法:
  python 07_build_xlsx.py 输出.xlsx                          # 生成带示例行的模板
  python 07_build_xlsx.py 输出.xlsx --csv 清单.csv            # 用你的统计结果出表
  python 07_build_xlsx.py 输出.xlsx --csv 清单.csv --title "某项目电气材料清单"

CSV 列顺序（必须一致）: 序号,设备名称,规格,数量,精确度,取证依据
文件编码用 UTF-8（带 BOM 或不带都可以）。
"""
import argparse
import sys

import pandas as pd

COLUMNS = ["序号", "设备名称", "规格", "数量", "精确度", "取证依据"]
WIDTHS = [6, 22, 22, 10, 14, 46]
SHEET = "材料清单"
EXAMPLE = pd.DataFrame([
    ["1", "示例设备 A", "规格 1", "0", "精确", "替换为你的取证结果"],
    ["—", "【合计】", "", "0", "汇总", "写明统计口径，例如：已去重，不含线缆长度"],
], columns=COLUMNS)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="输出的 .xlsx 路径")
    ap.add_argument("--csv", help="清单 CSV 文件；不给则输出示例模板")
    ap.add_argument("--title", default="工程量材料清单", help="表头标题")
    a = ap.parse_args()

    if a.csv:
        df = pd.read_csv(a.csv, dtype=str, encoding="utf-8-sig").fillna("")
        if list(df.columns) != COLUMNS:
            sys.exit("CSV 列必须依次为: " + ",".join(COLUMNS))
    else:
        df = EXAMPLE

    with pd.ExcelWriter(a.out, engine="xlsxwriter") as xw:
        wb = xw.book
        title_fmt = wb.add_format({"bold": True, "font_size": 12, "font_color": "#1F4E78",
                                   "font_name": "Microsoft YaHei"})
        head_fmt = wb.add_format({"bold": True, "bg_color": "#1F4E78", "font_color": "white",
                                  "border": 1, "align": "center", "valign": "vcenter",
                                  "text_wrap": True, "font_name": "Microsoft YaHei"})
        cell_fmt = wb.add_format({"border": 1, "valign": "vcenter", "text_wrap": True,
                                  "font_name": "Microsoft YaHei", "font_size": 10})
        df.to_excel(xw, sheet_name=SHEET, startrow=2, header=False, index=False)
        ws = xw.sheets[SHEET]
        ws.merge_range(0, 0, 0, len(COLUMNS) - 1, a.title, title_fmt)
        for j, col in enumerate(COLUMNS):
            ws.write(1, j, col, head_fmt)
            ws.set_column(j, j, WIDTHS[j], cell_fmt)
        ws.freeze_panes(2, 0)
    print("已保存", a.out)


if __name__ == "__main__":
    main()
