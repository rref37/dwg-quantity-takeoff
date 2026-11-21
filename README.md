# DWG 算量工具包（三方取证法）

从 AutoCAD DWG 图纸统计设备、部件数量，生成工程量材料清单。覆盖电气、给排水、建筑、结构、装修。

脚本读取的是 DXF。DWG 要先由使用者自行安装的 ODA File Converter 转换成 DXF，再用 Python（ezdxf）统计、渲染和出表。本仓库不附带 ODA、AutoCAD、天正、鸿业或 DwgExporter。

## 许可边界

本仓库自己的代码和文档使用 [MIT License](LICENSE)，版权人署名为 **Pdzapple**（2026）。MIT 允许使用、修改、分发和商业使用**这些内容**，分发时保留版权声明和许可全文。

MIT **不**授予第三方软件的许可。ODA File Converter、AutoCAD、天正、鸿业、DDC DwgExporter、PyMuPDF，以及 `requirements*.txt` 里各库的传递依赖，各自遵守上游条款。直接依赖里既有 MIT、BSD、Apache-2.0，也有可选的 PyMuPDF（AGPL-3.0 或 Artifex 商业许可）。不能把本项目说成“全部依赖都可自由商用”。明细和官方来源见 [THIRD_PARTY.md](THIRD_PARTY.md)，简要声明见 [NOTICE](NOTICE)。

支持请开本仓库 Issues：<https://github.com/rref37/dwg-quantity-takeoff/issues>

工程量结果只供复核前参考，须对照图纸和清单自行确认。

## 安装与运行

需要 Python 3.11 或更高版本。在仓库根目录执行：

```bash
pip install -r requirements.txt
```

可选 OCR（只在要把清单图片抄成文字行时安装）：

```bash
pip install -r requirements-ocr.txt
```

转换 DWG 之前，先按下一节自行下载并安装 ODA File Converter，然后：

```bash
# 查找顺序：--oda 参数、环境变量 ODA_FILE_CONVERTER、PATH 中的 ODAFileConverter
python dwg-quantity-takeoff/scripts/00_dwg_to_dxf.py 图纸.dwg out
python dwg-quantity-takeoff/scripts/02_count.py out/图纸.dxf
python dwg-quantity-takeoff/scripts/04_render.py out/图纸.dxf legend "图例" -o legend.png

# CSV 列：序号,设备名称,规格,数量,精确度,取证依据
python dwg-quantity-takeoff/scripts/07_build_xlsx.py 材料清单.xlsx --csv items.csv
```

Windows 可将转换器路径写入用户环境变量（把路径换成你自己的安装位置）：

```bat
setx ODA_FILE_CONVERTER "C:\path\to\ODAFileConverter.exe"
```

每个脚本都有 `--help`。逐步说明见 [使用说明.md](使用说明.md)。

## ODA File Converter

使用者自己从 ODA 官网下载，本仓库不提供安装包：

<https://www.opendesign.com/guestfiles/oda_file_converter>

2026-11-21 核对的官方文本：

- FAQ「What are ODA Viewer and ODA File Converter?」：二者是展示 ODA 框架能力的示例程序，可以免费下载，用来了解 ODA SDK。**如果不是 ODA 会员，只能用于非商业应用。** 官网只提供最新版本，更早版本仅会员可取。  
  <https://www.opendesign.com/faq/question/what-are-oda-viewer-and-oda-file-converter>
- 《ODA Community User Agreement》（2025-09-05）：社区用户得到的是有限、非独占、不可转让、不可再许可、可撤销的许可，可用于文档或界面所述的查看、浏览和转换；**不得把该程序或其一部分转售，或作为商业应用的一部分分发**。这项权利也不能转移给雇主或承包方。  
  <https://www.opendesign.com/agreements/2025/en/ODA%20Community%20User%20Agreement%2009-2025.pdf>

因此：非会员按上述条款限于非商业用途；商业用途需要 ODA 会员资格或其他适当的 ODA 授权。下载页上的 “Try for Free / 60 days” 是 ODA 软件试用入口，不能理解成 File Converter 已经允许商业使用。协议会改，以下载当时页面上的现行文本为准。上面两段是核对记录，不是法律意见，也不能代替你自己阅读协议。

