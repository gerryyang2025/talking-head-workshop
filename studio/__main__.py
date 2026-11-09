import argparse
import collections
import datetime
import importlib.util
import json
import re
import shutil
import threading
import tempfile
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, abort, jsonify, request, send_file
from werkzeug.exceptions import HTTPException

from . import media
from .media import (
    STORE,
    MODELS,
    asset,
    build_asset,
    db,
    public_asset,
    save_asset,
    token,
)
from .production import CAPTION_BAND, SIZES, plan, render, render_card_preview, visual_spans

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config.update(MAX_CONTENT_LENGTH=160 * 1024 * 1024)
executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="studio-render")
asset_lock = threading.RLock()
voice_lock = threading.Lock()


def lipsync_models():
    folder = "musetalk-1.5-fp16/"
    components = (
        ("MuseTalk 1.5", "根据配音生成口型 · UNet、VAE", ("mlx", "musetalk_mlx"),
         (folder + "config.json", folder + "unet.safetensors", folder + "vae.safetensors")),
        ("Whisper 音频编码器", "为 MuseTalk 提取语音特征", ("mlx", "musetalk_mlx"), (folder + "whisper_encoder.safetensors",)),
        ("YuNet", "检测画面中的人脸", ("cv2",), ("studio/yunet.onnx",)),
        ("2DFAN4", "定位面部关键点和嘴部区域", ("onnxruntime",), ("studio/2dfan4.onnx",)),
    )
    models = []
    for name, purpose, packages, files in components:
        missing = [pkg for pkg in packages if not importlib.util.find_spec(pkg)]
        missing.extend(path for path in files if not (MODELS / path).is_file())
        models.append(dict(name=name, purpose=purpose, missing=missing))
    return models


def dependencies(models=None):
    models = lipsync_models() if models is None else models
    missing = list(dict.fromkeys(item for model in models for item in model["missing"]))
    return dict(
        ready=not missing,
        missing=missing,
        engine="MuseTalk 1.5",
    )


def require_lipsync():
    deps = dependencies()
    if not deps["ready"]:
        raise ValueError("缺少口型依赖：" + ", ".join(deps["missing"]))


@app.before_request
def local_only():
    if urlsplit(request.host_url).hostname not in ("127.0.0.1", "localhost", "::1"):
        abort(403)
    if request.method == "POST" and (
        request.headers.get("X-Studio-Request") != "1"
        or (
            request.headers.get("Origin")
            and request.headers["Origin"] != request.host_url.rstrip("/")
        )
    ):
        abort(403)


@app.errorhandler(Exception)
def error(exc):
    code = (
        exc.code
        if isinstance(exc, HTTPException)
        else (400 if isinstance(exc, (ValueError, TypeError, KeyError)) else 500)
    )
    if code == 500:
        app.logger.exception("Studio request")
    return jsonify(error=str(exc)), code


@app.get("/")
def home():
    return app.send_static_file("index.html")


def all_jobs():
    with db() as con:
        return [
            json.loads(r[0])
            for r in con.execute("SELECT info FROM jobs ORDER BY rowid DESC LIMIT 60")
        ]


@app.get("/api/session")
def session():
    voices = media.system_voices()
    models = lipsync_models()
    voice_missing = media.personal_voice_missing()
    catalog = [
        dict(name="Qwen3-TTS 0.6B Base · 4-bit", purpose="用参考录音和逐字稿合成个人音色 · MLX-Audio、语音分词器", missing=voice_missing),
        *models,
    ]
    tools = [
        dict(name="macOS 系统语音", purpose=f"系统音色配音 · {len(voices)} 个可选声音",
             missing=[] if voices else ["未找到可用的系统音色"]),
        dict(name="FFmpeg / FFprobe", purpose="读取、转码和导出音视频",
             missing=[cmd for cmd in ("ffmpeg", "ffprobe") if not shutil.which(cmd)]),
    ]
    with db() as con:
        assets = [
            public_asset(json.loads(r[0]))
            for r in con.execute("SELECT info FROM assets ORDER BY rowid")
        ]
    return jsonify(
        assets=assets,
        jobs=all_jobs(),
        engine=dict(dependencies(models), tts=bool(voices), personalVoice=not voice_missing,
                    models=catalog, tools=tools),
        systemVoices=list(voices.values()),
        demoText=media.DEMO_TEXT,
        maxNarrationSeconds=media.MAX_NARRATION_SECONDS,
        exportSizes=SIZES,
        captionBand=CAPTION_BAND,
    )


