"""
Streamlit dashboard — Medical Report NER
Run from project root: streamlit run scripts/demo.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import re
import html
import pandas as pd
import streamlit as st
from collections import defaultdict
from seqeval.metrics import f1_score

from src.ner.crf_model import load_crf, predict_record
from src.relation.rules import extract_tuples


# ---------------------------------------------------------------- page setup
st.set_page_config(
    page_title="Medical Report NER",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------- CSS
CSS = """
<style>
/* --- typography & base --- */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.stApp {
    background: linear-gradient(180deg, #f8fafc 0%, #ffffff 500px);
}

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1400px;
}

/* --- hero banner --- */
.hero {
    background: linear-gradient(135deg, #1e40af 0%, #0891b2 100%);
    padding: 2.25rem 2rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(30, 64, 175, 0.18);
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%; right: -10%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.hero h1 {
    font-size: 1.9rem;
    font-weight: 700;
    margin: 0 0 0.5rem 0;
    color: white !important;
    position: relative;
    z-index: 1;
}
.hero p {
    font-size: 0.98rem;
    opacity: 0.92;
    margin: 0;
    position: relative;
    z-index: 1;
    max-width: 800px;
    line-height: 1.5;
}

/* --- section headers --- */
.section {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #64748b;
    margin: 1.75rem 0 0.75rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1.5px solid #e2e8f0;
}

/* --- metric cards --- */
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    transition: all 0.2s ease;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
    transform: translateY(-2px);
    border-color: #cbd5e1;
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    color: #64748b !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="stMetricValue"] {
    font-size: 1.9rem !important;
    font-weight: 700 !important;
    color: #1e40af !important;
}

/* --- tabs --- */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: #f1f5f9;
    padding: 6px;
    border-radius: 12px;
    border-bottom: none;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
    font-size: 0.88rem;
    color: #475569;
    border: none !important;
    transition: all 0.15s;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(255,255,255,0.5);
    color: #1e40af;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #1e40af !important;
    box-shadow: 0 2px 6px rgba(15,23,42,0.08);
}

/* --- dataframes --- */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
}

/* --- alerts --- */
.stAlert {
    border-radius: 10px;
}

/* --- sidebar --- */
[data-testid="stSidebar"] {
    background: #f8fafc;
    border-right: 1px solid #e2e8f0;
}
[data-testid="stSidebar"] h2 {
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748b !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.75rem !important;
    font-weight: 700;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] li {
    color: #334155 !important;
    font-size: 0.87rem;
    line-height: 1.6;
}

