import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import uuid
import wave
from contextlib import contextmanager
from pathlib import Path

import numpy as np

from istream import script as screenplay, slicer

ROOT = Path(__file__).resolve().parents[1]
STORE = Path(os.environ.get("KOUBO_STUDIO_DATA", ROOT / "build/studio")).resolve()
MODELS = ROOT / "build/models"
FPS = 25
RATE = 48000
MAX_SECONDS = 120
os.environ["PATH"] = str(ROOT / ".venv/bin") + os.pathsep + os.environ.get("PATH", "")
DEMO_TEXT = "把一张照片做成口播视频，要经过三步。\n先确定人物形象，再为文案配音。\n最后，让人物的口型跟上每一个字。"
VOICES = {"reed": "Reed (中文（中国大陆）)", "tingting": "Tingting"}
LAYOUTS = {
    "full": "全屏人物",
    "split": "分屏讲解",
    "pip": "圆形小窗",
    "card": "动态图文",
    "insert": "补充画面",
}


@contextmanager
def db():
    STORE.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(STORE / "studio.sqlite3", timeout=20)
    con.row_factory = sqlite3.Row
    try:
        with con:
            yield con
    finally:
        con.close()


def run(args, data=None):
    p = subprocess.run(list(map(str, args)), input=data, capture_output=True)
    if p.returncode:
        err = p.stderr.decode(errors="replace").strip()
        raise ValueError(err[-600:] or f"{args[0]} 执行失败")
    return p.stdout


def ff(*args):
    return run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *args]
    )


def inspect_file(path):
    return json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                "-format_whitelist",
                "mov,wav,mp3,aiff,aac,image2,png_pipe,jpeg_pipe,webp_pipe",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                path,
            ]
        )
    )


def token():
    return uuid.uuid4().hex