@app.post("/api/assets")
def upload():
    file = request.files.get("file")
    role = request.form.get("role", "host")
    if not file or not file.filename or role not in ("host", "audio", "insert", "personal_voice"):
        raise ValueError("请选择素材文件及用途")
    ext = Path(file.filename).suffix.lower()
    kinds = {
        ".jpg": "photo",
        ".jpeg": "photo",
        ".png": "photo",
        ".webp": "photo",
        ".mp4": "video",
        ".mov": "video",
        ".m4v": "video",
        ".mp3": "audio",
        ".wav": "audio",
        ".m4a": "audio",
        ".aiff": "audio",
        ".aac": "audio",
    }
    kind = kinds.get(ext)
    if not kind or (kind == "audio") != (role in ("audio", "personal_voice")):
        raise ValueError("文件类型与用途不符。支持常用图片、MP4/MOV 和 WAV/MP3/M4A。")
    ident = ("personal-" if role == "personal_voice" else "") + token()
    folder = STORE / "assets" / ident
    folder.mkdir(parents=True)
    try:
        path = folder / ("source" + ext)
        file.save(path)
        a = build_asset(path, kind, role, Path(file.filename).stem[:90], ident)
        if role == "personal_voice":
            media.register_reference(a, request.form.get("name", ""), request.form.get("transcript", ""))
        save_asset(a)
    except Exception:
        shutil.rmtree(folder)
        raise
    return jsonify(public_asset(a)), 201


@app.post("/api/assets/<ident>/transcript")
def edit_reference(ident):
    with asset_lock:
        profile = asset(ident)
        if profile["role"] != "personal_voice":
            raise ValueError("请选择个人音色")
        transcript = media.reference_text(request.get_json().get("transcript"), profile["duration"])
        if transcript != profile["transcript"]:
            profile.update(transcript=transcript, referenceVersion=media.signature(transcript))
            save_asset(profile)
    return jsonify(public_asset(profile))


@app.get("/api/assets/<ident>/<variant>")
def media_file(ident, variant):
    a = asset(ident)
    if variant == "reference" and a["role"] == "personal_voice":
        return send_file(Path(a["path"]).with_name("reference.wav"), conditional=True)
    key = {"source": "path", "poster": "poster_file"}.get(variant)
    if not key or not a.get(key):
        abort(404)
    return send_file(a[key], conditional=True)


@app.route("/api/shots/<ident>", methods=["GET", "POST"])
def shots(ident):
    with asset_lock:
        a = asset(ident)
        if a["role"] not in ("host", "insert"):
            raise ValueError("请选择人物母片")
        if request.method == "POST":
            a["shots"] = media.clean_shots(a, request.get_json()["shots"])
            save_asset(a)
        return jsonify(shots=media.shots_for(a))


@app.post("/api/voice")
def voice():
    cfg = request.get_json()
    cached_only = request.args.get("cached") == "1"
    personal = isinstance(cfg.get("voice"), str) and cfg["voice"].startswith("personal-")
    if cached_only or personal:
        cached = media.prepare_voice(cfg, cached_only=True)
        if cached_only or cached is not None:
            return jsonify(cached)
    if personal:
        # Serialize Metal inference with lip sync and other personal-voice requests.
        return jsonify(executor.submit(media.prepare_voice, cfg).result())
    with voice_lock:
        return jsonify(media.prepare_voice(cfg))


@app.post("/api/card-preview")
def card_preview():
    config = request.get_json()
    with tempfile.TemporaryDirectory(dir=STORE) as tmp:
        if config.get("insertSpeaking") is True:
            require_lipsync()
            # Share the GPU and cache with exports, including simultaneous preview requests.
            path = executor.submit(render_card_preview, config, Path(tmp)).result()
        else:
            path = render_card_preview(config, Path(tmp))
        return app.response_class(path.read_bytes(), mimetype="video/mp4")


@app.get("/api/voice/<ident>")
def hear(ident):
    if not re.fullmatch("[0-9a-f]{64}", ident):
        abort(404)
    return send_file(STORE / "voices" / ident / "voice.wav", conditional=True)


def visible_speech(spans):
    return any((s["voiced"] or "rest_from" in s) and (s["shot"] or s["insertSpeaking"]) for s in spans)


@app.post("/api/timeline-preview")
def timeline_preview():
    config = request.get_json()
    with asset_lock:
        tl = plan(config)
    first, stop = config.get("previewFirst"), config.get("previewStop")
    if type(first) is not int or type(stop) is not int or not 0 <= first < stop <= tl["frames"]:
        raise ValueError("预览范围超出时间线")
    spans = (s for s in visual_spans(tl) if s["first"] < stop and s["stop"] > first)
    with tempfile.TemporaryDirectory(dir=STORE) as tmp:
        args = (tl, Path(tmp), lambda *_: None, (first, stop))
        if visible_speech(spans):
            require_lipsync()
            path = executor.submit(render, *args).result()
        else:
            path = render(*args)
        return app.response_class(path.read_bytes(), mimetype="video/mp4")