/* --- entity pills --- */
.entity-text {
    line-height: 2.2;
    font-size: 13px;
    padding: 0.5rem 0;
}
.ent {
    padding: 3px 8px;
    border-radius: 6px;
    margin: 1px;
    font-weight: 500;
    transition: transform 0.12s ease, filter 0.12s ease;
    cursor: default;
    display: inline-block;
    white-space: nowrap;
}
.ent:hover {
    transform: translateY(-1px);
    filter: brightness(0.94);
    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
}
.ent-test  { background: #fef3c7; color: #78350f; border: 1px solid #fde68a; }
.ent-value { background: #d1fae5; color: #064e3b; border: 1px solid #a7f3d0; }
.ent-unit  { background: #dbeafe; color: #1e3a8a; border: 1px solid #bfdbfe; }
.ent-range { background: #ffe4e6; color: #881337; border: 1px solid #fecdd3; }
.plain     { color: #94a3b8; font-size: 13px; margin: 1px; }

/* --- legend pills --- */
.legend-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    margin: 3px 4px 3px 0;
    font-size: 12px;
    font-weight: 600;
}

/* --- metric card container tweak --- */
.metric-row [data-testid="stMetric"] {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
}

/* --- hide Streamlit footer --- */
footer { visibility: hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- data
LABEL_TO_CLASS = {
    "TEST":      "ent-test",
    "VALUE":     "ent-value",
    "UNIT":      "ent-unit",
    "REF_RANGE": "ent-range",
}

LABEL_COLORS = {
    "TEST":      "#fef3c7",
    "VALUE":     "#d1fae5",
    "UNIT":      "#dbeafe",
    "REF_RANGE": "#ffe4e6",
}


@st.cache_resource
def get_crf():
    path = "checkpoints/crf_full.pkl"
    if not Path(path).exists():
        st.error(f"Model not found at `{path}`. Run `python scripts/train_crf.py` first.")
        st.stop()
    return load_crf(path)


@st.cache_data
def load_test_reports():
    return [json.loads(line) for line in open("data/splits/test.jsonl")]


def base_report_id(rid):
    for suffix in ("_pdf", "_clean_ocr", "_degraded_ocr"):
        if rid.endswith(suffix):
            rid = rid[:-len(suffix)]
            break
    m = re.match(r"^(report_\d+)", rid)
    return m.group(1) if m else rid


def entity_f1(gold, pred):
    try:
        return f1_score([gold], [pred], average="micro", zero_division=0)
    except Exception:
        return 0.0


def render_ner(words, labels):
    """Render NER-highlighted text as HTML."""
    parts = []
    i = 0
    while i < len(words):
        if labels[i].startswith("B-"):
            label = labels[i][2:]
            j = i + 1
            while j < len(labels) and labels[j] == f"I-{label}":
                j += 1
            text = " ".join(html.escape(w) for w in words[i:j])
            cls = LABEL_TO_CLASS.get(label, "plain")
            parts.append(
                f'<span class="ent {cls}" title="{label}">{text}</span>'
            )
            i = j
        else:
            parts.append(f'<span class="plain">{html.escape(words[i])}</span>')
            i += 1
    return '<div class="entity-text">' + " ".join(parts) + "</div>"


def tuples_dataframe(tuples):
    rows = [{
        "Test":  t["test"],
        "Value": t["value"] or "—",
        "Unit":  t["unit"]  or "—",
        "Range": t["range"] or "—",
    } for t in tuples]
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ---------------------------------------------------------------- header
st.markdown("""
<div class="hero">
  <h1>🩺 Medical Report NER — Interactive Demo</h1>
  <p>CRF-based Named Entity Recognition and Relation Extraction from lab reports.
     Evaluated across digital PDFs, clean OCR, and degraded OCR to show how
     NER degrades under realistic scan noise — and why context features
     recover the signal.</p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("## Legend")
    for label, color in LABEL_COLORS.items():
        st.markdown(
            f'<span class="legend-pill" '
            f'style="background:{color};color:#0f172a;">{label}</span>',
            unsafe_allow_html=True,
        )

    st.markdown("## Model")
    st.markdown(
        "**CRF** with four feature groups:\n"
        "- Word identity\n"
        "- Position (x, y bucket)\n"
        "- Character n-grams\n"
        "- **Context** (prev/next word, neighbour flags)"
    )

    st.markdown("## Data")
    st.markdown(
        "- **100** synthetic lab reports\n"
        "- **5** panels: lipid, thyroid, CBC, LFT, KFT\n"
        "- Paired **clean + degraded** scans\n"
        "- **63.9%** token preservation on degraded"
    )

    st.markdown("## Splits")
    st.markdown(
        "- Train: **70** reports\n"
        "- Dev: **15** reports\n"
        "- Test: **15** reports\n"
        "- Zero report-level leakage"
    )


# ---------------------------------------------------------------- load
crf = get_crf()
reports = load_test_reports()

by_base = defaultdict(dict)
for r in reports:
    by_base[base_report_id(r["id"])][r["source"]] = r


# ---------------------------------------------------------------- tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🔬  Try a Report",
    "📊  NER Comparison",
    "🔗  Relation Extraction",
    "🧪  Feature Ablation",
])


# =========================================================== TAB 1
with tab1:
    st.markdown('<div class="section">SELECT A REPORT</div>', unsafe_allow_html=True)

    base_ids = sorted(by_base.keys())
    selected = st.selectbox(
        "Report to inspect",
        base_ids,
        index=0,
        label_visibility="collapsed",
    )

    sources = [
        ("pdf",          "📄  Digital PDF (clean)"),
        ("ocr_clean",    "📷  Clean OCR"),
        ("ocr_degraded", "🌫️  Degraded OCR"),
    ]

    cols = st.columns(3, gap="medium")
    for col, (src, label) in zip(cols, sources):
        with col:
            st.markdown(f'<div class="section">{label}</div>', unsafe_allow_html=True)
            rec = by_base[selected].get(src)
            if rec is None:
                st.info("No data for this source.")
                continue

            pred = predict_record(crf, rec)
            f1 = entity_f1(rec["labels"], pred)

            st.metric("Entity F1", f"{f1:.3f}")

            st.markdown(render_ner(rec["words"], pred), unsafe_allow_html=True)

            st.markdown(
                '<div class="section">EXTRACTED TUPLES</div>',
                unsafe_allow_html=True,
            )
            tuples = extract_tuples(rec["words"], pred, rec["bboxes"])
            if tuples:
                st.dataframe(
                    tuples_dataframe(tuples),
                    use_container_width=True,
                    hide_index=True,
                    height=min(280, 40 + 35 * len(tuples)),
                )
            else:
                st.warning("No tuples extracted.")

    st.info(
        "**Try this** — pick a report above, then compare the three columns. "
        "The **degraded OCR** column shows visible character errors "
        "(`Choleaterd`, `Makcai`, `mgdL`), but the CRF still recovers most "
        "entities because **context features** encode where each token sits."
    )


# =========================================================== TAB 2
with tab2:
    st.markdown('<div class="section">ENTITY-LEVEL MICRO-F1 ON TEST SET</div>',
                unsafe_allow_html=True)

    df_ner = pd.DataFrame([
        {"Method": "Regex",      "PDF": 1.000, "Clean OCR": 0.975, "Degraded OCR": 0.853},
        {"Method": "CRF",        "PDF": 1.000, "Clean OCR": 1.000, "Degraded OCR": 0.919},
        {"Method": "DistilBERT", "PDF": 0.876, "Clean OCR": 0.886, "Degraded OCR": 0.714},
    ]).set_index("Method")

    styled = df_ner.style.highlight_max(
        axis=0, props="background-color: #dcfce7; font-weight: 600; color: #14532d;"
    ).format("{:.3f}")

    st.dataframe(styled, use_container_width=True, height=180)

    st.markdown('<div class="section">INTERPRETATION</div>', unsafe_allow_html=True)
    st.markdown("""
    - **All methods are effectively ceiling on clean PDFs** — the task is genuinely solvable.
    - **The interesting comparison is degraded OCR**, where methods diverge:
      Regex **0.853**, CRF **0.919**, DistilBERT **0.714**.
    - **CRF beats regex by 6.6 points** and **DistilBERT by 20.5 points** on noisy input.
    - DistilBERT underperforms despite being a transformer — a **data-scale limitation**
      (210 training files is well below the thousands typically required for fine-tuning).
    """)


# =========================================================== TAB 3
with tab3:
    st.markdown('<div class="section">TUPLE EXACT-MATCH F1</div>',
                unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown("**Oracle** — gold labels → tuples (validates grouping logic):")
        df_oracle = pd.DataFrame([
            {"Source": "PDF",          "P": 1.000, "R": 1.000, "F1": 1.000},
            {"Source": "Clean OCR",    "P": 1.000, "R": 1.000, "F1": 1.000},
            {"Source": "Degraded OCR", "P": 1.000, "R": 1.000, "F1": 1.000},
        ]).set_index("Source").style.format("{:.3f}").highlight_max(
            axis=0, props="background-color: #dcfce7; color: #14532d;"
        )
        st.dataframe(df_oracle, use_container_width=True, height=170)

    with c2:
        st.markdown("**End-to-end** — CRF predictions → tuples (full pipeline):")
        df_e2e = pd.DataFrame([
            {"Source": "PDF",          "P": 1.000, "R": 1.000, "F1": 1.000},
            {"Source": "Clean OCR",    "P": 1.000, "R": 1.000, "F1": 1.000},
            {"Source": "Degraded OCR", "P": 0.906, "R": 0.873, "F1": 0.889},
            {"Source": "Overall",      "P": 0.973, "R": 0.962, "F1": 0.967},
        ]).set_index("Source").style.format("{:.3f}")
        st.dataframe(df_e2e, use_container_width=True, height=170)

    st.markdown('<div class="section">INTERPRETATION</div>', unsafe_allow_html=True)
    st.markdown("""
    - **Oracle F1 = 1.000** on all sources — the relation extractor is correct
      when given perfect labels. Row-grouping logic validated.
    - **End-to-end tuple F1 on degraded = 0.889**, only **3 points below**
      entity F1 (0.919). Error propagation is mild because the CRF is
      *precision-first* — when it misses an entity, it misses the whole tuple
      rather than producing a partially-wrong one.
    - **88.9% of tuples on degraded input are exactly correct** — sufficient
      for downstream abnormality detection.
    """)


# =========================================================== TAB 4
with tab4:
    st.markdown('<div class="section">CRF FEATURE ABLATION — WHICH GROUP DOES THE WORK?</div>',
                unsafe_allow_html=True)

    abl_df = pd.DataFrame([
        {"Variant": "Full CRF",        "PDF": 1.000, "Clean OCR": 1.000,
         "Degraded OCR": 0.919, "Δ vs Full": "—"},
        {"Variant": "No char n-grams", "PDF": 1.000, "Clean OCR": 1.000,
         "Degraded OCR": 0.918, "Δ vs Full": "-0.002"},
        {"Variant": "No position",     "PDF": 1.000, "Clean OCR": 1.000,
         "Degraded OCR": 0.916, "Δ vs Full": "-0.004"},
        {"Variant": "No context",      "PDF": 1.000, "Clean OCR": 1.000,
         "Degraded OCR": 0.866, "Δ vs Full": "-0.053"},
    ]).set_index("Variant")

    def highlight_context_row(row):
        if "No context" in row.name:
            return ["background-color: #fee2e2; color: #7f1d1d; font-weight: 600;"] * len(row)
        return [""] * len(row)

    styled = (abl_df.style
              .apply(highlight_context_row, axis=1)
              .format({"PDF": "{:.3f}", "Clean OCR": "{:.3f}", "Degraded OCR": "{:.3f}"}))

    st.dataframe(styled, use_container_width=True, height=220)

    st.success("""
**Key finding.** The CRF's entire advantage over regex on degraded OCR
comes from **context features** — the previous/next word and neighbour
flags. Removing them drops degraded F1 from **0.919 → 0.866**, back to
regex's level (0.853). Removing character n-grams or position features
changes nothing (Δ < 0.005).

**Interpretation:** the CRF does not recover corrupted text by recognizing
corrupted spellings. It recovers it by recognizing **structure** — `mgdL`
is a unit because it *follows a digit that follows a test name*, not
because the letters resemble `mg/dL`. **Structure beats spelling on
noisy input.**
    """)


# ---------------------------------------------------------------- footer
st.markdown(
    '<div style="text-align:center;color:#94a3b8;font-size:0.8rem;'
    'margin-top:3rem;padding-top:1.5rem;border-top:1px solid #e2e8f0;">'
    'CRF NER · Relation Extraction · Feature Ablation · '
    'tested on 15 held-out reports per input quality'
    '</div>',
    unsafe_allow_html=True,
)