"""
Fine-tune DistilBERT for NER.

Why DistilBERT instead of PubMedBERT:
- PubMedBERT is 110M params; on CPU it takes ~40+ min to train 5 epochs,
  which freezes laptops. DistilBERT is 66M and ~3x faster on CPU.
- Same tokenizer (WordPiece), same subword-alignment concepts, same
  fine-tuning pipeline. Only the pretraining corpus differs (general
  English instead of biomedical). Noted as a limitation in the report.

Key optimizations for CPU:
- max_len=128 (reports are ~85 words → ~120 subwords, so 128 is enough)
- 2 epochs (enough for fine-tuning on small data)
- batch_size=8
- dataloader_num_workers=0 (no multiprocessing overhead)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch
import numpy as np
from transformers import TrainingArguments, Trainer
from seqeval.metrics import f1_score as seq_f1

from src.ner.bert_ner import (
    LabReportDataset, load_jsonl,
    LABEL2ID, ID2LABEL, LABELS,
)

MODEL_NAME = "distilbert-base-uncased"
MAX_LEN = 256   # was 128


class WeightedTrainer(Trainer):
    def __init__(self, class_weights=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        loss_fn = torch.nn.CrossEntropyLoss(
            weight=self.class_weights, ignore_index=-100,
        )
        loss = loss_fn(logits.view(-1, logits.size(-1)), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    true_labels, true_preds = [], []
    for pred_row, lab_row in zip(preds, labels):
        tl, tp = [], []
        for p, l in zip(pred_row, lab_row):
            if l == -100:
                continue
            tl.append(ID2LABEL[l])
            tp.append(ID2LABEL[p])
        true_labels.append(tl)
        true_preds.append(tp)
    return {"f1": seq_f1(true_labels, true_preds, average="micro")}


def count_class_weights(records, num_labels):
    from collections import Counter
    counts = Counter()
    for rec in records:
        for l in rec["labels"]:
            counts[LABEL2ID[l]] += 1
    total = sum(counts.values())
    weights = []
    for i in range(num_labels):
        c = counts.get(i, 0)
        w = total / (num_labels * max(c, 1))
        weights.append(min(w, 10.0))
    return torch.tensor(weights, dtype=torch.float)


def main():
    from transformers import AutoTokenizer, AutoModelForTokenClassification

    train = load_jsonl("data/splits/train.jsonl")
    dev = load_jsonl("data/splits/dev.jsonl")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    train_ds = LabReportDataset(train, tokenizer, max_len=MAX_LEN)
    dev_ds = LabReportDataset(dev, tokenizer, max_len=MAX_LEN)

    class_weights = count_class_weights(train, len(LABELS))
    print("Class weights:", class_weights[:9].tolist())

    args = TrainingArguments(
        output_dir="checkpoints/bert-ner",
        learning_rate=5e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,
        num_train_epochs=6,
        
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=20,
        report_to="none",
        remove_unused_columns=False,
        dataloader_num_workers=0,
    )

    trainer = WeightedTrainer(
        class_weights=class_weights,
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=dev_ds,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    trainer.save_model("checkpoints/bert-ner-final")
    tokenizer.save_pretrained("checkpoints/bert-ner-final")
    print("Saved to checkpoints/bert-ner-final")


if __name__ == "__main__":
    main()