def signature(*parts):
    return hashlib.sha256(
        json.dumps(parts, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def asset(asset_id):
    with db() as con:
        row = con.execute("SELECT info FROM assets WHERE id=?", (asset_id,)).fetchone()
    if not row:
        raise ValueError("找不到所选素材")
    return json.loads(row[0])


def public_asset(a):
    return {k: v for k, v in a.items() if k not in {"path", "poster_file"}}


def save_asset(a):
    with db() as con:
        con.execute(
            "INSERT OR REPLACE INTO assets VALUES (?,?)",
            (a["id"], json.dumps(a, ensure_ascii=False)),
        )


def build_asset(path, kind, role, name, ident):
    data = inspect_file(path)
    streams = data["streams"]
    stream = next(
        (
            s
            for s in streams
            if s["codec_type"] == ("audio" if kind == "audio" else "video")
        ),
        None,
    )
    if not stream:
        raise ValueError("文件内容与所选素材类型不符")
    duration = float(data["format"].get("duration", 0)) if kind != "photo" else 0
    if kind != "photo" and not 0.08 <= duration <= MAX_SECONDS:
        raise ValueError(f"请使用 0.08 至 {MAX_SECONDS} 秒的素材")
    a = dict(
        id=ident,
        name=name,
        kind=kind,
        role=role,
        path=str(path),
        duration=duration,
        width=stream.get("width", 0),
        height=stream.get("height", 0),
    )
    if a["width"] * a["height"] > 48000000:
        raise ValueError("图像过大，请先缩小至 4800 万像素以内")
    folder = STORE / "assets" / ident
    folder.mkdir(exist_ok=True, parents=True)
    if kind != "audio":
        poster = folder / "poster.jpg"
        ff(
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            path,
            "-frames:v",
            "1",
            "-vf",
            "scale=960:960:force_original_aspect_ratio=decrease",
            poster,
        )
        a["poster_file"] = str(poster)
    return a


def init():
    with db() as con:
        con.executescript("""CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY, info TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, info TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS usage(job TEXT, shot TEXT, times INTEGER, PRIMARY KEY(job,shot));""")
        entries = con.execute("SELECT id,info FROM jobs").fetchall()
        for row in entries:
            info = json.loads(row["info"])
            if info["status"] in ("running", "queued"):
                info.update(status="failed", message="服务上次已停止，可重新生成。")
                con.execute(
                    "UPDATE jobs SET info=? WHERE id=?", (json.dumps(info), row["id"])
                )
        known = {r[0] for r in con.execute("SELECT id FROM assets")}
    base = ROOT / "build/gerry/talking-head"
    for ident, file, kind, role, name in [
        ("demo-plate", base / "portrait-base.mp4", "video", "host", "Gerry · 半身母片"),
        (
            "demo-photo",
            ROOT / "prompts/identity/gerry/ref.png",
            "photo",
            "host",
            "Gerry · 人物参考照",
        ),
        ("demo-audio", base / "narration.wav", "audio", "audio", "三步制作口播 · 配音"),
    ]:
        if ident not in known and file.is_file():
            save_asset(build_asset(file, kind, role, name, ident))


def shots_for(a):
    if "shots" in a:
        return a["shots"]
    duration = a["duration"]
    spans = [(0, duration, [])]
    if a["kind"] == "video" and duration >= 2.2:
        proxy = STORE / "assets" / a["id"] / "analysis.mp4"
        ff(
            "-i",
            a["path"],
            "-vf",
            "fps=5,scale=320:-2",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-c:a",
            "aac",
            proxy,
        )
        proposed = slicer.propose(slicer.analyze(str(proxy)), a["id"])
        spans = [
            (s["src"]["in"], min(duration, s["src"]["out"]), s["quality"]["defects"])
            for s in proposed
        ] or spans
    shots = []
    for i, (start, end, defects) in enumerate(spans):
        shots.append(
            dict(
                id=f"{a['id']}-{i + 1}",
                asset=a["id"],
                start=start,
                end=end,
                enabled=not bool(defects),
                label=f"镜头 {i + 1:02d}",
                emotion="待复核",
                gaze="待复核",
                gesture="待复核",
                warning="检测到画面叠层，请复核" if defects else "",
            )
        )
    a["shots"] = shots
    save_asset(a)
    return shots


def number(value, low, high, message):
    try:
        n = float(value)
    except (ValueError, TypeError):
        raise ValueError(message) from None
    if not math.isfinite(n) or not low <= n <= high:
        raise ValueError(message)
    return n


def clean_shots(a, rows):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 60:
        raise ValueError("请至少保留一个切片，最多 60 个")
    result = []
    for i, s in enumerate(rows):
        if not isinstance(s, dict):
            raise ValueError("切片格式无效")
        start = number(s.get("start"), 0, a["duration"], "入点超出素材范围")
        end = number(s.get("end"), start, a["duration"], "出点超出素材范围")
        if a["kind"] == "video" and end - start < 1 / FPS - 1e-6:
            raise ValueError("切片至少需要一帧")
        result.append(
            dict(
                id=f"{a['id']}-{i + 1}",
                asset=a["id"],
                start=start,
                end=end,
                enabled=s.get("enabled") is True,
                **{
                    k: str(s.get(k, ""))[:50]
                    for k in ("label", "emotion", "gaze", "gesture", "warning")
                },
            )
        )
    return result


def english_sentences(text):
    """Split at sentence-final periods, preserving decimals, domains and initials."""
    start = 0
    for match in re.finditer(r'\.[”"’)]*(?=\s|$)', text):
        prefix = text[start : match.start() + 1]
        if re.search(r"\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|e\.g|i\.e|[A-Z])\.$", prefix, re.I):
            continue
        yield text[start : match.end()].strip()
        start = match.end()
    if text[start:].strip():
        yield text[start:].strip()


def sentences(text):
    if not isinstance(text, str) or not text.strip() or len(text) > 1500:
        raise ValueError("请填写 1 至 1500 字的文案")
    _, beats, _ = screenplay.parse(text.strip())
    lines = [sentence for beat in beats for sentence in english_sentences(beat["text"])]
    if not lines or len(lines) > 60:
        raise ValueError("请使用 1 至 60 个句段")
    return lines


def read_pcm(path):
    raw = ff("-i", path, "-vn", "-ar", str(RATE), "-ac", "1", "-f", "s16le", "pipe:1")
    return np.frombuffer(raw, "<i2")


def write_wav(path, pcm):
    with wave.open(str(path), "wb") as w:
        w.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        w.writeframes(pcm.astype("<i2", copy=False).tobytes())


def prepare_voice(cfg):
    lines = sentences(cfg.get("text"))
    mode = cfg.get("voice", "reed")
    key = signature("voice-v1", lines, mode)
    store = STORE / "voices" / key
    result = store / "voice.json"
    if result.exists():
        return json.loads(result.read_text())
    store.mkdir(exist_ok=True, parents=True)
    spans = []
    if mode in VOICES:
        if not shutil.which("say"):
            raise ValueError("此系统没有 macOS say，请上传配音")
        parts = []
        samples = 0
        for line in lines:
            # Read speech from stdin to preserve punctuation and leading hyphens.
            run(["say", "-v", VOICES[mode], "-o", store / "line.aiff"], line.encode())
            pcm = read_pcm(store / "line.aiff")
            if len(pcm) < RATE * 0.04 or not np.any(pcm):
                raise ValueError("系统语音未产出有效音频，请检查声音或上传配音")
            spans.append((samples / RATE, (samples + len(pcm)) / RATE))
            pause = np.zeros(round(0.14 * RATE), dtype="<i2")
            parts.extend([pcm, pause])
            samples += len(pcm) + len(pause)
            if samples > MAX_SECONDS * RATE:
                raise ValueError("本工作台单条配音上限为 120 秒，请分段制作")
        pcm = np.concatenate(parts)
        method = "逐句合成"
    else:
        a = asset(mode)
        if a["kind"] != "audio":
            raise ValueError("请选择音频素材")
        pcm = read_pcm(a["path"])
        duration = len(pcm) / RATE
        if mode == "demo-audio" and lines == sentences(DEMO_TEXT):
            spans = [(0.48, 3.67), (3.79, 6.47), (6.59, 9.11)]
            method = "示例已校时"
        else:
            weights = np.cumsum([len(t) for t in lines])
            boundaries = np.r_[0, duration * weights / weights[-1]]
            spans = list(zip(boundaries[:-1], boundaries[1:]))
            method = "按字数初排，请试听校时"
    duration = len(pcm) / RATE
    if duration > MAX_SECONDS:
        raise ValueError("配音超过 120 秒")
    write_wav(store / "voice.wav", pcm)
    blocks = pcm[: len(pcm) // 160 * 160].astype(float).reshape(-1, 160)
    rms = np.sqrt(np.mean(blocks**2, axis=1))
    bars = [float(v.max()) if len(v) else 0 for v in np.array_split(rms, 96)]
    peak = max(max(bars), 1)
    info = dict(
        id=key,
        duration=duration,
        method=method,
        waveform=[round(v / peak, 3) for v in bars],
        lines=[
            dict(text=t, start=round(s, 3), end=round(e, 3))
            for t, (s, e) in zip(lines, spans)
        ],
    )
    tmp = result.with_suffix(".tmp")
    tmp.write_text(json.dumps(info, ensure_ascii=False))
    tmp.replace(result)
    return info
