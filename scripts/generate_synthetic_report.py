"""
Generate 100 synthetic lab reports as PDFs across 5 panels.
Run after Phase 1 Step 1 (pip install) is complete.
"""

import os
import random
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

random.seed(42)

TESTS = {
    "Total Cholesterol": {"unit": "mg/dL",   "ref": (0, 200),    "range_type": "upper", "panel": "lipid"},
    "Triglycerides":     {"unit": "mg/dL",   "ref": (0, 150),    "range_type": "upper", "panel": "lipid"},
    "HDL Cholesterol":   {"unit": "mg/dL",   "ref": (40, 999),   "range_type": "lower", "panel": "lipid"},
    "LDL Cholesterol":   {"unit": "mg/dL",   "ref": (0, 100),    "range_type": "upper", "panel": "lipid"},
    "VLDL Cholesterol":  {"unit": "mg/dL",   "ref": (5, 40),     "range_type": "range", "panel": "lipid"},
    "TSH":               {"unit": "mIU/L",   "ref": (0.4, 4.0),  "range_type": "range", "panel": "thyroid"},
    "T3":                {"unit": "ng/dL",   "ref": (80, 200),   "range_type": "range", "panel": "thyroid"},
    "T4":                {"unit": "ug/dL",   "ref": (5.0, 12.0), "range_type": "range", "panel": "thyroid"},
    "Hemoglobin":        {"unit": "g/dL",    "ref": (13.0, 17.0),"range_type": "range", "panel": "cbc"},
    "WBC":               {"unit": "10^3/uL", "ref": (4.0, 11.0), "range_type": "range", "panel": "cbc"},
    "RBC":               {"unit": "10^6/uL", "ref": (4.5, 5.9),  "range_type": "range", "panel": "cbc"},
    "Platelets":         {"unit": "10^3/uL", "ref": (150, 450),  "range_type": "range", "panel": "cbc"},
    "Hematocrit":        {"unit": "%",       "ref": (40, 52),    "range_type": "range", "panel": "cbc"},
    "ALT":               {"unit": "U/L",     "ref": (7, 56),     "range_type": "range", "panel": "lft"},
    "AST":               {"unit": "U/L",     "ref": (10, 40),    "range_type": "range", "panel": "lft"},
    "Bilirubin Total":   {"unit": "mg/dL",   "ref": (0.1, 1.2),  "range_type": "range", "panel": "lft"},
    "Albumin":           {"unit": "g/dL",    "ref": (3.5, 5.0),  "range_type": "range", "panel": "lft"},
    "Creatinine":        {"unit": "mg/dL",   "ref": (0.6, 1.3),  "range_type": "range", "panel": "kft"},
    "Urea":              {"unit": "mg/dL",   "ref": (7, 20),     "range_type": "range", "panel": "kft"},
    "Uric Acid":         {"unit": "mg/dL",   "ref": (3.4, 7.0),  "range_type": "range", "panel": "kft"},
}

PANELS = {
    "lipid":   ["Total Cholesterol", "Triglycerides", "HDL Cholesterol", "LDL Cholesterol", "VLDL Cholesterol"],
    "thyroid": ["TSH", "T3", "T4"],
    "cbc":     ["Hemoglobin", "WBC", "RBC", "Platelets", "Hematocrit"],
    "lft":     ["ALT", "AST", "Bilirubin Total", "Albumin"],
    "kft":     ["Creatinine", "Urea", "Uric Acid"],
}


def sample_value(info, abnormal_p=0.4):
    lo, hi = info["ref"]
    rt = info["range_type"]
    abnormal = random.random() < abnormal_p
    if rt == "upper":
        return round(random.uniform(hi * 1.05, hi * 1.6), 1) if abnormal \
               else round(random.uniform(hi * 0.3, hi * 0.95), 1)
    if rt == "lower":
        return round(random.uniform(lo * 0.5, lo * 0.95), 1) if abnormal \
               else round(random.uniform(lo * 1.1, lo * 1.8), 1)
    if abnormal:
        return round(random.uniform(hi * 1.1, hi * 1.5), 1) if random.random() < 0.5 \
               else round(random.uniform(lo * 0.5, lo * 0.9), 1)
    return round(random.uniform(lo, hi), 1)


def format_ref(info):
    lo, hi = info["ref"]
    if info["range_type"] == "upper":
        return f"<{hi}"
    if info["range_type"] == "lower":
        return f">{lo}"
    return f"{lo} - {hi}"


def generate_report(path, tests):
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    y = h - 60

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "CITY DIAGNOSTIC LABORATORY")
    y -= 16
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "123 Medical Street, Bengaluru 560001 | Ph: 080-XXXX-XXXX")
    y -= 25

    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Patient Name: [REDACTED]")
    c.drawString(320, y, "Age / Sex: 42 / M")
    y -= 14
    c.drawString(50, y, "Report ID: LAB-2024-XXXX")
    c.drawString(320, y, "Date: 2024-XX-XX")
    y -= 30

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Test Name")
    c.drawString(230, y, "Result")
    c.drawString(300, y, "Unit")
    c.drawString(380, y, "Reference Range")
    y -= 6
    c.line(50, y, 550, y)
    y -= 16

    c.setFont("Helvetica", 10)
    for test in tests:
        info = TESTS[test]
        val = sample_value(info)
        c.drawString(50, y, test)
        c.drawString(230, y, str(val))
        c.drawString(300, y, info["unit"])
        c.drawString(380, y, format_ref(info))
        y -= 18

    y -= 20
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, y, "Synthetic report generated for research. Not for clinical use.")

    c.save()


def main():
    out_dir = "data/synthetic"
    os.makedirs(out_dir, exist_ok=True)
    for i in range(100):
        panel_keys = random.sample(list(PANELS.keys()), k=random.choice([1, 1, 2]))
        tests = []
        for p in panel_keys:
            tests.extend(PANELS[p])
        generate_report(f"{out_dir}/report_{i:03d}.pdf", tests)
    print(f"Generated 100 PDFs in {out_dir}")


if __name__ == "__main__":
    main()