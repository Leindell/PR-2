"""Оценка качества поиска на эталонном наборе вопросов: Recall@1/3/5 и MRR@5 для трёх режимов."""
import json
from pathlib import Path

from search import MODES

golden = json.loads(Path("golden.json").read_text(encoding="utf-8"))
K = 5
lines = ["| Режим | Recall@1 | Recall@3 | Recall@5 | MRR@5 |", "|---|---|---|---|---|"]
misses = []
for mode, fn in MODES.items():
    hits = {1: 0, 3: 0, 5: 0}
    rr = 0.0
    for g in golden:
        found = [(r[4], r[2]) for r in fn(g["q"], K)]
        rank = next((i for i, f in enumerate(found, 1) if f == (g["doc"], g["section"])), None)
        if rank:
            rr += 1 / rank
            for k in hits:
                hits[k] += rank <= k
        elif mode == "hybrid":
            misses.append(f"- `{g['q']}` -> ожидали {g['doc']} / {g['section']}, топ-1: {found[0] if found else '-'}")
    n = len(golden)
    lines.append(f"| {mode} | {hits[1]/n:.2f} | {hits[3]/n:.2f} | {hits[5]/n:.2f} | {rr/n:.2f} |")

report = "\n".join([f"Вопросов в эталоне: {len(golden)}", ""] + lines
                   + ["", "Промахи гибрида (нет нужного раздела в топ-5):"] + (misses or ["- нет"]))
print(report)
Path("/results").mkdir(exist_ok=True)
Path("/results/eval.md").write_text(report + "\n", encoding="utf-8")
