# Project Decision Log

Running log of design decisions, fixes, findings, and things-to-remember.
Every time you make a non-obvious choice, add an entry. This becomes the
backbone of your report's methodology and limitations sections.

---

## Project setup
- Python version: 3.12
- OS: Windows
- Project path: C:\Users\Shradha\Desktop\NLP-Project
- Venv: `venv\Scripts\Activate.ps1`
- Poppler: `C:\poppler-26.09.0\Library\bin` (referenced explicitly in `make_scanned_versions.py` — avoids PATH issues)

---

## Phase 1 — Data generation and OCR

### Synthetic data
- 100 synthetic lab reports generated across 5 panels: lipid, thyroid, CBC, LFT, KFT
- Generator: `scripts/generate_synthetic_report.py` (reportlab)
- Layout: header, patient block, table with columns Test Name | Result | Unit | Reference Range
- Abnormal values injected ~40% of the time to ensure HIGH/LOW/NORMAL variety

### Scanned images
- 100 PDFs → 100 clean + 100 degraded PNGs at 200 DPI
- Degradation: rotation ±2.5°, Gaussian blur 1.0–2.4 px, brightness ×0.75–0.92, noise σ=12–22
- Decision: paired clean/degraded per report so robustness comparison is legitimate
- Rationale: without pairing, clean vs degraded differences could be due to report content, not degradation

### OCR
- PDFs: PyMuPDF (word-level bboxes, confidence = 1.0)
- Scans: EasyOCR (line-level boxes split into words by proportional width)
- EasyOCR runs on CPU (gpu=False in `easyocr_extractor.py`)

### Processed dataset
- 300 files in `data/processed/`: 100 pdf, 100 clean_ocr, 100 degraded_ocr
- Manifest: `data/processed/manifest.csv` (id, source, path, n_words)
- `build_dataset.py` supports resume — Ctrl+C and re-run safely skips existing files

### Degradation validation
- Paired comparison: 63.9% token preservation rate (clean → degraded)
- Chosen target band: 40–70% (realistic but learnable)
- Visible errors on degraded: Choleaterd, Makcai, Stoet, Reterence, token splits (36 → 3 6), unit mangling (mgdL on clean, worse on degraded)
- Decision: keep this degradation level. Stronger made values unrecoverable; weaker made errors invisible.

### Known issues discovered
- EasyOCR on clean scans still confuses `/` with `l` → mg/dL becomes mgldL
  - This is real OCR behavior on clean input, motivates the cleaning stage
- Degraded scans sometimes split single numbers into multiple tokens
  - Motivated the I-VALUE label in annotation and needs handling in relation extraction

---

## Phase 2 — Annotation (in progress)
(Add entries here as you complete annotation steps.)

---

## Open questions
- (add as they come up)

## Phase 3 — Regex NER baseline (test set)
- pdf:          1.000
- ocr_clean:    0.975
- ocr_degraded: 0.853  ← the interesting number
- Overall:      0.960

## Interpretation
Regex (exact match) achieves ceiling on clean PDF because the
test-name vocabulary is fixed. It is the right tool for structured
synthetic data, but it degrades under OCR noise (TEST recall 0.781,
VALUE recall 0.756 on degraded).

## Narrative for the report
The interesting comparison is NOT on PDF (all methods will tie).
It is on DEGRADED OCR, where learned features and pretrained
representations are expected to close the 0.85→0.95 gap.

## Known methodological concern
The annotator and regex baseline share algorithm structure, so
PDF F1 of 1.0 is partly circular. Mitigation: (a) CRF/BERT trained
on the same labels must still generalize to noisy input, which is
a genuine learning test; (b) we will hand-annotate 5 reports to
verify labels are correct (Phase 2 QA extension).

## Phase 3 — Regex baseline
- PDF: 1.000
- Clean OCR: 0.975
- Degraded OCR: 0.853 ← the number that matters

## Interpretation
The 15-point drop from PDF to degraded OCR is the signal.
CRF and BERT will be tested against this number, not against PDF.

## Phase 4 prediction (before running)
- Expected CRF on PDF: ~1.000 (tie with regex)
- Expected CRF on clean OCR: ~0.970
- Expected CRF on degraded OCR: 0.88 – 0.93 (if features help)
- Expected CRF on degraded OCR: 0.85 – 0.87 (if features do NOT help)

## The feature that should help most: character n-gram features
## (prefixes/suffixes of length 2-4). "Chol" prefix appears in both
## "Cholesterol" and "Choleaterd", so the CRF can recognize both.

## Phase 4 prediction (before running)
- Expected CRF on degraded OCR: 0.88 – 0.93 (if char n-grams help)
- Rationale: prefix/suffix features should let CRF recognize
  "Choleaterd" via shared "Chol" prefix with "Cholesterol".

  ## Phase 4 — CRF NER (test set)

| Method | pdf | clean_ocr | degraded_ocr |
|---|---|---|---|
| Regex | 1.000 | 0.975 | 0.853 |
| CRF   | 1.000 | 1.000 | 0.919 |
| Δ     | — | +2.5 | **+6.6** |

