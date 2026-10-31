import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Create output directory
OUTPUT_DIR = "Paper_Results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Global style for publication-ready charts
plt.style.use('default')
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'figure.autolayout': True
})

print(f"Generating assets in '{OUTPUT_DIR}'...")

# ==========================================
# 1. LABEL DISTRIBUTION
# ==========================================
labels = ['O', 'B-TEST', 'B-VALUE', 'B-UNIT', 'I-REF_RANGE', 'B-REF_RANGE', 'I-TEST', 'I-VALUE']
counts = [13911, 1588, 1490, 1046, 1028, 860, 544, 84]

df_labels = pd.DataFrame({'Label': labels, 'Count': counts})
df_labels['Percentage'] = (df_labels['Count'] / df_labels['Count'].sum()) * 100
df_labels.to_csv(f"{OUTPUT_DIR}/table_1_label_distribution.csv", index=False)
df_labels.to_markdown(f"{OUTPUT_DIR}/table_1_label_distribution.md", index=False)

fig, ax = plt.subplots(figsize=(10, 5))
colors = ['#94a3b8' if l == 'O' else '#68e8ff' for l in labels]
bars = ax.bar(labels, counts, color=colors)
ax.set_title('Label Distribution in Annotated Dataset')
ax.set_ylabel('Token Count')
ax.set_yscale('log') # Log scale because 'O' is much larger
for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, yval + 100, int(yval), ha='center', va='bottom', fontsize=9)
plt.xticks(rotation=45)
plt.savefig(f"{OUTPUT_DIR}/chart_1_label_distribution.png", dpi=300)
plt.close()

# ==========================================
# 2. NER MODEL COMPARISON
# ==========================================
models = ['Regex Baseline', 'CRF (Proposed)', 'DistilBERT']
pdf_f1 = [1.000, 1.000, 0.876]
clean_ocr_f1 = [0.975, 1.000, 0.886]
degraded_f1 = [0.853, 0.919, 0.714]

df_ner = pd.DataFrame({
    'Model': models,
    'Clean PDF F1': pdf_f1,
    'Clean OCR F1': clean_ocr_f1,
    'Degraded OCR F1': degraded_f1
})
df_ner.to_csv(f"{OUTPUT_DIR}/table_2_ner_comparison.csv", index=False)
df_ner.to_markdown(f"{OUTPUT_DIR}/table_2_ner_comparison.md", index=False)

x = np.arange(len(models))
width = 0.25

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x - width, pdf_f1, width, label='Clean PDF', color='#2aa8c2')
ax.bar(x, clean_ocr_f1, width, label='Clean OCR', color='#68e8ff')
ax.bar(x + width, degraded_f1, width, label='Degraded OCR', color='#f87171')

ax.set_ylabel('Micro-F1 Score')
ax.set_title('NER Performance Across Input Qualities')
ax.set_xticks(x)
ax.set_xticklabels(models)
ax.set_ylim(0.5, 1.1)
ax.legend(loc='lower left')
ax.grid(axis='y', linestyle='--', alpha=0.7)
plt.savefig(f"{OUTPUT_DIR}/chart_2_ner_comparison.png", dpi=300)
plt.close()

# ==========================================
# 3. CRF ABLATION STUDY
# ==========================================
variants = ['Full CRF', 'No Char N-grams', 'No Position', 'No Context']
ablation_f1 = [0.919, 0.918, 0.916, 0.866]
drop = ['—', '-0.001', '-0.003', '-0.053']

df_ablation = pd.DataFrame({
    'Variant': variants,
    'Degraded OCR F1': ablation_f1,
    'Drop vs Full CRF': drop
})
df_ablation.to_csv(f"{OUTPUT_DIR}/table_3_ablation_study.csv", index=False)
df_ablation.to_markdown(f"{OUTPUT_DIR}/table_3_ablation_study.md", index=False)

fig, ax = plt.subplots(figsize=(8, 5))
colors = ['#4ade80', '#94a3b8', '#94a3b8', '#f87171']
bars = ax.bar(variants, ablation_f1, color=colors, width=0.6)

ax.set_ylabel('Degraded OCR Micro-F1')
ax.set_title('CRF Feature Ablation Study')
ax.set_ylim(0.80, 0.95)

for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, yval + 0.002, round(yval, 3), ha='center', va='bottom', fontweight='bold')

ax.grid(axis='y', linestyle='--', alpha=0.7)
plt.savefig(f"{OUTPUT_DIR}/chart_3_ablation_study.png", dpi=300)
plt.close()

# ==========================================
# 4. RELATION EXTRACTION PERFORMANCE
# ==========================================
sources = ['Clean PDF', 'Clean OCR', 'Degraded OCR', 'Overall']
precision = [1.000, 1.000, 0.906, 0.973]
recall = [1.000, 1.000, 0.873, 0.962]
f1 = [1.000, 1.000, 0.889, 0.967]

df_relation = pd.DataFrame({
    'Source': sources,
    'Precision': precision,
    'Recall': recall,
    'F1-Score': f1
})
df_relation.to_csv(f"{OUTPUT_DIR}/table_4_relation_extraction.csv", index=False)
df_relation.to_markdown(f"{OUTPUT_DIR}/table_4_relation_extraction.md", index=False)

print("\n✅ All done!")
print(f"Check the '{OUTPUT_DIR}' folder. You will find CSV files (for Excel/Word) and PNG images (for the paper).")