import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
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
LEGACY_VOICE_IDS = {"Reed": "reed", "Tingting": "tingting"}
VOICE_PYTHON = ROOT / "build/voice-env/bin/python"
VOICE_MODEL = MODELS / "qwen3-tts-0.6b-base-4bit"
VOICE_REVISION = "0d6bb6fe33f92d47a507e23b9148940e8366ab5b"
SPEECH_PAUSE = 0.14
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


def system_voices():
    """Map saved voice IDs to the exact names accepted by this Mac's say command."""
    say = shutil.which("say")
    if not say:
        return {}
    try:
        listing = subprocess.run([say, "-v", "?"], capture_output=True, text=True,
                                 encoding="utf-8", timeout=5, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    voices = {}
    for line in listing.splitlines():
        match = re.fullmatch(r"(.+?)\s+([a-z]{2,3}(?:[_-][A-Za-z0-9]+)*)\s+#\s*(.*)", line)
        if not match:
            continue
        name, locale, sample = match.groups()
        locale = locale.replace("_", "-")
        ident = f"system:{locale}:{name}"
        # Existing projects and generated audio use these two language-specific IDs.
        base = name.partition(" (")[0]
        if locale == "zh-CN" and base in LEGACY_VOICE_IDS and LEGACY_VOICE_IDS[base] not in voices:
            ident = LEGACY_VOICE_IDS[base]
        voices[ident] = dict(id=ident, name=name, locale=locale, sample=sample)
    return voices


def reference_text(transcript, duration):
    if not isinstance(transcript, str) or not 1 <= len(transcript.strip()) <= 1500:
        raise ValueError("请填写录音逐字稿（最多 1500 字）")
    transcript = transcript.strip()
    # Reject only a large mismatch. Ignore punctuation, whitespace and Latin spelling.
    han = len(re.findall(r"[\u3400-\u9fff]", transcript))
    if han > max(30, 12 * duration):
        raise ValueError(f"参考录音仅 {duration:.1f} 秒，逐字稿含 {han} 个汉字。请试听录音，将逐字稿改为录音实际说出的内容。")
    return transcript


def register_reference(a, name, transcript):
    name = name.strip()
    if not 1 <= len(name) <= 60:
        raise ValueError("请填写音色名称（最多 60 字）")
    transcript = reference_text(transcript, a["duration"])
    path = Path(a["path"])
    reference = path.with_name("reference.wav")
    ff("-protocol_whitelist", "file,pipe", "-i", path, "-vn", "-ar", "24000",
       "-ac", "1", "-c:a", "pcm_s16le", reference)
    with wave.open(str(reference), "rb") as wav:
        pcm = np.frombuffer(wav.readframes(wav.getnframes()), "<i2")
    if not pcm.size or not np.any(pcm):
        raise ValueError("参考录音没有可用声音，请选择清晰的单人录音")
    a.update(name=name, transcript=transcript)


def personal_voice_missing():
    required = ("config.json", "model.safetensors", "merges.txt", "vocab.json", "tokenizer_config.json",
                "speech_tokenizer/config.json", "speech_tokenizer/model.safetensors")
    missing = [name for name in required if not (VOICE_MODEL / name).is_file()]
    if not VOICE_PYTHON.is_file() or not VOICE_PYTHON.with_name("mlx_audio.tts.generate").is_file():
        missing.append("MLX-Audio 独立环境")
    return missing


def personal_voice_ready():
    return not personal_voice_missing()


def synthesized_lines(mode, lines, folder, profile):
    if profile is not None:
        if not personal_voice_ready():
            raise ValueError("本机缺少个人音色引擎或模型，请按 README 的个人音色步骤安装")
        request = dict(lines=lines, model=str(VOICE_MODEL), transcript=profile["transcript"],
                       reference=str(Path(profile["path"]).with_name("reference.wav")),
                       maxSeconds=MAX_SECONDS, pause=SPEECH_PAUSE)
        try:
            worker = subprocess.run([VOICE_PYTHON, Path(__file__).with_name("personal_voice.py"), folder],
                                    input=json.dumps(request).encode(), capture_output=True, timeout=1800)
        except subprocess.TimeoutExpired:
            raise ValueError("个人音色合成超时，请将文案分段后再试") from None
        if worker.returncode:
            detail = worker.stderr.decode(errors="replace").strip().splitlines()
            raise ValueError(detail[-1].removeprefix("ValueError: ")[:300] if detail else "个人音色推理进程已退出")
        for index in range(len(lines)):
            yield read_pcm(folder / f"{index}.wav")
    else:
        voice = system_voices().get(mode)
        if not voice:
            raise ValueError("本机找不到所选系统音色，请刷新页面后重新选择或使用素材库录音")
        for line in lines:
            # Read speech from stdin to preserve punctuation and leading hyphens.
            run(["say", "-v", voice["name"], "-o", folder / "line.aiff"], line.encode())
            yield read_pcm(folder / "line.aiff")


def prepare_voice(cfg, *, cached_only=False):
    lines = sentences(cfg.get("text"))
    mode = cfg.get("voice", "reed")
    if not isinstance(mode, str) or not mode:
        raise ValueError("请选择配音来源")
    profile = None
    version = "voice-v1"
    if mode.startswith("personal-"):
        profile = asset(mode)
        if profile["role"] != "personal_voice":
            raise ValueError("请选择素材库中的个人音色")
        reference_text(profile["transcript"], profile["duration"])
        version = ["personal-voice-v2", VOICE_REVISION, profile["transcript"]]
    key = signature(version, lines, mode)
    store = STORE / "voices" / key
    result = store / "voice.json"
    if result.is_file() and (store / "voice.wav").is_file():
        return json.loads(result.read_text())
    if cached_only:
        return None
    store.mkdir(exist_ok=True, parents=True)
    spans = []
    if mode in LEGACY_VOICE_IDS.values() or mode.startswith(("system:", "personal-")):
        parts = []
        samples = 0
        pause = np.zeros(round(SPEECH_PAUSE * RATE), dtype="<i2")
        with tempfile.TemporaryDirectory(dir=store) as tmp:
            for pcm in synthesized_lines(mode, lines, Path(tmp), profile):
                if len(pcm) < RATE * 0.04 or not np.any(pcm):
                    raise ValueError("未产出有效音频，请检查所选音色")
                spans.append((samples / RATE, (samples + len(pcm)) / RATE))
                parts.extend([pcm, pause])
                samples += len(pcm) + len(pause)
                if samples > MAX_SECONDS * RATE:
                    raise ValueError("本工作台单条配音上限为 120 秒，请分段制作")
        pcm = np.concatenate(parts)
        method = "个人音色逐句合成" if mode.startswith("personal-") else "逐句合成"
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
    if profile:
        info["referenceVersion"] = signature(profile["transcript"])
    tmp = result.with_suffix(".tmp")
    tmp.write_text(json.dumps(info, ensure_ascii=False))
    tmp.replace(result)
    return info
