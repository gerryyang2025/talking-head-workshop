"""Prompt library: compose plate prompts from blocks, verify frozen plates, derive spec shots, generate refresh plates, build docs."""
import json
import os
import random

from .vocab import VOCAB, ENERGY

SPEC_CAMERA = {
    ("mcu", "9:16", "center"): dict(face_box=[0.37, 0.17, 0.26, 0.19], face_h_px=360, safe=["upper_band", "lower_third"], scale_max=1.25),
    ("ms", "9:16", "center"): dict(face_box=[0.41, 0.15, 0.18, 0.12], face_h_px=230, safe=["upper_band", "lower_third"], scale_max=1.25),
    ("mcu", "16:9", "left"): dict(face_box=[0.25, 0.17, 0.13, 0.31], face_h_px=330, safe=["right_half", "lower_third", "upper_band"], scale_max=1.2),
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _num(x):
    x = float(x)
    return str(int(x)) if x.is_integer() else f"{x:g}"


def tl_line(sec, lang, shift=0.0):
    a, b = sec["t"][0] - shift, sec["t"][1] - shift
    return f"{_num(a)}–{_num(b)}s: {sec['en']}" if lang == "en" else f"{_num(a)}–{_num(b)} 秒：{sec['zh']}"


def compose(lib, pid, lang="en", part=None):
    """Full prompt text. part='A'/'B' splits a 60 s plate into two chained 30 s generations."""
    p = lib["plates"][pid]
    B = lib["blocks"]
    lock = B[p["lock"]][lang]
    secs = p["timeline"]
    shift = 0.0
    extra = []
    if part:
        lock = lock.replace("60-second", "30-second").replace("60 秒", "30 秒")
        if part == "A":
            secs = [s for s in secs if s["t"][1] <= 30]
        else:
            secs = [s for s in secs if s["t"][0] >= 30]
            shift = 30.0
            extra = [B["continue"][lang]]
    lines = [lock] + extra + [B["identity"][lang], B["setting"][lang], p["performance"][lang], "Timeline:" if lang == "en" else "时间线："]
    lines += [tl_line(s, lang, shift) for s in secs]
    lines.append(p["avoid"][lang])
    return "\n".join(lines)


def verify_frozen(lib):
    bad = []
    for key, txt in lib.get("frozen_check", {}).items():
        lang, pid = key.split(":")
        if compose(lib, pid, lang) != txt:
            bad.append(key)
    return bad


def spec_shots(lib, pid):
    p = lib["plates"][pid]
    pos = p.get("subject_pos", "center")
    cam = SPEC_CAMERA.get((p["framing"], p["aspect"], pos), SPEC_CAMERA[("mcu", "9:16", "center")])
    cuts = p["cut_points"]
    secs = [s for s in p["timeline"] if s["kind"] == "section"]
    windows = []
    if p.get("shots_override"):
        for o in p["shots_override"]:
            sec = next(s for s in secs if s["t"][0] < o["out"] and s["t"][1] > o["in"])
            windows.append((o["id"], o["in"], o["out"], sec, o))
    else:
        for k, sec in enumerate(secs):
            a = max(c for c in cuts if c <= sec["t"][0])
            b = min(c for c in cuts if c >= sec["t"][1])
            windows.append((f"{pid}_s{k + 1}", a, b, sec, {}))
    out = []
    for sid, a, b, sec, o in windows:
        tg = sec["tags"]
        off = sec["t"][0] - a
        talking = tg.get("mouth") == "talking"
        out.append({
            "id": sid, "plate": pid, "src": {"in": a, "out": b},
            "home_in": not o.get("first_only", False), "home_out": True,
            "camera": {"framing": p["framing"], "aspect": p["aspect"], "angle": "front", "subject_pos": pos, "face_box": cam["face_box"], "face_h_px": cam["face_h_px"]},
            "performance": {"energy": tg["energy"], "emotion": tg["emotion"],
                            "gestures": [dict(g, t=round(g["t"] + off, 2)) for g in tg.get("gestures", [])],
                            "gaze": "lens", "mouth": tg["mouth"], "hands": tg.get("hands", "out_of_frame"),
                            "head_motion": "small", "speaking": talking},
            "edit": {"roles": tg["roles"], "transitions_in": ["first_only"] if o.get("first_only") else ["cut", "zoomcut", "broll_fade", "mgwipe"],
                     "layouts": ["full", "split", "pip"], "position": "first_only" if o.get("first_only") else "any",
                     "scale_max": cam["scale_max"], "reversible": tg.get("reversible", "no"), "mirror_ok": False,
                     "cut_points": [0.0], "keep_out": [[round(x + off, 2), round(y + off, 2)] for x, y in tg.get("keep_out", [])],
                     **({"speech_offset": o["speech_offset"]} if o.get("speech_offset") else {})},
            "mg": {"safe_zones": cam["safe"]},
            "lipsync": {"ready": talking, "jaw": "mid"},
            "quality": {"qc": 4, "defects": []},
            "usage": {"times_used": 0, "last_used": None},
            "provenance": "spec",
            "notes": f"{p['title_zh']} · {sec['zh']}",
        })
    return out


def plate_record(lib, pid):
    p = lib["plates"][pid]
    size = [1080, 1920] if p["aspect"] == "9:16" else [1920, 1080]
    return {"id": pid, "file": None, "name": p["file"], "title": p["title_zh"], "framing": p["framing"], "aspect": p["aspect"], "size": size, "fps": 25,
            "duration": p["duration"], "source_type": "generated", "prompt_ref": f"prompts/library.json#plates.{pid}", "status": "spec — not generated yet",
            "home_pose_times": p["cut_points"]}


def refresh(lib, n=4, seed=1, framing="mcu", start_index=1):
    """Compose n new 30 s plates from the micro-action menu (same locks → drop-in compatible)."""
    rng = random.Random(seed)
    pool = [m for m in lib["micro_actions"] if m["framing"] == framing]
    out = {}
    base = "K03" if framing == "mcu" else "K02"
    used_sets = set()
    for k in range(n):
        for _ in range(200):
            pick = rng.sample(pool, 4)
            key = tuple(sorted(m["id"] for m in pick))
            if key not in used_sets and len({m["from"] for m in pick}) >= 3:
                used_sets.add(key)
                break
        pid = f"R{start_index + k:02d}"
        tl = [{"t": [0, 1], "en": "She holds the home pose, then begins speaking.", "zh": "保持回位姿势，然后开始说话。", "kind": "start"}]
        for j, m in enumerate(pick):
            a = 1 + 7 * j
            tl.append({"t": [a, a + 6], "en": m["en"], "zh": m["zh"], "kind": "section", "tags": m["tags"], "from": m["id"]})
            if j < 3:
                tl.append({"t": [a + 6, a + 7], "en": "She returns to the home pose and holds it still for one second.", "zh": "回到回位姿势，静止保持一秒。", "kind": "home"})
        tl.append({"t": [28, 30], "en": "She finishes her sentence, returns to the home pose and holds it still until the end, the final frame matching the first frame as closely as possible.",
                   "zh": "说完这句话，回到回位姿势，静止保持到结束，最后一帧尽量与第一帧一致。", "kind": "end"})
        bp = lib["plates"][base]
        out[pid] = {"title_zh": f"月度换新底板 {pid}", "title_en": f"Monthly refresh plate {pid}", "file": f"liz01_o1_{framing}_916_refresh-{pid.lower()}_mid_30s_v01.mov",
                    "framing": framing, "aspect": "9:16", "duration": 30, "lock": bp["lock"], "first_frame": bp["first_frame"], "status": "generated by `istream prompts refresh`",
                    "performance": lib["plates"]["K03" if framing == "mcu" else "K02"]["performance"], "avoid": bp["avoid"], "negative": bp["negative"],
                    "cut_points": [0.5, 7.5, 14.5, 21.5, 29.0], "timeline": tl}
    return out


# ----------------------------------------------------------------------------- docs
def vlm_prompt():
    enums = {f: list(VOCAB[f]) for f in ("emotion", "gesture", "gaze", "mouth", "hands", "head_motion", "role", "reversible", "jaw")}
    return (
        "You are tagging one shot from a digital-human talking-head plate for an automatic editor.\n"
        "Input: 3–5 frames from the shot (start, middle, end, plus any gesture peak), the shot duration, and measured metrics "
        "(face box, motion level, speech fraction). Look only at what is visible; do not guess intentions.\n"
        "Return ONE JSON object, no prose, with exactly these keys:\n"
        '{"emotion": <one of emotion>, "gestures": [{"g": <one of gesture>, "t": <seconds from shot start>}], "gaze": <gaze>, '
        '"mouth": <mouth>, "hands": <hands>, "head_motion": <head_motion>, "roles": [<1–3 of role, best first>], '
        '"reversible": <reversible>, "jaw": <jaw>, "energy": <1–5>, "defects": [<free text, e.g. "second face: glass reflection left half">], "notes": <≤20 words>}\n'
        "Rules: hands anywhere near the mouth or chin → hands=\"near_face\". A smile showing many teeth → mouth=\"open_smile\". "
        "reversible=\"good\" only if the motion is symmetric (nods, stillness) and nothing (blink, gesture) would look backwards. "
        "roles: open = the host arrives / greets; pause/listen = mouth closed; emphasis = a clear peak (lean-in, brow raise, firm nod).\n"
        "Allowed values:\n" + "\n".join(f"- {k}: {', '.join(v)}" for k, v in enums.items()) + f"\n- energy: {', '.join(str(e) for e in ENERGY)}"
    )


def build_md(lib):
    L = []
    w = L.append
    w("# 高级无限流 · 底板提示词库 · Prompt Library")
    w("")
    w("> 本文件由 `python -m istream prompts build` 从 `prompts/library.json` 生成，请改 JSON，不要改这里。")
    w("> K01–K03 的默认形象提示词取自 [plates-source.md](plates-source.md)（原稿名 `dh-plates-final-koubo.md`），可用 `python -m istream prompts verify` 校验。")
    w("> 提示词校验只检查文本。生成实际母片后，按[制作 Skill](../SKILL.md)复核人物、动作与切点。")
    w("")
    w("## 0. 怎么用")
    w("")
    w("1. **拼装公式：** `锁定行(画幅/景别/时长) + 身份 + 场景与光线 + 表演 + 时间线 + 避免`。身份和场景两块是全库共享的，**一字不改**；需要更换形象时用 `python -m istream identity set --photo ./me.jpg` 同步身份块和首帧提示词。")
    w("2. **首帧图：** 先用 IMG-A（近景）/ IMG-B（中景）/ IMG-A169（横屏左三分之一）生成首帧图，生成底板时设为首帧；支持尾帧的工具，尾帧也用同一张图，保证所有底板首尾一致、可以互拼。")
    w("3. **30 秒底板：** 直接粘贴完整提示词。每条抽 4–5 次，挑最好的一条入库。")
    w("4. **60 秒底板（L01 / L02）：** 工具支持 60 秒就用完整版；不支持就用「接力 A / 接力 B」两段各 30 秒生成：B 段用 A 段尾帧作首帧（或用延长功能），开头已带“从上一段的回位姿势无缝接续”。接力点在 28–31 秒的回位静止段里，切点 29.5 秒。")
    w("5. **开场底板（O01）：** 4 个开场镜头都从“准备动作”的中间切入，所以第一帧主播就已经“在场”（低头看提纲 / 刚转回来 / 正在前倾 / 静场吸气），而不是突然出现。这 4 段只能做全片第一个镜头（O01_s4 例外，也可做章节开场）。")
    w("6. **生成设置（沿用定稿）：** 同一模型和版本；1080p 起，能更高就更高；统一帧率（优先 25fps）；每次挂同一张身份参考图；模型自带的音频一律静音；单次上限不足 30 秒时在 14–15 秒的回位处拆两段。")
    w("")
    w("## 1. 首帧图")
    for k, v in lib["first_frames"].items():
        w("")
        w(f"### {k}")
        w("")
        w("**EN**")
        w("")
        w("```text\n" + v["en"] + "\n```")
        w("")
        w("**中文**")
        w("")
        w("```text\n" + v["zh"] + "\n```")
    groups = [("2. 30 秒底板（定稿 + 横屏孪生）", ["K01", "K02", "K03", "K01H"]), ("3. 60 秒长底板", ["L01", "L02"]), ("4. 开场入镜底板", ["O01"])]
    for title, ids in groups:
        w("")
        w(f"## {title}")
        for pid in ids:
            p = lib["plates"][pid]
            w("")
            w(f"### {pid} · {p['title_zh']} · {p['title_en']}")
            w("")
            w(f"- 文件名：`{p['file']}` ｜ {p['framing'].upper()} · {p['aspect']} · {p['duration']} 秒 · 首帧图 {p['first_frame']} ｜ 状态：{p['status']}")
            w(f"- 切点（回位静止中点）：{' / '.join(_num(c) + 's' for c in p['cut_points'])}")
            w("")
            w("| 时间 | 段 | 动作 | 角色 roles | 能量 | 情绪 | 嘴 | 倒放 |")
            w("|---|---|---|---|---|---|---|---|")
            k = 0
            for s in p["timeline"]:
                if s["kind"] in ("section",):
                    k += 1
                    tg = s["tags"]
                    w(f"| {_num(s['t'][0])}–{_num(s['t'][1])}s | s{k} | {s['zh']} | {', '.join(tg['roles'])} | {tg['energy']} | {tg['emotion']} | {tg['mouth']} | {tg.get('reversible', 'no')} |")
                elif s["kind"] == "setup":
                    w(f"| {_num(s['t'][0])}–{_num(s['t'][1])}s | 准备 | {s['zh']}（不单独使用，作为开场镜头的入点） | — | — | — | closed | — |")
            for lang, name in (("en", "EN Master Prompt"), ("zh", "中文 Master Prompt")):
                w("")
                w(f"**{name}**")
                w("")
                w("```text\n" + compose(lib, pid, lang) + "\n```")
            if p["duration"] == 60:
                for part in ("A", "B"):
                    for lang, name in (("en", "EN"), ("zh", "中文")):
                        w("")
                        w(f"**接力 {part}（30 秒）· {name}**")
                        w("")
                        w("```text\n" + compose(lib, pid, lang, part) + "\n```")
            w("")
            w(f"**负面提示词（支持负面框的工具）：** `Negative: {p['negative']}`")
    w("")
    w("## 5. 月度换新：用菜单组合新底板")
    w("")
    w("“无限”不是一套底板永远用下去，而是**锁定段不变、动作段持续换新**。下面的微动作菜单来自已有底板加上 5 个新动作；`python -m istream prompts refresh --n 4 --framing mcu --seed 202611` 会从菜单里抽出没用过的组合，生成 R01… 新底板（锁定段相同，可直接混进旧库），同时生成它们的预期标签。")
    w("")
    w("| id | 景别 | 动作 | roles | 能量 | 情绪 |")
    w("|---|---|---|---|---|---|")
    for m in lib["micro_actions"]:
        w(f"| {m['id']} | {m['framing']} | {m['zh']} | {', '.join(m['tags']['roles'])} | {m['tags']['energy']} | {m['tags']['emotion']} |")
    ex = refresh(lib, n=1, seed=202611, framing="mcu")
    lib2 = dict(lib, plates=dict(lib["plates"], **ex))
    w("")
    w("**示例：R01（seed 202611 抽出的组合）· EN**")
    w("")
    w("```text\n" + compose(lib2, "R01", "en") + "\n```")
    w("")
    w("## 6. VLM 打标提示词（入库第 2 步）")
    w("")
    w("切片工具只能测出“机器测得出来的”标签（切点、人脸、运动、静音、缺陷）。情绪、手势名称、角色用下面这段提示词交给多模态模型（每个镜头喂 3–5 帧 + 测量值），返回 JSON 直接合并进 `shots.json`，再人工抽查 20%。")
    w("")
    w("```text\n" + vlm_prompt() + "\n```")
    return "\n".join(L) + "\n"


def build_txt(lib):
    out = ["# 高级无限流 · prompts only (generated from prompts/library.json)", ""]
    for lang in ("en", "zh"):
        out.append(f"==================== {'ENGLISH' if lang == 'en' else '中文'} ====================")
        for k, v in lib["first_frames"].items():
            out += [f"--- {k} ---", v[lang], ""]
        for pid, p in lib["plates"].items():
            out += [f"--- {pid} · {p['file']} ---", compose(lib, pid, lang), ""]
            if p["duration"] == 60:
                for part in ("A", "B"):
                    out += [f"--- {pid} 接力 {part} ---", compose(lib, pid, lang, part), ""]
    out += ["==================== VLM tagging prompt ====================", vlm_prompt(), ""]
    return "\n".join(out)


# ----------------------------------------------------------------------------- overlays (copy-time patches; never touch library.json)
OVERLAY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "overlays")


