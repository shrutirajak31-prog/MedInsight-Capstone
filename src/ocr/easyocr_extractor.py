"""
Extract word-level text and bounding boxes from images using EasyOCR.
EasyOCR returns line-level boxes, so we split them into word boxes.
"""

import easyocr
from PIL import Image
from src.ocr.split_words import split_line_to_words

_reader = None


def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)  # set True if CUDA available
    return _reader


def extract_image(path, split_to_words=True):
    reader = get_reader()
    results = reader.readtext(path, detail=1, paragraph=False)

    words = []
    for bbox_pts, text, conf in results:
        xs = [p[0] for p in bbox_pts]
        ys = [p[1] for p in bbox_pts]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        if split_to_words:
            words.extend(split_line_to_words(text, bbox, float(conf)))
        else:
            words.append({"text": text, "bbox": bbox, "confidence": float(conf)})

    img = Image.open(path)
    w, h = img.size
    return [{
        "page": 0,
        "page_w": w,
        "page_h": h,
        "words": words,
        "source": "ocr",
    }]


if __name__ == "__main__":
    import json
    pages = extract_image("data/scanned/clean/report_000_0.png")
    print(f"Words: {len(pages[0]['words'])}")
    print(json.dumps(pages[0]["words"][:15], indent=2, default=float))