# -*- coding: utf-8 -*-
"""回归测试：用一张合成的小 DXF 跑通主要脚本。运行: python -m pytest tests -q"""
import math
import re
import subprocess
import sys
from pathlib import Path

import ezdxf
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from _common import load  # noqa: E402


def run(script, *args, check=True):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    if check:
        assert p.returncode == 0, p.stderr
    return p


@pytest.fixture
def sample(tmp_path):
    """两个插座在 EM-强电 图层，一个图例符号在 LEGEND 图层（位于视口窗口之外）。"""
    doc = ezdxf.new("R2018")
    blk = doc.blocks.new("SOCKET")
    blk.add_line((0, 0), (100, 0))
    blk.add_circle((0, 0), 50)
    blk.add_arc((0, 0), 30, 0, 90)
    msp = doc.modelspace()
    msp.add_blockref("SOCKET", (1000, 0), dxfattribs={"layer": "EM-强电"})
    msp.add_blockref("SOCKET", (5000, 0), dxfattribs={"layer": "EM-强电"})
    msp.add_blockref("SOCKET", (9000, 0), dxfattribs={"layer": "LEGEND"})
    txt = msp.add_text("普通插座", dxfattribs={"layer": "TXT", "height": 200})
    txt.set_placement((1000, -500))
    lay = doc.layouts.new("A3")
    vp = lay.add_viewport(center=(0, 0), size=(297, 210), view_center_point=(3000, 0), view_height=8000)
    vp.dxf.id = 2
    path = tmp_path / "sample.dxf"
    doc.saveas(path)
    return path


def test_load_flattens_entities(sample):
    df = load(str(sample))
    refs = df[df["Description"] == "<AcDbBlockReference>"]
    assert len(refs) == 3
    assert set(refs["BlockTableRecord"]) == {"SOCKET"}
    defs = df[df["BlockId"] == "SOCKET"]
    assert sorted(defs["Description"]) == ["<AcDbArc>", "<AcDbCircle>", "<AcDbLine>"]
    arc = defs[defs["Description"] == "<AcDbArc>"].iloc[0]
    assert math.isclose(arc["EndAngle"], math.pi / 2)  # 弧度，不是角度
    vp = df[df["Description"] == "<AcDbViewport>"]
    assert len(vp) == 1 and int(vp.iloc[0]["Number"]) == 2


def test_count_by_layer(sample):
    out = run("02_count.py", sample).stdout
    assert "SOCKET" in out
    assert re.search(r"\b2\s+EM-强电", out)


def test_fingerprint(sample):
    out = run("03_fingerprint.py", sample).stdout
    assert "SOCKET" in out
    assert "Arc" in out and "Circle" in out and "Line" in out


def test_viewport_window_separates_legend(sample):
    out = run("05_viewport_windows.py", sample, "--layers", "EM-强电,LEGEND").stdout
    assert "窗内=2" in out
    assert "窗外（图例/详图）=1" in out
    out = run("05_viewport_windows.py", sample, "--layers", "LEGEND").stdout
    assert "窗内=0" in out and "窗外（图例/详图）=1" in out


def test_detail_check_counts_all_instances(sample):
    out = run("06_detail_check.py", sample, "--name", "SOCKET", "--bin", "3600").stdout
    assert "匹配 3 个" in out


def test_render_block_and_region(sample, tmp_path):
    sym = tmp_path / "sym.png"
    run("04_render.py", sample, "block", "SOCKET", "-o", sym)
    assert sym.stat().st_size > 0
    area = tmp_path / "area.png"
    # 负数直接作为位置参数传入
    run("04_render.py", sample, "region", "-10", "20000", "-10", "5000", "-o", area)
    assert area.stat().st_size > 0


def test_build_xlsx_from_csv(tmp_path):
    csv = tmp_path / "items.csv"
    csv.write_text("序号,设备名称,规格,数量,精确度,取证依据\n"
                   "1,插座,250V10A,2,精确,测试\n", encoding="utf-8")
    out = tmp_path / "out.xlsx"
    run("07_build_xlsx.py", out, "--csv", csv)
    assert out.stat().st_size > 0


def test_build_xlsx_rejects_bad_columns(tmp_path):
    csv = tmp_path / "bad.csv"
    csv.write_text("a,b\n1,2\n", encoding="utf-8")
    p = run("07_build_xlsx.py", tmp_path / "x.xlsx", "--csv", csv, check=False)
    assert p.returncode != 0 and "CSV 列必须" in p.stderr


def test_dwg_to_dxf_reports_missing_oda(tmp_path):
    dwg = tmp_path / "a.dwg"
    dwg.write_bytes(b"not really a drawing")
    p = run("00_dwg_to_dxf.py", dwg, tmp_path / "out", "--oda", str(tmp_path / "nope.exe"), check=False)
    assert p.returncode != 0
    assert "找不到 ODAFileConverter" in p.stderr
