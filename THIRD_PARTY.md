# 第三方组件

本文件记录**本仓库脚本实际 import 或 requirements 实际声明**的组件，以及文档里提到、但脚本并未调用的可选程序。核对日期：2026-11-21。requirements 使用版本范围，安装到的具体 wheel 可能更新许可文本；以你环境里该版本自带的 LICENSE 为准。

发布测试当时用 `pip install -r requirements-dev.txt` 装到并打开了这些 wheel 的许可证文件：ezdxf 1.4.5（MIT）、pandas 3.1.1（顶层 BSD-3-Clause，wheel 内还另附组件许可证）、XlsxWriter 3.3.3（BSD-2-Clause）、Matplotlib 3.11.2（Matplotlib License / PSF 分类）、pytest 9.2.0（MIT）、NumPy 2.5.5（元数据 `License-Expression` 为 `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`）。没有安装 OCR 栈，因此没有打开 PaddleOCR / PaddlePaddle 的已安装 wheel。传递依赖没有逐一审计。**不能据此认为全部依赖都是宽松许可。**

本仓库的 MIT 许可不覆盖本表中的任何一项，也不附带它们的安装包。

## 主流程直接依赖

| 组件 | 本仓库中的使用 | 声明 | 2026-11-21 核对到的上游许可 | 官方来源 |
|---|---|---|---|---|
| ezdxf | `scripts/_common.py` 读 DXF；`scripts/08_proxy_to_geom.py` 展开代理对象；`tests/test_pipeline.py` 写合成 DXF | `requirements.txt`：`ezdxf>=1.4,<2` | MIT License。Copyright (c) 2020 Manfred Moitzi | <https://github.com/mozman/ezdxf> （`LICENSE`） |
| pandas | `_common.py`、`04_render.py`、`07_build_xlsx.py`、`08_proxy_to_geom.py` | `requirements.txt`：`pandas>=2.0` | 顶层为 BSD 3-Clause。Copyright (c) 2008-2011 AQR Capital Management, LLC, Lambda Foundry, Inc. and PyData Development Team；Copyright (c) 2011-2026 Open source contributors。已安装的 3.1.1 wheel 还带有其他组件许可证文件（其中包括 Apache-2.0、MIT、PSF、Boost），不能把整个 wheel 看成只有一份 BSD 文本 | <https://github.com/pandas-dev/pandas> （`LICENSE`） |
| XlsxWriter | `07_build_xlsx.py` 与 `08_proxy_to_geom.py` 通过 `pandas.ExcelWriter(..., engine="xlsxwriter")` 写 xlsx。脚本没有 `import xlsxwriter`，但指定了这个引擎 | `requirements.txt`：`xlsxwriter>=3.1` | BSD 2-Clause。Copyright (c) 2013-2026 John McNamara | <https://github.com/jmcnamara/XlsxWriter> （`LICENSE.txt`） |
| Matplotlib | `04_render.py`、`08_proxy_to_geom.py` 渲染 PNG | `requirements.txt`：`matplotlib>=3.8` | Matplotlib License（项目说明为基于 PSF、BSD 兼容，不是 MIT）。Copyright (c) 2012- Matplotlib Development Team。1.3.0 及以后适用该共享版权文本 | <https://matplotlib.org/stable/project/license.html> |

## 仅测试

| 组件 | 本仓库中的使用 | 声明 | 2026-11-21 核对到的上游许可 | 官方来源 |
|---|---|---|---|---|
| pytest | `tests/test_pipeline.py` | `requirements-dev.txt`：`pytest>=8` | MIT License。Copyright (c) 2004 Holger Krekel and others | <https://github.com/pytest-dev/pytest> （`LICENSE`） |

## 可选，且脚本会 import

| 组件 | 本仓库中的使用 | 声明 | 2026-11-21 核对到的上游许可 | 官方来源 |
|---|---|---|---|---|
| PaddleOCR | `scripts/09_ocr_table.py` 执行 `from paddleocr import PaddleOCR`。主流程和现有测试都不调用它 | `requirements-ocr.txt`：`paddleocr>=3.7,<4` | Apache License 2.0。附录中的版权行为 Copyright (c) 2016 PaddlePaddle Authors | <https://github.com/PaddlePaddle/PaddleOCR> （`LICENSE`） |
| PaddlePaddle | `09_ocr_table.py` 没有直接 `import paddle`。PaddleOCR 运行时需要它；requirements 把 CPU 包钉在 3.3.1，是为了避开文档里记录的 oneDNN 问题 | `requirements-ocr.txt`：`paddlepaddle==3.3.1` | Apache License 2.0。Copyright (c) 2016 PaddlePaddle Authors | <https://github.com/PaddlePaddle/Paddle> （`LICENSE`） |

