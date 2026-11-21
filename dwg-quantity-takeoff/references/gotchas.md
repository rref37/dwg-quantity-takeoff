# 踩过的坑(按出现频率)

## 出 Excel
- **openpyxl 写 xlsx 崩** `TypeError: Fill() takes no arguments`,连默认空 workbook 都崩。→ 一律用 `pd.ExcelWriter(engine="xlsxwriter")`。注:openpyxl **读** 没问题,只是写崩;删某页可以 `load_workbook` + `del wb[sheet]` + `save`(这条路有时能 save 成功,不行就 xlsxwriter 重建)。

## 编码
- **PowerShell 5.1 读含中文的 `.ps1` 会乱码**(按 GBK 读 UTF-8 文件),路径里的中文变成 `瀹″浘` 一类,导致"找不到路径"。→ 凡涉及中文路径/内容的脚本,**用 Python 跑**(Python3 源码默认 UTF-8)。
- **控制台中文乱码**:统计结果**写 UTF-8 文件再 Read**,别只靠 stdout。脚本里 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")` 可缓解。

## 渲染
- **matplotlib 不显示中文**(豆腐块 + glyph warning)→ `plt.rcParams["font.sans-serif"]=["Microsoft YaHei","SimSun"]; plt.rcParams["axes.unicode_minus"]=False`。
- **DwgExporter `--sheets-to-pdf` 导出的整页 PDF 太小**,图例文字糊成一团读不出。→ 别指望 PDF,自己按 bbox 用 04_render.py 重绘那一块。

## 后台命令输出被吞
- PowerShell 里 `& python x.py 2>&1` 在后台任务里 stdout 经常captured不到。→ 重定向到文件 `python x.py *> log.txt` 再 Read;或干脆让脚本自己写结果文件。判断成功看**输出文件时间戳是否刷新**最可靠。

## 依赖
- 主流程依赖见仓库根目录 `requirements.txt`：ezdxf、pandas、xlsxwriter、matplotlib。脚本用 `ExcelWriter(engine="xlsxwriter")` 写表，不 import openpyxl。只有你自己用 pandas 读 xlsx 时才需要另装读取引擎。许可和来源见 [THIRD_PARTY.md](../../THIRD_PARTY.md)。
