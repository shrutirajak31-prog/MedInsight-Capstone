"""
Unified dataset builder with resume support.
- Iterates over synthetic PDFs -> PDF extractor
- Iterates over scan images -> OCR extractor
- Saves one JSON per report to data/processed/
- Writes manifest.csv
- SKIPS files that already exist (safe to Ctrl+C and re-run)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import json
import csv
from src.ocr.pdf_extractor import extract_pdf
from src.ocr.easyocr_extractor import extract_image


def _existing_entry(out_path):
    d = json.load(open(out_path))
    return {
        "id": d["id"],
        "source": d["source"],
        "path": out_path,
        "n_words": sum(len(p["words"]) for p in d["pages"]),
    }


def _process_pdf(path, out_path, rid):
    if os.path.exists(out_path):
        print(f"[skip] {rid} (exists)")
        return _existing_entry(out_path)
    pages = extract_pdf(path)
    out = {"id": rid, "source": "pdf", "original_file": path, "pages": pages}
    json.dump(out, open(out_path, "w"), default=float)
    n = sum(len(p["words"]) for p in pages)
    print(f"[pdf] {rid}: {n} words")
    return {"id": rid, "source": "pdf", "path": out_path, "n_words": n}


def _process_ocr(path, out_path, rid, source_tag):
    if os.path.exists(out_path):
        print(f"[skip] {rid} (exists)")
        return _existing_entry(out_path)
    pages = extract_image(path)
    out = {"id": rid, "source": source_tag, "original_file": path, "pages": pages}
    json.dump(out, open(out_path, "w"), default=float)
    n = sum(len(p["words"]) for p in pages)
    print(f"[{source_tag}] {rid}: {n} words")
    return {"id": rid, "source": source_tag, "path": out_path, "n_words": n}


def build():
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/splits", exist_ok=True)

    manifest = []

    pdf_dir = "data/synthetic"
    for fname in sorted(os.listdir(pdf_dir)):
        if not fname.endswith(".pdf"):
            continue
        rid = fname.replace(".pdf", "")
        path = os.path.join(pdf_dir, fname)
        out_path = f"data/processed/{rid}_pdf.json"
        manifest.append(_process_pdf(path, out_path, rid))

    clean_dir = "data/scanned/clean"
    for fname in sorted(os.listdir(clean_dir)):
        if not fname.endswith(".png"):
            continue
        rid = fname.replace(".png", "") + "_clean_ocr"
        path = os.path.join(clean_dir, fname)
        out_path = f"data/processed/{rid}.json"
        manifest.append(_process_ocr(path, out_path, rid, "ocr_clean"))

    deg_dir = "data/scanned/degraded"
    for fname in sorted(os.listdir(deg_dir)):
        if not fname.endswith(".png"):
            continue
        rid = fname.replace(".png", "") + "_degraded_ocr"
        path = os.path.join(deg_dir, fname)
        out_path = f"data/processed/{rid}.json"
        manifest.append(_process_ocr(path, out_path, rid, "ocr_degraded"))

    with open("data/processed/manifest.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=manifest[0].keys())
        writer.writeheader()
        writer.writerows(manifest)

    print(f"\nTotal processed files: {len(manifest)}")


if __name__ == "__main__":
    build()