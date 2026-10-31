"""
CRF NER model with character n-gram and position features.

Feature flags (all default True, so the original model is preserved):
- use_char_ngrams:  prefix/suffix features (the OCR-robustness signal)
- use_position:     x/y bucket features (the layout signal)
- use_context:      prev/next word features (the sequence signal)

Ablation: set a flag to False to train a variant without that feature group.
"""

import json
import joblib
import os
from pathlib import Path


def _shape(s):
    shape = ""
    for c in s[:10]:
        if c.isdigit():
            shape += "d"
        elif c.isupper():
            shape += "X"
        elif c.islower():
            shape += "x"
        else:
            shape += c
    return shape


def word_features(words, bboxes, i, max_x, max_y,
                  use_char_ngrams=True, use_position=True, use_context=True):
    """Extract features for one token."""
    w = words[i]
    wl = w.lower().strip(".,:;()[]")
    bbox = bboxes[i]

    cx = ((bbox[0] + bbox[2]) / 2) / (max_x or 1)
    cy = ((bbox[1] + bbox[3]) / 2) / (max_y or 1)

    feats = {
        "bias": 1.0,
        "word": wl,
        "is_digit": wl.isdigit(),
        "has_digit": any(c.isdigit() for c in wl),
        "has_slash": "/" in wl,
        "has_lt": "<" in wl,
        "has_gt": ">" in wl,
        "has_dash": "-" in wl or "–" in wl,
        "has_period": "." in wl,
        "is_alpha": wl.replace("-", "").replace("'", "").isalpha() and len(wl) > 0,
        "len": min(len(wl), 20),
        "len_bucket": ("short" if len(wl) <= 2
                       else "medium" if len(wl) <= 6
                       else "long"),
        "shape": _shape(wl),
    }

    if use_position:
        feats["x_bucket"] = int(cx * 10)
        feats["y_bucket"] = int(cy * 20)

    if use_char_ngrams:
        for n in (2, 3, 4):
            if len(wl) >= n:
                feats[f"pre{n}"] = wl[:n]
                feats[f"suf{n}"] = wl[-n:]

    if use_context:
        if i > 0:
            prev = words[i - 1].lower().strip(".,:;()[]")
            feats["prev_word"] = prev
            feats["prev_is_digit"] = prev.isdigit()
            feats["prev_has_lt"] = "<" in prev
            feats["prev_has_gt"] = ">" in prev
            feats["prev_shape"] = _shape(prev)
        else:
            feats["BOS"] = True

        if i < len(words) - 1:
            nxt = words[i + 1].lower().strip(".,:;()[]")
            feats["next_word"] = nxt
            feats["next_is_digit"] = nxt.isdigit()
            feats["next_has_slash"] = "/" in nxt
            feats["next_shape"] = _shape(nxt)
        else:
            feats["EOS"] = True

    return feats


def featurize_record(record, use_char_ngrams=True, use_position=True,
                     use_context=True):
    """Convert one annotated record to (X, y)."""
    words = record["words"]
    bboxes = record["bboxes"]
    labels = record["labels"]

    max_x = max((b[2] for b in bboxes), default=1) or 1
    max_y = max((b[3] for b in bboxes), default=1) or 1

    X = [
        word_features(words, bboxes, i, max_x, max_y,
                      use_char_ngrams=use_char_ngrams,
                      use_position=use_position,
                      use_context=use_context)
        for i in range(len(words))
    ]
    return X, labels


def load_jsonl(path):
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    return records


def train_crf(train_path, dev_path, model_path,
              c1=0.1, c2=0.1, max_iter=100, verbose=True,
              use_char_ngrams=True, use_position=True, use_context=True):
    """Train a CRF and save it to model_path."""
    from sklearn_crfsuite import CRF

    train = load_jsonl(train_path)
    dev = load_jsonl(dev_path)

    X_train, y_train = [], []
    for i, rec in enumerate(train):
        X, y = featurize_record(rec,
                                use_char_ngrams=use_char_ngrams,
                                use_position=use_position,
                                use_context=use_context)
        X_train.append(X)
        y_train.append(y)
        if verbose and (i + 1) % 20 == 0:
            print(f"  featurized {i + 1}/{len(train)} training files")

    print(f"Training CRF on {len(X_train)} files "
          f"({sum(len(x) for x in X_train)} tokens)")
    print(f"Feature flags: char_ngrams={use_char_ngrams}, "
          f"position={use_position}, context={use_context}")

    crf = CRF(
        algorithm="lbfgs",
        c1=c1,
        c2=c2,
        max_iterations=max_iter,
        all_possible_transitions=True,
    )
    crf.fit(X_train, y_train)
    print("Training complete.")

    X_dev, y_dev = [], []
    for rec in dev:
        X, y = featurize_record(rec,
                                use_char_ngrams=use_char_ngrams,
                                use_position=use_position,
                                use_context=use_context)
        X_dev.append(X)
        y_dev.append(y)
    y_pred = crf.predict(X_dev)

    from seqeval.metrics import f1_score
    dev_f1 = f1_score(y_dev, y_pred, average="micro")
    print(f"Dev micro-F1: {dev_f1:.4f}")

    os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)
    joblib.dump(crf, model_path)
    print(f"Saved to {model_path}")
    return crf


def predict_record(crf, record, use_char_ngrams=True, use_position=True,
                   use_context=True):
    """Predict labels for one record."""
    X, _ = featurize_record(record,
                            use_char_ngrams=use_char_ngrams,
                            use_position=use_position,
                            use_context=use_context)
    return crf.predict_single(X)


def load_crf(model_path):
    return joblib.load(model_path)