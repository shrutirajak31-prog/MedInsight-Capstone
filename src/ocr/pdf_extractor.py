"""
Extract word-level text and bounding boxes from digital PDFs using PyMuPDF.
"""

import fitz


def extract_pdf(path):
    """
    Returns list of pages:
    [{"page": int, "page_w": float, "page_h": float,
      "words": [{"text": str, "bbox": (x0,y0,x1,y1), "confidence": 1.0}],
      "source": "pdf"}]
    """
    doc = fitz.open(path)
    pages = []
    for pno, page in enumerate(doc):
        words = []
        for x0, y0, x1, y1, text, block, line, word_no in page.get_text("words"):
            words.append({
                "text": text,
                "bbox": (x0, y0, x1, y1),
                "confidence": 1.0,
            })
        pages.append({
            "page": pno,
            "page_w": page.rect.width,
            "page_h": page.rect.height,
            "words": words,
            "source": "pdf",
        })
    doc.close()
    return pages


if __name__ == "__main__":
    pages = extract_pdf("data/synthetic/report_000.pdf")
    print(f"Pages: {len(pages)}")
    for w in pages[0]["words"][:20]:
        print(w)