真实转换还受本机环境限制：需要转换器二进制、它接受的 DWG 版本，以及原图是否保存了代理对象的显示几何。这些都不在本仓库的合成测试里。

## 测试

```bash
pip install -r requirements-dev.txt
python -m pytest dwg-quantity-takeoff/tests -q
python -m py_compile dwg-quantity-takeoff/scripts/*.py dwg-quantity-takeoff/legacy/*.py dwg-quantity-takeoff/tests/*.py
```

`tests/test_pipeline.py` 在临时目录写一张合成 DXF（块名 `SOCKET`，图层 `EM-强电` / `LEGEND`），不读取真实图纸。它覆盖计数、指纹、视口去重、详图分箱、渲染和 xlsx。`00_dwg_to_dxf.py` 只断言“找不到 ODAFileConverter”这一失败分支。

发布时这次运行**没有**安装 ODA File Converter、AutoCAD、天正、鸿业或 DwgExporter，也没有安装 PaddleOCR。因此没有验证真实 DWG 转换、代理对象炸开、COM 退路和 OCR。测试通过只说明合成样例上的脚本行为。

## 目录

```
├── README.md
├── 使用说明.md
├── LICENSE                    MIT；只覆盖本仓库
├── NOTICE
├── THIRD_PARTY.md             直接依赖与可选组件的许可来源
├── requirements.txt           主流程 Python 依赖
├── requirements-dev.txt       测试依赖
├── requirements-ocr.txt       可选 OCR 依赖
├── .gitignore
└── dwg-quantity-takeoff/
    ├── .gitignore
    ├── SKILL.md               方法与流程
    ├── scripts/               00、02–09 与 _common.py
    ├── references/            各专业要点、依赖与踩坑
    ├── tests/                 合成 DXF 回归测试
    └── legacy/                旧的 DDC DwgExporter 路线，不在主流程中
```

不要把 `.env`、虚拟环境、日志、真实图纸、DXF/xlsx/png 转换结果或安装程序提交进 git。规则写在根目录和 `dwg-quantity-takeoff/` 两级 `.gitignore`。两级规则都避免用 `*.json` / `*.csv` 一刀切，以免挡住映射文件和测试夹具。

## 核心方法：三方取证

算量最容易错的不是“数不出”，是**数错了还以为对**。三个独立角度互相印证：

1. **数据直读**：真块名加图层分组计数。大多数部件直接出数。
2. **几何指纹**：匿名块按几何组成归类，再用已知命名块去匹配。
3. **渲染对比**：认不出就把符号或图例渲染成图看。

另有三道质检：图框窗口去重、同层多副本去重（给排水常见）、详图陷阱（只画典型房间的，真实数 = 详图数 × 房间数）。

详细流程见 [dwg-quantity-takeoff/SKILL.md](dwg-quantity-takeoff/SKILL.md)。

## 边界

- 数图块得到的是数量统计，只是算量的前半段。
- 导线和管线长度：平面常只画符号不画连线，几何量取不到，只能估算，不能当实测。
- 完整算量还需套定额。门窗、结构构件、装修清单优先查明细表，比硬数平面更可靠。
- 天正等代理对象若没有存显示几何，ezdxf 解不出来，需先在已获授权的天正里炸开。
- 各专业的图层习惯和判断顺序见 [dwg-quantity-takeoff/references/disciplines.md](dwg-quantity-takeoff/references/disciplines.md)。文中的名称和规格是通用示例，不是某套真实图纸的实测记录。

## 参考资料

[dwg-quantity-takeoff/references/](dwg-quantity-takeoff/references/tooling.md) 收录依赖安装和踩坑记录。其中 [ddc-excel-columns.md](dwg-quantity-takeoff/references/ddc-excel-columns.md) 与 [com-fallback.md](dwg-quantity-takeoff/references/com-fallback.md) 描述的是旧路线（DDC DwgExporter 或 AutoCAD COM），仅供对照。这两条路线使用的程序都不在本仓库里，也不由 MIT 授权。