发布测试的环境没有安装这两个包，因此没有打开已安装 wheel 里的 LICENSE，只核对了上述仓库默认分支上的 LICENSE 文件。OCR 模型文件另有下载来源和条款，不在本仓库内。

## 传递依赖（脚本未直接 import，未全部列出）

| 组件 | 关系 | 2026-11-21 核对到的上游许可 | 官方来源 |
|---|---|---|---|
| NumPy | 本次安装中，ezdxf 1.4.5、pandas 3.1.1 和 Matplotlib 3.11.2 都会带入它。`references/tooling.md` 还记录：安装 Paddle 时可能把 NumPy 升到 2.x。本仓库 `.py` 文件没有 `import numpy` | 已安装的 2.5.5 wheel：顶层 `LICENSE.txt` 为 BSD 3-Clause，Copyright (c) 2005-2025 NumPy Developers。同一 wheel 的 `License-Expression` 是 `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`，并带有 highway、随机数等组件的单独许可证。上游 git 默认分支的年份可能与这个 wheel 不同 | <https://github.com/numpy/numpy> （`LICENSE.txt`） |

同一次 `pip install` 还会带入 pillow、fonttools、packaging、python-dateutil、contourpy、pyparsing 等包。本次没有逐个打开它们的 LICENSE。PaddleOCR 还可能带入 paddlex、modelscope 或其他下载器；`tooling.md` 里的 ModelScope 做法来自原有安装笔记，本次环境未安装 OCR 栈，**没有核实** `paddleocr` 3.7 是否一定依赖 modelscope，也没有审核 modelscope 的许可文本。使用前查看实际环境中该包自带的 LICENSE。

## 文档提到、但任何脚本都没有 import

| 组件 | 关系 | 许可（不要当成宽松许可） | 官方来源 |
|---|---|---|---|
| PyMuPDF（import 名 `fitz`） | 装修清单若是 PDF 光栅，使用者可以自己用它把页面渲成 PNG，再交给 `09_ocr_table.py`。全仓库 `*.py` 均无 `import fitz` / `pymupdf`。`requirements*.txt` 未声明它 | 官方文档写明：PyMuPDF 与 MuPDF **同时**提供开源 AGPL 和商业许可。不能满足 AGPL 时，需向 Artifex 取得商业许可。Artifex 是 MuPDF 的商业许可代理。本仓库的 MIT **不会**把 PyMuPDF 变成 MIT/BSD | <https://pymupdf.readthedocs.io/en/latest/about.html> （License and Copyright）。AGPL-3.0 文本：<https://www.gnu.org/licenses/agpl-3.0.html> |
| openpyxl | 当前脚本不 import，requirements 未声明。旧笔记里“用 pandas 读 xlsx”才需要读取引擎。写表已固定为 xlsxwriter | 本次不把它算作本项目依赖，没有审核其许可 | 不随本仓库分发 |

## 不在本仓库中的外部程序

这些程序不是 Python 依赖，仓库里没有它们的二进制，MIT 不提供其许可。使用者自行取得并遵守各自条款。

| 程序 | 与本仓库的关系 | 许可要点（2026-11-21） | 官方来源 |
|---|---|---|---|
| ODA File Converter | `00_dwg_to_dxf.py` 用子进程调用使用者本机上的程序。`08_proxy_to_geom.py` 在输入为 DWG 时经由 ezdxf 的 odafc 插件调用它 | 可从官网下载。FAQ：非 ODA 会员仅限非商业应用。Community User Agreement（2025-09-05）：有限、不可转让、不可再许可；不得作为商业应用的一部分分发。商业用途需适当的 ODA 授权。详见 [README.md](README.md) | 下载：<https://www.opendesign.com/guestfiles/oda_file_converter> ；FAQ：<https://www.opendesign.com/faq/question/what-are-oda-viewer-and-oda-file-converter> ；协议：<https://www.opendesign.com/agreements/2025/en/ODA%20Community%20User%20Agreement%2009-2025.pdf> |
| Autodesk AutoCAD | 仅 `references/com-fallback.md` 和 `legacy/` 描述 COM 退路 | 商业软件，须自行持有授权 | 以 Autodesk 现行许可为准 |
| 天正、鸿业 | 图纸里的代理对象可能来自这些插件。脚本不能代替它们把未缓存几何炸开 | 商业软件，须自行持有授权。本仓库不提供破解、绕过或序列号 | 以各自厂商现行许可为准 |
| DDC DwgExporter | `legacy/01_dwg_to_excel.py` 调用使用者传入的 `--exe` | 第三方商业工具，不在主流程中，本仓库不附带 | 以该软件发行方的许可为准 |

中文渲染默认尝试 Microsoft YaHei、SimHei、SimSun，这些字体不在仓库里，也不由本 MIT 许可授权。没有这些字体时，Matplotlib 会退到 DejaVu Sans，中文可能显示为方块。