Per-entity F1 on degraded OCR:
| Entity | Regex | CRF | Δ |
|---|---|---|---|
| VALUE     | 0.810 | 0.944 | +13.4 |
| TEST      | 0.870 | 0.937 | +6.7 |
| UNIT      | 0.903 | 0.889 | -1.4 |
| REF_RANGE | 0.857 | 0.824 | -3.3 |

## Interpretation
CRF gains are concentrated in long-token entities (VALUE, TEST) where
character n-grams help recover corrupted prefixes/suffixes. Short
entities (UNIT, REF_RANGE) slightly regress because full-token
corruption removes all signal. This motivates Phase 5: pretrained
contextual embeddings may handle short corrupted tokens better.

## Prediction was correct: char n-grams closed the OCR gap.

## Phase 5 prediction (before running)
- PubMedBERT on degraded OCR: expected 0.92 – 0.96
  Rationale: subword tokenization breaks "Choleaterd" into ["Cho", "lea", "terd"]
  which may align better with "Cholesterol" -> ["Cho", "les", "ter", "ol"] than
  character n-grams alone. BERT also sees surrounding context, which helps
  short tokens like mg/dL by looking at neighbors.
- Risk: if train data (PDF + clean OCR) does not include enough degraded examples,
  BERT may overfit to clean text — same failure mode CRF avoided but BERT
  has more capacity to overfit.

  ## Phase 5 — Final decision

Attempted: DistilBERT (2 runs), PubMedBERT (attempted on CPU, did not complete).
Decision: not switching to PubMedBERT on Colab. Diminishing returns —
the data-scale finding is established with DistilBERT.

Final NER comparison:
| Method | pdf | clean_ocr | degraded_ocr | avg |
| Regex      | 1.000 | 0.975 | 0.853 | 0.943 |
| CRF        | 1.000 | 1.000 | 0.919 | 0.973 |
| DistilBERT | 0.876 | 0.886 | 0.714 | 0.825 |

Finding: at 210 training files, feature-based CRF beats fine-tuned transformers.
Diagnosed via PDF precision 0.991 / recall 0.785 (under-fitting signature),
not truncation (max subword length 195 < 256).

## Phase 6 — Relation extraction (starting now)

## Phase 6 — Relation extraction (proximity heuristic)

ORACLE F1: 1.000 on all sources (row-grouping logic validated).

END-TO-END tuple F1 (CRF NER → proximity grouping):
| Source | Gold | Pred | P | R | F1 |
| pdf          | 70 | 70 | 1.000 | 1.000 | 1.000 |
| clean_ocr    | 72 | 72 | 1.000 | 1.000 | 1.000 |
| degraded_ocr | 55 | 53 | 0.906 | 0.873 | 0.889 |
| OVERALL      | 185 | 183 | 0.973 | 0.962 | 0.967 |

## Error propagation analysis
Entity F1 degraded = 0.919
Tuple  F1 degraded = 0.889
Drop = 0.030 (3 points) — mild

Interpretation: CRF makes precision-first errors. When it misses an
entity, it usually misses the whole tuple, not a partial field. So the
pipeline does not compound errors heavily. 48/55 tuples correct on
degraded, with 7 misses and 5 false positives.

This is a positive quality signal for CRF and for the rule-based
relation extractor.

## Implications for the capstone
The 0.889 tuple F1 on degraded input is sufficient for downstream
abnormality detection — the >88% correct tuples mean ~88% of the
high/low/normal classifications will be correct on OCR input.

## Phase 8 — CRF feature ablation (FINAL)

| Variant            | pdf   | clean_ocr | degraded | overall |
|--------------------|-------|-----------|----------|---------|
| Full CRF           | 1.000 | 1.000     | 0.919    | 0.982   |
| No char n-grams    | 1.000 | 1.000     | 0.918    | 0.982   |
| No position        | 1.000 | 1.000     | 0.916    | 0.981   |
| No context         | 1.000 | 1.000     | 0.866    | 0.970   |

Δ vs Full CRF (degraded):
  No context      -0.0531  ← the only meaningful drop
  No position     -0.0038  (noise)
  No char n-grams -0.0017  (noise)

## THE KEY FINDING (goes in the report abstract)

The CRF's advantage over regex on degraded OCR comes almost entirely
from context features (previous/next word, neighbor digit/operator
flags), not from character n-grams or position features.

Remove context  → F1 drops 6.6 → 0.866 (ties regex's 0.853)
Remove char n-grams → F1 drops to 0.918 (noise)
Remove position → F1 drops to 0.916 (noise)

## Interpretation

The CRF does not recover corrupted text by recognizing corrupted
spellings. It recovers it by recognizing structural position:
"mgdL" is a unit not because the letters resemble "mg/dL", but
because it follows a digit that follows a test name.

This is STRUCTURE over SPELLING on noisy input. A more sophisticated
and more defensible claim than the intuitive "char n-grams win".

## Why position features do not help
Context features (prev_word, next_is_digit, prev_has_lt) already
encode structural relationships. prev_word = "Cholesterol" tells the
model "this is a value in a test row" more reliably than x_bucket = 3.
Absolute coordinates are redundant once the local token neighborhood
is known.

## Cross-reference to capstone

This finding directly motivates the layout-aware component of the
capstone: structural information is what recovers signal from OCR
errors. The NLP project proves this at the token level; the capstone
extends it to the document level via bbox-based relation extraction.