def load_overlay(name="human_premium", path=None):
    """Load an overlay (e.g. prompts/overlays/human_premium.json). Returns None if missing."""
    p = path or os.path.join(OVERLAY_DIR, f"{name}.json")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_overlays(names):
    """'human_premium,gesture_expression' (or a list) → [overlay, ...] in application order. Raises KeyError on a missing one."""
    if isinstance(names, str):
        names = [n.strip() for n in names.split(",") if n.strip()]
    out = []
    for n in names:
        ov = load_overlay(n)
        if ov is None:
            raise KeyError(n)
        out.append(ov)
    return out


def _as_list(ov):
    if ov is None:
        return [load_overlay()]
    return list(ov) if isinstance(ov, (list, tuple)) else [ov]


def _in_scope(entry, pid):
    """Entries with a "plates" list only apply to those plates (gesture_expression); others apply everywhere."""
    pl = entry.get("plates")
    return not pl or pid in pl


def with_overlay_plates(lib, ov=None):
    """Library copy with overlay-defined plates (e.g. K04/K05 from gesture_expression) added in memory.
    avoid/negative may be borrowed from a library plate via avoid_from/negative_from. Library plates are never replaced."""
    extra = {}
    for o in _as_list(ov):
        for pid, p in (o or {}).get("plates", {}).items():
            if pid in lib["plates"]:
                continue
            q = dict(p)
            q.setdefault("avoid", lib["plates"][q.get("avoid_from", "K01")]["avoid"])
            q.setdefault("negative", lib["plates"][q.get("negative_from", "K01")]["negative"])
            extra[pid] = q
    return dict(lib, plates=dict(lib["plates"], **extra)) if extra else lib


