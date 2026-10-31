"""
PubMedBERT NER with subword alignment.

Key concepts:
1. is_split_into_words=True -> tokenizer treats input as pre-tokenized words
2. word_ids() -> tells us which word each subword came from
3. -100 -> ignore index, so continuation subwords and special tokens
   do not contribute to loss or metrics
"""

import json
import torch
import numpy as np
from torch.utils.data import Dataset
from transformers import AutoTokenizer, AutoModelForTokenClassification

LABELS = [
    "O",
    "B-TEST", "I-TEST",
    "B-VALUE", "I-VALUE",
    "B-UNIT", "I-UNIT",
    "B-REF_RANGE", "I-REF_RANGE",
    "B-LOWER_BOUND", "I-LOWER_BOUND",
    "B-UPPER_BOUND", "I-UPPER_BOUND",
    "B-QUALITATIVE_RESULT", "I-QUALITATIVE_RESULT",
]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}


class LabReportDataset(Dataset):
    def __init__(self, records, tokenizer, max_len=512):
        self.records = records
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        rec = self.records[idx]
        words = rec["words"]
        word_labels = rec["labels"]

        encoding = self.tokenizer(
            words,
            is_split_into_words=True,
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt",
        )

        word_ids = encoding.word_ids(batch_index=0)
        labels = []
        prev_word = None
        for wid in word_ids:
            if wid is None:
                labels.append(-100)   # special tokens
            elif wid != prev_word:
                # First subword of this word gets the actual label
                labels.append(LABEL2ID[word_labels[wid]])
            else:
                # Continuation subword: ignore
                labels.append(-100)
            prev_word = wid

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def get_model_and_tokenizer(model_name="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=len(LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    return model, tokenizer