# 依赖工具与安装（装了 skill 跑不起来先看这页）

本 skill 只含**方法和脚本**，不含二进制工具。主流程只依赖下面"必备"的几项，OCR 和 PDF 相关的按需安装。

## 必备

| 工具 | 用途 | 安装 / 获取 | 验证 |
|---|---|---|---|
| **Python 3.11+** | 跑所有脚本 | 系统已有即可 | `python --version` |
| **ODA File Converter**（第三方程序，不随仓库提供） | DWG→DXF，`00_dwg_to_dxf.py` 调用使用者本机上的程序。不要求同时安装 AutoCAD | 自行从官网下载 https://www.opendesign.com/guestfiles/oda_file_converter 。找不到时用 `--oda` 指定路径，或设置环境变量 `ODA_FILE_CONVERTER`。非 ODA 会员按官方 FAQ 仅限非商业用途；商业用途需适当的 ODA 授权。本仓库 MIT 不授予该许可，见 [README.md](../../README.md) | 在你有权使用转换器的环境里，`00_dwg_to_dxf.py` 能输出 DXF。合成测试只覆盖“找不到程序”的失败分支 |
| **ezdxf / pandas / xlsxwriter / matplotlib** | 读 DXF、统计、渲染、出清单 | `pip install -r requirements.txt`（在仓库根目录执行）。许可并不都是 MIT，见 [THIRD_PARTY.md](../../THIRD_PARTY.md) | `python -m pytest tests -q`（在 `dwg-quantity-takeoff/` 下执行） |

> ⚠️ openpyxl 写 xlsx 在部分环境会崩（`Fill() takes no arguments`）。出表一律用 `pd.ExcelWriter(engine="xlsxwriter")`，`07_build_xlsx.py` 已经这样做。

## 按需

| 工具 | 用途 | 安装 |
|---|---|---|
| **PyMuPDF (fitz)** | 把 PDF 图纸或清单渲染成高清 PNG，给 OCR 或人工读数用。全仓库脚本都不 import 它，requirements 也未声明 | 自行决定是否安装。官方同时提供 **AGPL-3.0 和商业许可**，不是宽松许可；不能满足 AGPL 时需向 Artifex 取得商业许可。见 [THIRD_PARTY.md](../../THIRD_PARTY.md) |

## OCR（只有要把 OLE/光栅清单自动抄成表才装）

> 背景：装修的"清单与计价表"、材料表常以 **OLE 嵌入对象**存放，DXF 和 PDF 文字层都读不出（只有图框标题栏有字），表体是光栅图。**渲染成 PNG 后用 OCR 抄数**，再用 合价 = 量 × 单价 自洽校验。详见 `disciplines.md` 装修节。

```
pip install -r requirements-ocr.txt
```

**实测 4 个坑（Win10 + Python 3.11 + paddlepaddle 3.3.1 / paddleocr 3.7.0，务必照做）：**

1. **别用 PP-StructureV3 全家桶**。它要额外 `pip install "paddlex[ocr]"`，且加载版面/表格/公式/图表一大堆模型，首跑从百度服务器下载常 SSL 崩。**基础 `PaddleOCR(lang="ch")` 拿带坐标的文字框，再自己按 y 聚行、按 x 排列就够**（见 `scripts/09_ocr_table.py`）。
2. **模型下载走 ModelScope，别走默认百度源**（`paddle-model-ecology.bj.bcebos.com` 从国内或代理常 `SSLEOFError`）：跑前 `set/export PADDLE_PDX_MODEL_SOURCE=modelscope`（`pip install paddleocr` 已带 modelscope 包）。
3. **paddlepaddle 3.3.1 CPU 的 oneDNN+PIR 执行器有 bug**：推理报 `NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]` → **构造时传 `enable_mkldnn=False`**（环境变量 `FLAGS_use_mkldnn=0` 不生效，必须在代码里传）。
4. **pip 装到一半被锁文件中断**会留下 `site-packages\~xxx` 残目录，下次装报 `WinError 5 拒绝访问`。删掉所有 `~*` 残目录再装。
5. 附带：paddle 会把 **numpy 升到 2.x**。若别的脚本崩在 numpy 上，留意版本。

## 天正 / 自动化的限制

- 天正代理对象要管线长度 → 在天正里手动 `文件布图→图形导出→天正3(T3)` 炸开后再统计（见 disciplines.md 给排水节）。
- ⚠️ AutoCAD/天正常以**管理员身份运行**，Windows UIPI 会挡住 computer-use 的键鼠注入，COM 也可能报"需提升权限"。自动化驱动不了时，让用户手动操作，或改用非管理员身份启动。

## 脚本清单（`scripts/`）

`00_dwg_to_dxf` DWG 转 DXF · `02_count` 块/层直方图 · `03_fingerprint` 匿名块指纹 · `04_render` 渲染块/图例/区域 · `05_viewport_windows` 图框去重 · `06_detail_check` 详图陷阱 · `07_build_xlsx` 出表 · `08_proxy_to_geom` 代理几何/管长 · `09_ocr_table` 清单 PNG 转结构化行（PaddleOCR）

`legacy/01_dwg_to_excel.py` 是旧的 DDC DwgExporter 路线，依赖商用工具，不在主流程中。