def overlay_catalog_lib(lib, ov=None):
    """Library copy for `catalog build-spec --overlay …`: overlay plates added, plate-scoped replacements applied to the
    section texts (catalog notes) and tag_patches merged into the expected tags (roles/gestures the patch adds)."""
    ovs = _as_list(ov)
    lib2 = with_overlay_plates(lib, ovs)
    plates = dict(lib2["plates"])
    for pid in list(plates):
        p = json.loads(json.dumps(plates[pid]))
        touched = False
        for o in ovs:
            patches = o.get("tag_patches", {}).get(pid, {})
            k = 0
            for sec in p["timeline"]:
                for lang in ("en", "zh"):
                    for r in o.get("replace", []):
                        if r.get("plates") and pid in r["plates"] and r[lang][0] in sec[lang]:
                            sec[lang] = sec[lang].replace(*r[lang])
                            touched = True
                if sec["kind"] != "section":
                    continue
                k += 1
                add = patches.get(str(k))
                if add:
                    tg = sec["tags"]
                    tg["roles"] = tg["roles"] + [x for x in add.get("roles", []) if x not in tg["roles"]]
                    tg["gestures"] = sorted(tg.get("gestures", []) + add.get("gestures", []), key=lambda g: g["t"])
                    touched = True
        if touched:
            plates[pid] = p
    return dict(lib2, plates=plates)


