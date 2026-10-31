import json
from pathlib import Path
import re

def base_report_id(rid):
    for suffix in ("_pdf", "_clean_ocr", "_degraded_ocr"):
        if rid.endswith(suffix):
            rid = rid[:-len(suffix)]
            break
    m = re.match(r"^(report_\d+)", rid)
    return m.group(1) if m else rid

sets = {}
for name in ('train', 'dev', 'test'):
    sets[name] = set()
    for line in open(f'data/splits/{name}.jsonl'):
        d = json.loads(line)
        sets[name].add(base_report_id(d['id']))
    print(f'{name}: {len(sets[name])} unique base reports')

print('train / dev overlap :', len(sets['train'] & sets['dev']))
print('train / test overlap:', len(sets['train'] & sets['test']))
print('dev / test overlap  :', len(sets['dev'] & sets['test']))