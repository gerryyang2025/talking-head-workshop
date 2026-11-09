"""User photo → digital-human identity → GENERATE_PACK (meta-plate prompts).

Flow: upload photo → `istream identity set` → generate unobstructed plates → slice → assemble.
Does NOT auto-analyse the face (no VLM). Appearance locks come from --describe / --outfit / --name only.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from . import prompts as pm

STARTER_PLATES = ("K01", "K02", "O01")
OPTIONAL_PLATES = ("K01H", "K03", "L01", "L02")

# Markers used to splice Subject / 人物 into first-frame prompts without rewriting framing text.
_SUBJECT_EN_PREFIX = "Subject: "
_SUBJECT_ZH_PREFIX = "人物："
_AFTER_SUBJECT_EN = ". She faces"
_AFTER_SUBJECT_ZH = "。她正对"


def _now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def default_path(root: str) -> str:
    return os.path.join(root, "prompts", "identity_default.json")


def state_path(root: str) -> str:
    return os.path.join(root, "prompts", "identity", "current.json")


def load_default(root: str) -> dict:
    path = default_path(root)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"missing {path} — reinstall the skill package or restore prompts/identity_default.json"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def ensure_default_backup(root: str, lib: dict | None = None) -> str:
    """Write identity_default.json once from the current library if missing."""
    path = default_path(root)
    if os.path.isfile(path):
        return path
    if lib is None:
        lib = pm.load(os.path.join(root, "prompts", "library.json"))
    data = {
        "note": "Auto-saved default persona for `istream identity restore`.",
        "blocks_identity": lib["blocks"]["identity"],
        "first_frames": lib["first_frames"],
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return path


def build_identity_text(
    *,
    name: str | None = None,
    describe: str | None = None,
    outfit: str | None = None,
) -> dict:
    """Compose EN+ZH identity blocks. Never invent gender/age — only use --describe/--name/--outfit."""
    parts_en = [
        "exactly the same person as in the attached reference image "
        "(same face, hair, skin tone, age appearance)"
    ]
    parts_zh = ["与所附参考图中为同一人（脸型、发型、肤色、年龄感一致）"]
    if name:
        parts_en.append(f"reference name: {name}")
        parts_zh.append(f"称呼/姓名：{name}")
    if describe:
        parts_en.append(describe.strip())
        parts_zh.append(describe.strip())
    if outfit:
        parts_en.append(f"wearing {outfit.strip()}")
        parts_zh.append(f"穿着：{outfit.strip()}")
    else:
        parts_en.append("clothing matches the reference image unless an outfit lock is given")
        parts_zh.append("服装与参考图一致（除非另行指定服装锁定）")
    parts_en.append("No jewelry, no glasses unless visible in the reference")
    parts_zh.append("不戴首饰；除非参考图中可见，否则不戴眼镜")
    en_body = parts_en[0]
    if len(parts_en) > 1:
        en_body += ". " + ". ".join(parts_en[1:])
    zh_body = parts_zh[0]
    if len(parts_zh) > 1:
        zh_body += "。" + "。".join(parts_zh[1:])
    return {
        "en": f"Identity: {en_body}.",
        "zh": f"人物：{zh_body}。",
    }


def _identity_body(block: dict) -> tuple[str, str]:
    en = block["en"]
    zh = block["zh"]
    if en.startswith("Identity: "):
        en = en[len("Identity: ") :]
    if en.endswith("."):
        en = en[:-1]
    if zh.startswith("人物："):
        zh = zh[len("人物：") :]
    if zh.endswith("。"):
        zh = zh[:-1]
    return en, zh


def apply_identity_to_library(lib: dict, identity: dict) -> None:
    """Update blocks.identity and splice Subject/人物 into first_frames."""
    lib["blocks"]["identity"] = {"en": identity["en"], "zh": identity["zh"]}
    en_body, zh_body = _identity_body(identity)
    for key, ff in lib["first_frames"].items():
        lib["first_frames"][key] = {
            "en": _splice_subject_en(ff["en"], en_body),
            "zh": _splice_subject_zh(ff["zh"], zh_body),
        }


def _splice_subject_en(text: str, body: str) -> str:
    i = text.find(_SUBJECT_EN_PREFIX)
    j = text.find(_AFTER_SUBJECT_EN)
    if i < 0 or j < 0 or j <= i:
        # fallback: leave framing, append note
        return text
    return text[: i + len(_SUBJECT_EN_PREFIX)] + body + text[j:]


def _splice_subject_zh(text: str, body: str) -> str:
    i = text.find(_SUBJECT_ZH_PREFIX)
    j = text.find(_AFTER_SUBJECT_ZH)
    if i < 0 or j < 0 or j <= i:
        return text
    return text[: i + len(_SUBJECT_ZH_PREFIX)] + body + text[j:]


def restore_default(lib: dict, root: str) -> None:
    d = load_default(root)
    lib["blocks"]["identity"] = dict(d["blocks_identity"])
    lib["first_frames"] = {k: dict(v) for k, v in d["first_frames"].items()}


def copy_photo(photo: str, dest_dir: str, slug: str) -> str:
    os.makedirs(dest_dir, exist_ok=True)
    ext = os.path.splitext(photo)[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    dest = os.path.join(dest_dir, f"ref{ext}")
    shutil.copy2(photo, dest)
    # also keep a stable name ref.jpg when possible (jpeg)
    if ext in (".jpg", ".jpeg"):
        stable = os.path.join(dest_dir, "ref.jpg")
        if os.path.abspath(dest) != os.path.abspath(stable):
            shutil.copy2(dest, stable)
            dest = stable
    return dest


def write_identity_json(path: str, meta: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")


def build_generate_pack_md(lib: dict, meta: dict) -> str:
    """Operator-facing one-stop pack: generate unobstructed meta plates first."""
    L = []
    w = L.append
    slug = meta.get("slug", "user")
    photo = meta.get("photo_rel") or meta.get("photo") or "(attach your reference photo)"
    name = meta.get("name") or slug

    w("# 生成包 · GENERATE_PACK — 无遮挡元视频底板")
    w("")
    w(f"> 当前模板：`{slug}`。在仓库根目录运行 `python3 -m istream identity set --photo ./me.jpg` 可生成自己的版本。")
    w("")
    w("## 生成母片")
    w("")
    w(f"- 人物：{name}。参考照：{photo}。")
    w("- 为同一批母片使用相同参考照、模型与版本。先生成首帧，再生成近景、中景或开场动作。")
    w("- 建议使用 1080p 或更高分辨率、25 fps。保留嘴部清晰、手势避开脸、切点处姿势稳定的片段。剪辑时沿用最终配音。")
    w("")
    w("## 负面提示词 / Negative (all starter plates)")
    w("")
    neg = lib["plates"]["K01"]["negative"]
    w("```text")
    w(f"Negative: {neg}")
    w("```")
    w("")
    w("## 无遮挡提醒 / No-occlusion (from Avoid lines)")
    w("")
    w("Avoid 段已写明：hands touching or covering the face or mouth · 手不碰脸不挡嘴 · 无道具挡嘴 · 干净背景。")
    w("生成时若模型爱把手抬起来，加重负面里的 `hands touching face, hand covering mouth`，或在提示词 Timeline 里强调 hands stay below frame。")
    w("")
    w("## 当前身份块 / Current identity block")
    w("")
    w("**EN**")
    w("")
    w("```text")
    w(lib["blocks"]["identity"]["en"])
    w("```")
    w("")
    w("**中文**")
    w("")
    w("```text")
    w(lib["blocks"]["identity"]["zh"])
    w("```")
    w("")
    w("> 外貌细节来自你提供的 `--describe` / `--outfit` / `--name`，**不会**自动读图分析脸。")
    w("> Appearance locks come only from flags you pass — there is no automatic face analysis.")
    w("")
    w("## 首帧图提示词 / First-frame prompts")
    w("")
    for k, v in lib["first_frames"].items():
        w(f"### {k}")
        w("")
        w("**EN**")
        w("")
        w("```text")
        w(v["en"])
        w("```")
        w("")
        w("**中文**")
        w("")
        w("```text")
        w(v["zh"])
        w("```")
        w("")
    w("## 起步套装提示词 / Starter plate prompts（先生成这三条）")
    w("")
    w("推荐 Phase 0 / 标准档先跑 **K01 + K02 + O01**（近景主力 · 中景手势 · 开场入镜）。")
    w("")
    for pid in STARTER_PLATES:
        p = lib["plates"][pid]
        w(f"### {pid} · {p['title_zh']} · {p['title_en']}")
        w("")
        w(f"- 文件名：`{p['file']}` ｜ {p['framing'].upper()} · {p['aspect']} · {p['duration']}s · 首帧 {p['first_frame']}")
        w(f"- 切点：{' / '.join(str(c) + 's' for c in p['cut_points'])}")
        w("")
        w("**EN Master Prompt**")
        w("")
        w("```text")
        w(pm.compose(lib, pid, "en"))
        w("```")
        w("")
        w("**中文 Master Prompt**")
        w("")
        w("```text")
        w(pm.compose(lib, pid, "zh"))
        w("```")
        w("")
        w(f"**Avoid EN：** {p['avoid']['en']}")
        w("")
        w(f"**避免（中文）：** {p['avoid']['zh']}")
        w("")
    w("## 更多底板 / More plates")
    w("")
    w("完整中英提示词（含 L01/L02 60s 接力、K01H 横屏孪生、K03 近景变体）见：")
    w("")
    w("- `prompts/PROMPT_LIBRARY.md`")
    w("- `prompts/prompts-only.txt`（纯提示词，方便复制）")
    w("")
    for pid in OPTIONAL_PLATES:
        p = lib["plates"][pid]
        w(f"- **{pid}** · {p['title_zh']} · {p['framing'].upper()} · {p['aspect']} · {p['duration']}s · 首帧 {p['first_frame']}")
    w("")
    w("## 生成之后 / After generation")
    w("")
    w("```bash")
    w("# 1) 切片（无遮挡元视频 → 可复用镜头）")
    w("python3 -m istream slice path/to/K01.mp4 --id K01 --out drafts/K01.json --sheet drafts/K01_sheet.jpg")
    w("python3 -m istream slice path/to/K02.mp4 --id K02 --out drafts/K02.json --sheet drafts/K02_sheet.jpg")
    w("python3 -m istream slice path/to/O01.mp4 --id O01 --out drafts/O01.json --sheet drafts/O01_sheet.jpg")
    w("# 2) 人工/VLM 复核 → catalog merge-review")
    w("# 3) 写稿 → plan → edit → lipsync → render（见 SKILL.md）")
    w("```")
    w("")
    w("## 恢复默认形象 / Restore default persona")
    w("")
    w("换回包内定稿东亚女性形象（并让 `prompts verify` 再次对上 frozen_check）：")
    w("")
    w("```bash")
    w("python3 -m istream identity restore")
    w("```")
    w("")
    w("换过身份后，`istream prompts verify` 会报 MISMATCH，这是预期行为；只有默认形象才与 K01–K03 定稿逐字一致。")
    w("")
    L += human_premium_section()
    L += gesture_expression_section(lib)
    return "\n".join(L) + "\n"


def human_premium_section(ov: dict | None = None) -> list:
    """`## 真人感 / 去 AI 味（P0）` — rendered from prompts/overlays/human_premium.json so it survives every pack rebuild."""
    ov = ov or pm.load_overlay("human_premium")
    if not ov:
        return []
    L = []
    w = L.append
    w("## 真人感 / 去 AI 味（P0）")
    w("")
    w(f"> 状态：{ov.get('status_zh', ov['status'])}")
    w("> 完整原理、参考照规则、选片与后期：`docs/HUMAN_PREMIUM.md`。这里只放 P0 补丁、负面补充和入库评分卡。")
    w("> 叠加层只在复制时生效，**不改** `library.json`，所以 K01–K03 定稿的逐字校验（`prompts verify`）不受影响。")
    w("")
    w("**一键拿到已叠加的完整提示词 / Get the patched prompts:**")
    w("")
    w("```bash")
    w("python3 -m istream prompts overlay --plate K01 --lang both --negative           # 完整版")
    w("python3 -m istream prompts overlay --plate K02 --lang en --compact --negative   # 提示词字数受限的工具")
    w("python3 -m istream prompts overlay --first-frame IMG-A --lang both               # 首帧图")
    w("```")
    w("")
    w("### 1) 句子替换 / Line swaps（叠加时自动完成）")
    w("")
    w("| 原句 | 改为 | 为什么 |")
    w("|---|---|---|")
    for r in ov["replace"]:
        w(f"| {r['zh'][0]} · *{r['en'][0]}* | {r['zh'][1]} · *{r['en'][1]}* | {r.get('why_zh', r['why'])} |")
    w("")
    for key, title in (("setting_append", "2) 场景与光线补丁 · Setting patch（接在 Setting / 场景与光线 句末）"),
                       ("performance_append", "3) 表演微行为补丁 · Performance patch（接在 Performance / 表演 句末）"),
                       ("first_frame_append", "4) 首帧图补丁 · First-frame patch（放在 “No text, no logo.” 之前）"),
                       ("style_line", "5) 可选气质句 · Optional style line（`--style`，单独成行放在场景之后）")):
        w(f"### {title}")
        w("")
        w("```text")
        w(ov[key]["en"])
        w("```")
        w("")
        w("```text")
        w(ov[key]["zh"])
        w("```")
        w("")
    w("### 6) 负面补充 / Negative extras（追加到每条底板的负面框）")
    w("")
    w("```text")
    w(", ".join(ov["negative_extra"]["en"]))
    w("```")
    w("")
    w("```text")
    w("，".join(ov["negative_extra"]["zh"]))
    w("```")
    w("")
    w("负面框字数受限时只用短版 / short list: `" + ", ".join(ov["negative_extra"]["short_en"]) + "`")
    w("")
    w("### 7) 入库评分卡 / Take scorecard（每条底板抽 4–5 次后逐条打勾）")
    w("")
    w("| # | 检查（是 / 否） | Check (yes / no) |")
    w("|---|---|---|")
    for it in ov["scorecard"]:
        w(f"| {it['id']} | {it['zh']} | {it['en']} |")
    w("")
    w(f"**规则：** {ov['scorecard_rule']['zh']}")
    w(f"**Rule:** {ov['scorecard_rule']['en']}")
    w("")
    return L


def gesture_expression_section(lib: dict, ov: dict | None = None) -> list:
    """`## 手势与表情（P0）` — rendered from prompts/overlays/gesture_expression.json (survives every pack rebuild).
    K04/K05 are composed from the current lib, so they carry whatever identity the pack was built for."""
    ov = ov or pm.load_overlay("gesture_expression")
    if not ov:
        return []
    L = []
    w = L.append
    w("## 手势与表情（P0）")
    w("")
    w(f"> 状态：{ov.get('status_zh', ov['status'])}")
    w("> 词表、诊断、例时间线和脚本映射见 `docs/GESTURE_EXPRESSION.md`；这里只放 P0 补丁、新底板 K04 / K05、负面补充和评分卡。")
    w("> 硬规则不变：嘴永远不被挡、手不碰脸、切点在回位、头部 ±20°、无首饰 / 眼镜 / logo、机位锁死；手势像访谈主持人，不是短视频舞蹈或舞台表演。")
    w("> 同样是复制时叠加，**不改** `library.json`，`prompts verify` 照常通过。")
    w("")
    w("**一键拿到已叠加的完整提示词 / Get the patched prompts:**")
    w("")
    w("```bash")
    w("python3 -m istream prompts overlay --plate K02 --lang both --negative --gesture            # 真人感 + 手势表情（叠加）")
    w("python3 -m istream prompts overlay --overlay gesture_expression --plate K02 --negative     # 只叠手势表情")
    w("python3 -m istream prompts overlay --plate K04 --lang zh --negative --gesture              # 新：中景手势密集底板")
    w("python3 -m istream prompts overlay --plate K05 --lang en --compact --negative --gesture    # 新：近景表情密集底板（字数受限）")
    w("python3 -m istream catalog build-spec --overlay gesture_expression --out catalog/gesture  # 预期标签目录（含 K04 / K05）")
    w("```")
    w("")
    w("### 1) 近景规则 / MCU rule")
    w("")
    w(f"- {ov['mcu_rule']['zh']}")
    w(f"- {ov['mcu_rule']['en']}")
    w("")
    w("### 2) 表情词表 / Expression lexicon（近景、中景都可用）")
    w("")
    w("| # | 表情 | 标签 | 什么时候用 | 表演提示（EN） |")
    w("|---|---|---|---|---|")
    for e in ov["expressions"]:
        w(f"| {e['id']} | {e['name_zh']} · {e['name_en']} | `{e['key']}` | {e['when_zh']} | {e['cue']['en']} |")
    w("")
    w("### 3) 手势词表 / Gesture lexicon（只用于中景 MS，手在画内）")
    w("")
    w("| # | 手势 | 标签 | 路径（回位 → 手势 → 回位） | 幅度上限 | 时长 | 风险 |")
    w("|---|---|---|---|---|---|---|")
    for g in ov["gestures"]:
        w(f"| {g['id']} | {g['name_zh']} · {g['name_en']} | `{g['key']}` | {g['path_zh']} | {g['limit_zh']} | {g['duration']} | {g['risk']} |")
    w("")
    w("### 4) 句子替换 / Line swaps（只作用于标注的底板，叠加时自动完成）")
    w("")
    w("| 底板 | 原句 | 改为 | 为什么 |")
    w("|---|---|---|---|")
    for r in ov["replace"]:
        w(f"| {' / '.join(r.get('plates', ['全部']))} | {r['zh'][0]} · *{r['en'][0]}* | {r['zh'][1]} · *{r['en'][1]}* | {r.get('why_zh', r['why'])} |")
    w("")
    for fr, title in (("ms", "5) 中景表演补丁 · MS performance patch（K02 / K04 / L02，接在 Performance / 表演 句末）"),
                      ("mcu", "6) 近景表演补丁 · MCU performance patch（K01 / K03 / K05 / O01 / K01H）")):
        w(f"### {title}")
        w("")
        for lang in ("en", "zh"):
            w("```text")
            w(ov["performance_append_by_framing"][fr][lang])
            w("```")
            w("")
        w(f"避免补丁 / Avoid add-on：`{ov['avoid_append_by_framing'][fr]['en']}` · `{ov['avoid_append_by_framing'][fr]['zh']}`")
        w("")
    w("### 7) 负面补充 / Negative extras")
    w("")
    w("所有底板 / all plates:")
    w("")
    w("```text")
    w(", ".join(ov["negative_extra"]["en"]))
    w("```")
    w("")
    w("```text")
    w("，".join(ov["negative_extra"]["zh"]))
    w("```")
    w("")
    w("中景再加 / MS plates also:")
    w("")
    w("```text")
    w(", ".join(ov["negative_extra_ms"]["en"]))
    w("```")
    w("")
    w("```text")
    w("，".join(ov["negative_extra_ms"]["zh"]))
    w("```")
    w("")
    for d in ov.get("negative_drop", []):
        w(f"- {' / '.join(d['plates'])} 去掉 `{', '.join(d['drop'])}`：{d['why_zh']}")
    w("")
    w("### 8) 新底板 K04 / K05（叠加层定义，不进 `library.json`，待验证）")
    w("")
    lib2 = pm.with_overlay_plates(lib, ov)
    for pid in pm.overlay_plate_ids(ov):
        p = lib2["plates"][pid]
        w(f"#### {pid} · {p['title_zh']} · {p['framing'].upper()} · {p['aspect']} · {p['duration']}s · 首帧 {p['first_frame']}")
        w("")
        for lang in ("en", "zh"):
            w("```text")
            w(pm.compose_overlay(lib, pid, lang, ov))
            w("```")
            w("")
        w("```text")
        w("Negative: " + pm.negative_overlay(lib, pid, ov))
        w("```")
        w("")
    w("### 9) 入库评分卡（加项）/ Scorecard add-ons")
    w("")
    w("| # | 检查（是 / 否） | Check (yes / no) |")
    w("|---|---|---|")
    for it in ov["scorecard"]:
        w(f"| {it['id']} | {it['zh']} | {it['en']} |")
    w("")
    w(f"**规则：** {ov['scorecard_rule']['zh']}")
    w(f"**Rule:** {ov['scorecard_rule']['en']}")
    w("")
    return L


def set_identity(
    root: str,
    photo: str,
    *,
    slug: str = "user",
    name: str | None = None,
    outfit: str | None = None,
    describe: str | None = None,
    out_dir: str | None = None,
    library_path: str | None = None,
) -> dict:
    """Photo → identity.json + library identity + GENERATE_PACK.md + rebuild docs."""
    ensure_default_backup(root)
    if not os.path.isfile(photo):
        raise FileNotFoundError(photo)
    library_path = library_path or os.path.join(root, "prompts", "library.json")
    lib = pm.load(library_path)

    slug = (slug or "user").strip().replace(" ", "-")
    id_dir = os.path.join(root, "prompts", "identity", slug)
    dh_dir = os.path.join(root, "dh-library", "00_identity", slug)
    photo_prompts = copy_photo(photo, id_dir, slug)
    photo_dh = copy_photo(photo, dh_dir, slug)

    identity = build_identity_text(name=name, describe=describe, outfit=outfit)
    apply_identity_to_library(lib, identity)

    meta = {
        "slug": slug,
        "name": name,
        "outfit": outfit,
        "describe": describe,
        "photo": photo_prompts,
        "photo_dh_library": photo_dh,
        "photo_rel": os.path.relpath(photo_prompts, root),
        "created": _now_iso(),
        "identity": identity,
        "note": "Appearance locks are from --describe/--outfit/--name only; no automatic face analysis.",
        "frozen_check": "N/A after identity set — run `identity restore` before `prompts verify` on default persona",
    }
    write_identity_json(os.path.join(id_dir, "identity.json"), meta)
    write_identity_json(state_path(root), meta)
    write_identity_json(os.path.join(dh_dir, "identity.json"), meta)

    with open(library_path, "w", encoding="utf-8") as f:
        json.dump(lib, f, ensure_ascii=False, indent=2)
        f.write("\n")

    pack = build_generate_pack_md(lib, meta)
    pack_paths = [
        os.path.join(root, "prompts", "GENERATE_PACK.md"),
        os.path.join(id_dir, "GENERATE_PACK.md"),
    ]
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        pack_paths.append(os.path.join(out_dir, "GENERATE_PACK.md"))
    for p in pack_paths:
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(pack)

    md_path = os.path.join(root, "prompts", "PROMPT_LIBRARY.md")
    txt_path = os.path.join(root, "prompts", "prompts-only.txt")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(pm.build_md(lib))
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(pm.build_txt(lib))

    return {
        "meta": meta,
        "written": [
            library_path,
            md_path,
            txt_path,
            *pack_paths,
            os.path.join(id_dir, "identity.json"),
            state_path(root),
            photo_prompts,
            photo_dh,
        ],
    }


def show_identity(root: str, library_path: str | None = None) -> str:
    library_path = library_path or os.path.join(root, "prompts", "library.json")
    lib = pm.load(library_path)
    lines = [
        "## blocks.identity",
        lib["blocks"]["identity"]["en"],
        lib["blocks"]["identity"]["zh"],
        "",
    ]
    st = state_path(root)
    if os.path.isfile(st):
        with open(st, encoding="utf-8") as f:
            meta = json.load(f)
        lines += [
            "## current identity state",
            f"slug: {meta.get('slug')}",
            f"photo: {meta.get('photo') or meta.get('photo_rel')}",
            f"name: {meta.get('name')}",
            f"created: {meta.get('created')}",
            f"note: {meta.get('note')}",
            f"frozen_check: {meta.get('frozen_check')}",
        ]
    else:
        lines.append("(no prompts/identity/current.json — using library default or hand-edited identity)")
    return "\n".join(lines) + "\n"


def restore_identity(root: str, library_path: str | None = None) -> dict:
    ensure_default_backup(root)
    library_path = library_path or os.path.join(root, "prompts", "library.json")
    lib = pm.load(library_path)
    restore_default(lib, root)
    with open(library_path, "w", encoding="utf-8") as f:
        json.dump(lib, f, ensure_ascii=False, indent=2)
        f.write("\n")
    md_path = os.path.join(root, "prompts", "PROMPT_LIBRARY.md")
    txt_path = os.path.join(root, "prompts", "prompts-only.txt")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(pm.build_md(lib))
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(pm.build_txt(lib))
    # rewrite GENERATE_PACK for default persona
    meta = {
        "slug": "default",
        "name": "default (shipped persona)",
        "photo": "(use your own reference image matching the default identity text, or run identity set)",
        "created": _now_iso(),
        "note": "Restored shipped default. Prefer `identity set --photo` for your own face.",
    }
    pack = build_generate_pack_md(lib, meta)
    pack_path = os.path.join(root, "prompts", "GENERATE_PACK.md")
    with open(pack_path, "w", encoding="utf-8") as f:
        f.write(pack)
    # clear current pointer but keep per-slug folders
    st = state_path(root)
    if os.path.isfile(st):
        os.remove(st)
    bad = pm.verify_frozen(lib)
    return {
        "written": [library_path, md_path, txt_path, pack_path],
        "verify_frozen": bad,
        "verify_ok": not bad,
    }