def overlay_plate_ids(ov=None):
    return [pid for o in _as_list(ov) for pid in (o or {}).get("plates", {})]


def _append_to_line(lines, prefix, extra, lang):
    for i, l in enumerate(lines):
        if l.startswith(prefix):
            sep = " " if lang == "en" else ""
            lines[i] = l + sep + extra
            return 1
    return 0


def apply_overlay_text(text, ov, lang, kind="plate", style=False, compact=False, pid=None, framing=None):
    """Apply an overlay to an already composed prompt. kind: 'plate' | 'first_frame'. Returns (text, n_applied).
    compact=True uses the short setting/performance patches (for tools with ~3k-character prompt limits).
    pid scopes plate-specific replacements; framing ('mcu' | 'ms') picks the *_by_framing patches."""
    n = 0
    if kind == "plate":
        for r in ov.get("replace", []):
            if not _in_scope(r, pid):
                continue
            old, new = r[lang]
            if old in text:
                n += text.count(old)
                text = text.replace(old, new)
        lines = text.split("\n")
        set_prefix, perf_prefix, avoid_prefix = ("Setting and light:", "Performance:", "Avoid:") if lang == "en" else ("场景与光线：", "表演：", "避免：")
        sk, pk = ("setting_compact", "performance_compact") if compact else ("setting_append", "performance_append")
        if sk in ov:
            n += _append_to_line(lines, set_prefix, ov[sk][lang], lang)
        if pk in ov:
            n += _append_to_line(lines, perf_prefix, ov[pk][lang], lang)
        fk = "performance_compact_by_framing" if compact else "performance_append_by_framing"
        if framing and framing in ov.get(fk, {}):
            n += _append_to_line(lines, perf_prefix, ov[fk][framing][lang], lang)
        if style and "style_line" in ov:
            for i, l in enumerate(lines):
                if l.startswith(set_prefix):
                    lines.insert(i + 1, ov["style_line"][lang])
                    n += 1
                    break
        adds = []
        if "avoid_append" in ov:
            adds.append(ov["avoid_append"][lang])
        if framing and framing in ov.get("avoid_append_by_framing", {}):
            adds.append(ov["avoid_append_by_framing"][framing][lang])
        if adds:
            for i, l in enumerate(lines):
                if l.startswith(avoid_prefix):
                    end = "." if lang == "en" else "。"
                    sep = ", " if lang == "en" else "，"
                    body = l[:-1] if l.endswith(end) else l
                    lines[i] = body + sep + sep.join(adds) + end
                    n += 1
                    break
        return "\n".join(lines), n
    # first-frame image prompt: insert before the closing "No text, no logo." / "无文字，无 logo。"
    add = ov.get("first_frame_append", {}).get(lang)
    if not add:
        return text, 0
    tail = "No text, no logo." if lang == "en" else "无文字，无 logo。"
    if text.endswith(tail):
        return text[: -len(tail)] + add + (" " if lang == "en" else "") + tail, 1
    return text + (" " if lang == "en" else "") + add, 1


