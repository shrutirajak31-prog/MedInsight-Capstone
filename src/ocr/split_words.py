"""
Split an OCR line into word boxes using proportional character widths.
Preserves left-to-right ordering for downstream relation extraction.
"""


def split_line_to_words(text, bbox, conf):
    x0, y0, x1, y1 = bbox
    width = x1 - x0
    words = text.split()
    if not words:
        return []
    total_chars = sum(len(w) for w in words) or 1
    out = []
    cursor = x0
    for w in words:
        w_width = width * (len(w) / total_chars)
        out.append({
            "text": w,
            "bbox": (cursor, y0, cursor + w_width, y1),
            "confidence": conf,
        })
        cursor += w_width
    return out