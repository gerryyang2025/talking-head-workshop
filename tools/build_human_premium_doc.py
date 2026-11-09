"""Render docs/HUMAN_PREMIUM.md from tools/HUMAN_PREMIUM.template.md + prompts/overlays/human_premium.json.

The overlay JSON is the single source of truth for every copy-paste snippet, so the doc can never drift from
what `istream prompts overlay` and GENERATE_PACK.md actually apply.
Run from the package root:  python3 tools/build_human_premium_doc.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tpl = open(os.path.join(ROOT, "tools", "HUMAN_PREMIUM.template.md"), encoding="utf-8").read()
ov = json.load(open(os.path.join(ROOT, "prompts", "overlays", "human_premium.json"), encoding="utf-8"))

score = ["| # | 检查（是 / 否） | Check (yes / no) |", "|---|---|---|"]
for it in ov["scorecard"]:
    score.append(f"| {it['id']} | {it['zh']} | {it['en']} |")

values = {"SCORECARD_TABLE": "\n".join(score), "scorecard_rule.zh": ov["scorecard_rule"]["zh"]}
for key in ("setting_append", "performance_append", "first_frame_append", "style_line"):
    for lang in ("en", "zh"):
        values[f"{key}.{lang}"] = ov[key][lang]


def sub(m):
    k = m.group(1)
    if k not in values:
        sys.exit(f"unknown placeholder {k}")
    return values[k]


out = re.sub(r"\{\{([A-Za-z_.]+)\}\}", sub, tpl)
assert "{{" not in out
path = os.path.join(ROOT, "docs", "HUMAN_PREMIUM.md")
open(path, "w", encoding="utf-8").write(out)
print("wrote", path, len(out), "chars")