def compose_overlay(lib, pid, lang="en", ov=None, part=None, style=False, compact=False):
    """compose() + overlay(s), applied in order. ov: one overlay, a list (stacking), or None (human_premium).
    The library and the frozen K01–K03 text are untouched; overlay-only plates (K04/K05) are composed from a copy."""
    ovs = _as_list(ov)
    lib2 = with_overlay_plates(lib, ovs)
    text = compose(lib2, pid, lang, part)
    framing = lib2["plates"][pid]["framing"]
    for o in ovs:
        text = apply_overlay_text(text, o, lang, "plate", style, compact, pid=pid, framing=framing)[0]
    return text


def first_frame_overlay(lib, key, lang="en", ov=None):
    text = lib["first_frames"][key][lang]
    for o in _as_list(ov):
        text = apply_overlay_text(text, o, lang, "first_frame")[0]
    return text


def negative_overlay(lib, pid, ov=None, short=False, lang="en"):
    """Plate negative + overlay extras (deduplicated, stacked overlays in order). negative_extra_ms only joins on MS plates
    (hand tells are noise on close-ups). Plate-scoped negative_drop entries remove base terms that would fight a patch
    (e.g. 'looking away' vs the K01 thinking glance). lang='zh' returns the Chinese extras only (for CN negative boxes)."""
    ovs = _as_list(ov)
    lib2 = with_overlay_plates(lib, ovs)
    framing = lib2["plates"][pid]["framing"]
    key = "short_" + lang if short else lang
    ex = []
    for o in ovs:
        for x in o["negative_extra"][key] + (o.get("negative_extra_ms", {}).get(key, []) if framing == "ms" else []):
            if x.lower() not in {y.lower() for y in ex}:
                ex.append(x)
    if lang == "zh":
        return "，".join(ex)
    drop = {d.lower() for o in ovs for e in o.get("negative_drop", []) if _in_scope(e, pid) for d in e["drop"]}
    base = [x.strip() for x in lib2["plates"][pid]["negative"].split(",") if x.strip().lower() not in drop]
    seen = {x.lower() for x in base}
    return ", ".join(base + [x for x in ex if x.lower() not in seen])
