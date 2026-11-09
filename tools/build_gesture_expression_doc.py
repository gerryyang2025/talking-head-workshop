"""Render docs/GESTURE_EXPRESSION.md from tools/GESTURE_EXPRESSION.template.md + prompts/overlays/gesture_expression.json.

The overlay JSON is the single source of truth for every lexicon entry, timeline, snippet, mapping and scorecard row,
so the doc can never drift from what `istream prompts overlay --gesture`, GENERATE_PACK.md and the planner use.
Run from the package root:  python3 tools/build_gesture_expression_doc.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from istream import prompts as pm  # noqa: E402

with open(os.path.join(ROOT, "tools", "GESTURE_EXPRESSION.template.md"), encoding="utf-8") as _f:
    tpl = _f.read()
ov = pm.load_overlay("gesture_expression")
lib = pm.load(os.path.join(ROOT, "prompts", "library.json"))

IDS = {}
for it in ov["expressions"] + ov["gestures"]:
    IDS.setdefault(it["key"], it["id"])
BY_ID = {it["id"]: it for it in ov["expressions"] + ov["gestures"]}


def lexicon_expr():
    rows = ["| 表情 | 何时用 | 切片位置 |", "|---|---|---|"]
    for e in ov["expressions"]:
        rows.append(f"| {e['id']} {e['name_zh']} (`{e['key']}`) | {e['when_zh']} | {e['cut_zh']} |")
    return "\n".join(rows)


def lexicon_gest():
    rows = ["| 手势 | 动作路径 | 幅度上限 | 风险 |", "|---|---|---|---|"]
    for g in ov["gestures"]:
        rows.append(f"| {g['id']} {g['name_zh']} (`{g['key']}`) | {g['path_zh']} | {g['limit_zh']} | {g['risk']} |")
    return "\n".join(rows)


def tag_ids(tags):
    return " + ".join(f"{IDS.get(g['g'], '')} `{g['g']}`".strip() for g in tags.get("gestures", [])) or "—"


def timeline(pid):
    """Timeline table of a plate as generated WITH the gesture overlay (patched text + patched expected tags)."""
    lib2 = pm.overlay_catalog_lib(lib, ov)
    p = lib2["plates"][pid]
    rows = ["| 时间 | 动作（ZH） | Action (EN) | 词表 / 标签 | 角色 |", "|---|---|---|---|---|"]
    for s in p["timeline"]:
        t = f"{pm._num(s['t'][0])}–{pm._num(s['t'][1])} s"
        if s["kind"] == "section":
            rows.append(f"| {t} | {s['zh']} | {s['en']} | {tag_ids(s['tags'])} | {', '.join(s['tags']['roles'])} |")
        else:
            mark = {"start": "起始回位", "home": "**回位 ✂**", "end": "**回位 ✂（尾帧≈首帧）**"}[s["kind"]]
            rows.append(f"| {t} | {s['zh']} | {s['en']} | {mark} | — |")
    return "\n".join(rows)


def intents():
    rows = ["| 意图 role | 标记 | 触发词 | 中景：表情 + 手势 | 近景替代 | 备注 |", "|---|---|---|---|---|---|"]
    for it in ov["intents"]:
        ex = " / ".join(f"{i} {BY_ID[i]['name_zh']}" for i in it["expressions"]) or "—"
        ge = " / ".join(f"{i} {BY_ID[i]['name_zh']}" for i in it["gestures"]) or "—"
        tag = f"`{it['role']}`"
        rows.append(f"| {tag} | {it['markup_zh']} | {it['triggers_zh']} | {ex} ＋ {ge} | {it['mcu_alt_zh']} | {it.get('note_zh', '')} |")
    return "\n".join(rows)


def scorecard():
    rows = ["| # | 检查（是 / 否） | Check (yes / no) |", "|---|---|---|"]
    rows += [f"| {it['id']} | {it['zh']} | {it['en']} |" for it in ov["scorecard"]]
    return "\n".join(rows)


values = {
    "EXPR_LEXICON": lexicon_expr(),
    "GESTURE_LEXICON": lexicon_gest(),
    "INTENT_TABLE": intents(),
    "TIMELINE_K04": timeline("K04"),
    "SCORECARD_TABLE": scorecard(),
    "mcu_rule.zh": ov["mcu_rule"]["zh"],
    "scorecard_rule.zh": ov["scorecard_rule"]["zh"],
}


def sub(m):
    k = m.group(1)
    if k not in values:
        sys.exit(f"unknown placeholder {k}")
    return values[k]


def render():
    out = re.sub(r"\{\{([A-Za-z0-9_.]+)\}\}", sub, tpl)
    assert "{{" not in out
    return out


if __name__ == "__main__":
    path = os.path.join(ROOT, "docs", "GESTURE_EXPRESSION.md")
    text = render()
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", path, len(text), "chars")
