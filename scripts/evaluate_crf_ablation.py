"""
CRF feature ablation.

Trains 4 CRF variants (skips training if checkpoint exists):
1. Full CRF         : char n-grams + position + context (the baseline)
2. No char n-grams  : only word/position/context features
3. No position      : only word/char n-grams/context features
4. No context       : only word/char n-grams/position features

Evaluates each on the test set by input source.
The comparison isolates WHICH feature group is responsible for OCR robustness.

Skip-if-exists behavior:
- First run: trains all 4 variants (~8-12 min).
- Subsequent runs: reuses existing checkpoints, only evaluates (~10 sec).
- To force retrain: delete the checkpoint file in checkpoints/.
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from collections import defaultdict
from seqeval.metrics import f1_score
from src.ner.crf_model import train_crf, load_crf, predict_record


VARIANTS = [
    {
        "name": "Full CRF",
        "path": "checkpoints/crf_full.pkl",
        "flags": dict(use_char_ngrams=True, use_position=True, use_context=True),
    },
    {
        "name": "No char n-grams",
        "path": "checkpoints/crf_no_char.pkl",
        "flags": dict(use_char_ngrams=False, use_position=True, use_context=True),
    },
    {
        "name": "No position",
        "path": "checkpoints/crf_no_position.pkl",
        "flags": dict(use_char_ngrams=True, use_position=False, use_context=True),
    },
    {
        "name": "No context",
        "path": "checkpoints/crf_no_context.pkl",
        "flags": dict(use_char_ngrams=True, use_position=True, use_context=False),
    },
]


def evaluate_variant(model_path, flags):
    """Load a trained CRF and evaluate on the test set by input source."""
    crf = load_crf(model_path)
    per_src = defaultdict(lambda: {"gold": [], "pred": []})

    with open("data/splits/test.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            pred = predict_record(crf, rec, **flags)
            per_src[rec["source"]]["gold"].append(rec["labels"])
            per_src[rec["source"]]["pred"].append(pred)

    results = {}
    for src in ("pdf", "ocr_clean", "ocr_degraded"):
        d = per_src[src]
        results[src] = f1_score(d["gold"], d["pred"], average="micro")

    all_g = sum((v["gold"] for v in per_src.values()), [])
    all_p = sum((v["pred"] for v in per_src.values()), [])
    results["overall"] = f1_score(all_g, all_p, average="micro")
    return results


def main():
    # 1. Train all variants (skip if checkpoint exists)
    for v in VARIANTS:
        print("\n" + "=" * 72)
        if os.path.exists(v["path"]):
            print(f"SKIP: {v['name']} (checkpoint exists at {v['path']})")
            print("=" * 72)
            continue

        print(f"TRAINING: {v['name']}")
        print("=" * 72)
        train_crf(
            train_path="data/splits/train.jsonl",
            dev_path="data/splits/dev.jsonl",
            model_path=v["path"],
            c1=0.1, c2=0.1, max_iter=100,
            verbose=True,
            **v["flags"],
        )

    # 2. Evaluate all variants
    print("\n" + "=" * 72)
    print("CRF FEATURE ABLATION — TEST SET")
    print("=" * 72)
    header = f"\n{'Variant':<22} {'pdf':>8} {'clean_ocr':>12} {'degraded':>12} {'overall':>10}"
    print(header)
    print("-" * 72)

    all_results = {}
    for v in VARIANTS:
        res = evaluate_variant(v["path"], v["flags"])
        all_results[v["name"]] = res
        print(f"{v['name']:<22} {res['pdf']:>8.4f} {res['ocr_clean']:>12.4f} "
              f"{res['ocr_degraded']:>12.4f} {res['overall']:>10.4f}")

    # 3. Compute deltas vs Full CRF
    baseline = all_results["Full CRF"]
    print("\n" + "=" * 72)
    print("DELTA vs FULL CRF (negative = feature group was helping)")
    print("=" * 72)
    print(f"\n{'Variant':<22} {'Δ pdf':>10} {'Δ clean':>12} {'Δ degraded':>14}")
    print("-" * 72)
    for name, res in all_results.items():
        if name == "Full CRF":
            continue
        d_pdf = res["pdf"] - baseline["pdf"]
        d_cln = res["ocr_clean"] - baseline["ocr_clean"]
        d_deg = res["ocr_degraded"] - baseline["ocr_degraded"]
        print(f"{name:<22} {d_pdf:>+10.4f} {d_cln:>+12.4f} {d_deg:>+14.4f}")

    # 4. Auto interpretation
    print("\n" + "=" * 72)
    print("INTERPRETATION")
    print("=" * 72)

    deltas = {name: res["ocr_degraded"] - baseline["ocr_degraded"]
              for name, res in all_results.items() if name != "Full CRF"}

    if not deltas:
        return

    biggest_drop_name = min(deltas, key=deltas.get)
    biggest_drop = deltas[biggest_drop_name]

    if abs(biggest_drop) < 0.005:
        print("All feature groups are redundant on this data.")
        print("Removing any single group does not change degraded F1 materially.")
        print("The CRF's advantage over regex comes from the combination,")
        print("not from any single feature group.")
    else:
        print(f"The largest drop on degraded OCR is from '{biggest_drop_name}' "
              f"(Δ = {biggest_drop:+.4f}).")
        print(f"This is the feature group doing the most work on noisy input.")

    print("\nAll deltas on degraded OCR (sorted by magnitude):")
    for name in sorted(deltas, key=deltas.get):
        print(f"  {name:<22} {deltas[name]:+.4f}")


if __name__ == "__main__":
    main()