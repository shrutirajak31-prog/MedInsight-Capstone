"""
Convert synthetic PDFs to rasterized images (paired clean + degraded) for OCR testing.

Every PDF produces TWO images:
- one clean (rasterized but no artifacts)
- one degraded (rotation + blur + noise + contrast reduction)

This allows paired comparison in robustness experiments.
"""

import os
import random
from pdf2image import convert_from_path
from PIL import Image, ImageFilter
import numpy as np

random.seed(42)

POPPLER_PATH = r"C:\poppler-26.09.0\Library\bin"


def degrade_image(img, severity):
    # Rotation: up to 2.5 degrees
    angle = random.uniform(-2.5, 2.5)
    img = img.rotate(angle, fillcolor="white", expand=False)

    # Stronger blur
    if severity == "medium":
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(1.0, 1.6)))
    else:  # heavy
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(1.6, 2.4)))

    # Contrast/brightness reduction + heavier noise
    arr = np.array(img).astype(np.float32)
    arr = arr * random.uniform(0.75, 0.92)  # dimmer
    sigma = 12 if severity == "medium" else 22
    arr = np.clip(arr + np.random.normal(0, sigma, arr.shape), 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def main():
    pdf_dir = "data/synthetic"
    clean_dir = "data/scanned/clean"
    degraded_dir = "data/scanned/degraded"

    # clear old outputs so re-runs are idempotent
    for d in (clean_dir, degraded_dir):
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):
            if f.endswith(".png"):
                os.remove(os.path.join(d, f))

    pdfs = sorted(f for f in os.listdir(pdf_dir) if f.endswith(".pdf"))
    print(f"Processing {len(pdfs)} PDFs (clean + degraded for each)")

    for pdf in pdfs:
        pages = convert_from_path(
            os.path.join(pdf_dir, pdf),
            dpi=200,
            poppler_path=POPPLER_PATH,
        )
        for pno, page in enumerate(pages):
            name = pdf.replace(".pdf", "")
            # every report gets a clean version
            page.save(f"{clean_dir}/{name}_{pno}.png", "PNG")
            # every report also gets a degraded version
            sev = random.choice(["medium", "medium", "heavy"])
            degrade_image(page, sev).save(f"{degraded_dir}/{name}_{pno}.png", "PNG")

    print(f"Clean: {len([f for f in os.listdir(clean_dir) if f.endswith('.png')])} images")
    print(f"Degraded: {len([f for f in os.listdir(degraded_dir) if f.endswith('.png')])} images")


if __name__ == "__main__":
    main()