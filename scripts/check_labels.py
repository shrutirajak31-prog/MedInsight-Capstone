import json, glob, collections

counts = collections.Counter()
for f in glob.glob('data/annotated/*.json'):
    d = json.load(open(f))
    counts.update(d['labels'])

total = sum(counts.values())
for lab, c in counts.most_common():
    pct = 100 * c / total
    print(f'{lab:20s} {c:8d}  {pct:6.2f}%')
print(f'{"TOTAL":20s} {total:8d}')