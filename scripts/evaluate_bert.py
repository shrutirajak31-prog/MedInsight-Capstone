"""
Evaluate fine-tuned DistilBERT on the test set, by input source.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import torch
from collections import defaultdict
from transformers import AutoTokenizer, AutoModelForTokenClassification
from seqeval.metrics import classification_report, f1_score

from src.ner.bert_ner import ID2LABEL, load_jsonl

MAX_LEN = 128


def predict_record(model, tokenizer, words):
    enc = tokenizer(
        words, is_split_into_words=True,
        truncation=True, max_length=MAX_LEN,
        padding="max_length", return_tensors="pt",
    )
    with torch.no_grad():
        logits = model(**enc).logits
    preds = logits.argmax(-1).squeeze(0).tolist()
    word_ids = enc.word_ids(batch_index=0)

    word_preds = []
    prev = None
    for wid, p in zip(word_ids, preds):
        if wid is None:
            continue
        if wid != prev:
            word_preds.append(ID2LABEL[p])
        prev = wid
    while len(word_preds) < len(words):
        word_preds.append("O")
    return word_preds[:len(words)]


def main():
    model = AutoModelForTokenClassification.from_pretrained("checkpoints/bert-ner-final")
    tokenizer = AutoTokenizer.from_pretrained("checkpoints/bert-ner-final")
    model.eval()

    per_source = defaultdict(lambda: {"gold": [], "pred": []})
    for rec in load_jsonl("data/splits/test.jsonl"):
        pred = predict_record(model, tokenizer, rec["words"])
        per_source[rec["source"]]["gold"].append(rec["labels"])
        per_source[rec["source"]]["pred"].append(pred)

    print("=" * 70)
    print("DistilBERT NER — TEST SET")
    print("=" * 70)
    print(f"\n{'Source':<20} {'Files':>6} {'Micro-F1':>10}")
    print("-" * 40)
    all_gold, all_pred = [], []
    for src in ("pdf", "ocr_clean", "ocr_degraded"):
        d = per_source[src]
        f1 = f1_score(d["gold"], d["pred"], average="micro")
        print(f"{src:<20} {len(d['gold']):>6} {f1:>10.4f}")
        all_gold.extend(d["gold"])
        all_pred.extend(d["pred"])
    print(f"{'OVERALL':<20} {len(all_gold):>6} {f1_score(all_gold, all_pred, average='micro'):>10.4f}")

    print("\n" + "=" * 70)
    for src in ("pdf", "ocr_clean", "ocr_degraded"):
        print(f"\n--- {src.upper()} ---")
        print(classification_report(
            per_source[src]["gold"], per_source[src]["pred"],
            digits=3, zero_division=0,
        ))


if __name__ == "__main__":
    main()