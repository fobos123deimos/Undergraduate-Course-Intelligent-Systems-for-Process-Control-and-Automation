"""Render the three PDF editions and record mechanical document checks.

Requires pypdf, pypdfium2 and Pillow. Inspect the resulting PNGs visually;
mechanical checks alone do not establish that a diagram is readable.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re

import pypdf
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def validate(output):
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for relative in ("course/notes.pdf", "problem-sets/exercises.pdf", "problem-sets/solutions.pdf"):
        path = ROOT / relative
        raw = path.read_bytes()
        reader = pypdf.PdfReader(path)
        document = pdfium.PdfDocument(path)
        stem = path.stem
        thumbnails = []
        page_records = []
        for index, page in enumerate(document):
            text_page = page.get_textpage()
            text = text_page.get_text_range()
            width, height = page.get_size()
            outside = []
            for char in range(text_page.count_chars()):
                try:
                    left, bottom, right, top = text_page.get_charbox(char)
                except Exception:
                    continue
                if left < -0.5 or bottom < -0.5 or right > width + 0.5 or top > height + 0.5:
                    outside.append(char)
            image = page.render(scale=0.7).to_pil().convert("RGB")
            image_path = output / f"{stem}-{index+1:03d}.png"
            image.save(image_path)
            image.thumbnail((360, 510))
            canvas = Image.new("RGB", (380, 540), "#dddddd")
            canvas.paste(image, ((380-image.width)//2, 24))
            ImageDraw.Draw(canvas).text((12, 5), f"{stem} / page {index+1}", fill="black")
            thumbnails.append(canvas)
            page_records.append({"page": index+1, "characters": len(text), "characters_outside_page": len(outside)})
            text_page.close()
            page.close()
        for offset in range(0, len(thumbnails), 12):
            chunk = thumbnails[offset:offset+12]
            sheet = Image.new("RGB", (380*3, 540*math.ceil(len(chunk)/3)), "white")
            for idx, thumb in enumerate(chunk):
                sheet.paste(thumb, (380*(idx%3), 540*(idx//3)))
            sheet.save(output / f"{stem}-contact-{offset//12+1:02d}.png")
        log_path = path.with_suffix(".log")
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        warnings = [line.strip() for line in log.splitlines() if re.search(r"Overfull|Missing character|^!", line)]
        records.append({
            "path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw), "pages": len(reader.pages), "page_checks": page_records,
            "layout_or_glyph_warnings": warnings,
        })
        document.close()
    result = {"documents": records,
              "visual_review": {"status": "pending", "required_scope": "Inspect all page renders and focused equation/diagram pages."},
              "render_output": "PNG page renders and contact sheets are kept outside the repository by default."}
    report = ROOT / "docs" / "document-validation.json"
    report.parent.mkdir(exist_ok=True)
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{key: value for key, value in row.items() if key != "page_checks"} for row in records], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT.parent / "tmp" / "document-review")
    validate(parser.parse_args().output)
