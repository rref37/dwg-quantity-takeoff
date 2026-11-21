# -*- coding: utf-8 -*-
"""清单/材料表 PNG -> 结构化行(基础 PaddleOCR + 按坐标聚行)。
给 OLE 嵌入 / 光栅表格用:DwgExporter 和 PDF 文字层都读不出表体时,先把 PDF 渲成 PNG
(PyMuPDF,见 disciplines.md 装修节)再跑本脚本,最后人工/脚本做 合价=量×单价 校验。

用法:  python 09_ocr_table.py <png> [out.txt]
环境:  先 `export/set PADDLE_PDX_MODEL_SOURCE=modelscope`(避开百度源 SSL 崩)
依赖坑见 references/tooling.md(别用 PP-StructureV3 全家桶 / enable_mkldnn=False / WinError5 清 ~* 残目录)。
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from paddleocr import PaddleOCR

def main(img, out=None, row_tol=18):
    out = out or os.path.splitext(img)[0] + "_ocr.txt"
    ocr = PaddleOCR(lang="ch",
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    enable_mkldnn=False)  # paddle 3.3.1 CPU 的 oneDNN+PIR bug,必须关
    boxes = []
    for res in ocr.predict(img):
        d = res.json["res"]
        for poly, txt in zip(d["dt_polys"], d["rec_texts"]):
            cx = sum(p[0] for p in poly) / len(poly)
            cy = sum(p[1] for p in poly) / len(poly)
            boxes.append((cx, cy, txt))
    boxes.sort(key=lambda b: (b[1], b[0]))
    rows, cur, lasty = [], [], None
    for cx, cy, t in boxes:
        if lasty is None or abs(cy - lasty) <= row_tol:
            cur.append((cx, t))
        else:
            cur.sort(); rows.append(cur); cur = [(cx, t)]
        lasty = cy
    if cur: cur.sort(); rows.append(cur)
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# OCR {img}  ({len(boxes)} boxes, {len(rows)} rows)\n\n")
        for r in rows:
            f.write(" | ".join(t for _, t in r) + "\n")
    print("wrote", out, "| boxes", len(boxes), "rows", len(rows))

if __name__ == "__main__":
    main(*sys.argv[1:])
