"""
Train the CRF NER model.
Run: python scripts/train_crf.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ner.crf_model import train_crf


if __name__ == "__main__":
    train_crf(
        train_path="data/splits/train.jsonl",
        dev_path="data/splits/dev.jsonl",
        model_path="checkpoints/crf.pkl",
        c1=0.1,
        c2=0.1,
        max_iter=100,
    )