@app.get("/api/voice/<ident>/info")
def voice_info(ident):
    if not re.fullmatch("[0-9a-f]{64}", ident):
        abort(404)
    return send_file(
        STORE / "voices" / ident / "voice.json", mimetype="application/json"
    )


def job_info(ident, con):
    row = con.execute("SELECT info FROM jobs WHERE id=?", (ident,)).fetchone()
    if not row:
        abort(404)
    return json.loads(row[0])


def put_job(info, usage=None):
    with db() as con:
        con.execute(
            "INSERT INTO jobs VALUES (?,?) ON CONFLICT(id) DO UPDATE SET info=excluded.info",
            (info["id"], json.dumps(info, ensure_ascii=False)),
        )
        if usage:
            con.executemany(
                "INSERT OR IGNORE INTO usage VALUES (?,?,?)",
                [(info["id"], s, n) for s, n in usage.items()],
            )


def worker(info, timeline):
    def notify(p, message):
        if info["progress"] != p or info["message"] != message:
            info.update(status="running", progress=p, message=message)
            put_job(info)

    try:
        folder = STORE / "jobs" / info["id"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "timeline.json").write_text(
            json.dumps(timeline, ensure_ascii=False, indent=2)
        )
        summary = render(timeline, folder, notify)
        # A cut can interrupt a shot several times. Count each placement once.
        placements = {s["owner"]: s for s in visual_spans(timeline)}.values()
        used = collections.Counter(s["shot"]["id"] for s in placements if s["shot"])
        materials = used.copy()
        materials.update(s["insert"] for s in placements if s["insert"])
        info.update(
            status="done",
            progress=100,
            message="成片可播放",
            qc=summary,
            usage=dict(materials),
        )
        put_job(info, used)
    except Exception as exc:
        traceback.print_exc()
        info.update(status="failed", message=str(exc)[:500] or type(exc).__name__)
        put_job(info)


@app.post("/api/jobs")
def create_job():
    config = request.get_json()
    with asset_lock:
        tl = plan(config)
    if visible_speech(visual_spans(tl)):
        require_lipsync()
    info = dict(
        id=token(),
        voiceId=tl["voice"],
        title=tl["title"],
        aspect=tl["aspect"],
        status="queued",
        progress=0,
        message="等待本机渲染",
        created=datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    )
    put_job(info)
    executor.submit(worker, dict(info), tl)
    return jsonify(info), 202


@app.get("/api/jobs/<ident>")
def get_job(ident):
    with db() as con:
        return jsonify(job_info(ident, con))


@app.post("/api/jobs/<ident>/review")
def review_job(ident):
    payload = request.get_json()
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, dict) or not items or items.keys() - {"playback", "mouth", "edit"}:
        raise ValueError("请选择有效的复核项")
    with db() as con:
        # Merge individual decisions under the write lock so tabs can review independently.
        con.execute("BEGIN IMMEDIATE")
        job = job_info(ident, con)
        if job["status"] != "done":
            abort(409, description="生成完成后才可复核")
        review = job.setdefault("review", {})
        for key, item in items.items():
            status = item.get("status") if isinstance(item, dict) else None
            if status not in ("pending", "passed", "issue"):
                raise ValueError("无效的复核状态")
            if payload.get("onlyMissing") is True and key in review:
                continue
            entry = {"status": status}
            if status == "issue":
                note = item.get("note")
                if not isinstance(note, str) or not 1 <= len(note.strip()) <= 300:
                    raise ValueError("请用 1 至 300 字描述问题")
                entry["note"] = note.strip()
                entry["time"] = media.number(
                    item.get("time"), 0, job["qc"]["duration"], "问题位置超出成片时长"
                )
            review[key] = entry
        con.execute("UPDATE jobs SET info=? WHERE id=?", (json.dumps(job, ensure_ascii=False), ident))
    return jsonify(job)


@app.get("/api/jobs/<ident>/<what>")
def result(ident, what):
    with db() as con:
        info = job_info(ident, con)
    if info["status"] != "done" or what not in ("film", "timeline"):
        abort(404)
    path = STORE / "jobs" / ident / ("film.mp4" if what == "film" else "timeline.json")
    return send_file(
        path,
        conditional=True,
        as_attachment=request.args.get("download") == "1",
        download_name=(info["title"] + ".mp4") if what == "film" else "timeline.json",
    )


def main():
    parser = argparse.ArgumentParser(description="单机数字人口播工作台")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    # A second launcher must not mark the running worker's jobs as interrupted.
    import fcntl

    STORE.mkdir(parents=True, exist_ok=True)
    lock = (STORE / "service.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.exit(1, "此工作区的口播服务已在运行。\n")
    media.init()
    app.run(
        host="127.0.0.1", port=args.port, threaded=True, debug=False, use_reloader=False
    )


if __name__ == "__main__":
    main()
