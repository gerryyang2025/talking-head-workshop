import argparse
import collections
import datetime
import importlib.util
import json
import re
import shutil
import threading
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
from .production import CAPTION_BAND, SIZES, plan, render

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config.update(MAX_CONTENT_LENGTH=160 * 1024 * 1024)
executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="studio-render")
asset_lock = threading.RLock()
voice_lock = threading.Lock()
WEIGHTS = [
    "musetalk-1.5-fp16/" + v
    for v in (
        "config.json",
        "unet.safetensors",
        "vae.safetensors",
        "whisper_encoder.safetensors",
    )
]
WEIGHTS += ["studio/yunet.onnx", "studio/2dfan4.onnx"]


def dependencies():
    missing = [name for name in WEIGHTS if not (MODELS / name).is_file()]
    missing.extend(
        pkg
        for pkg in ("mlx", "musetalk_mlx", "onnxruntime")
        if not importlib.util.find_spec(pkg)
    )
    return dict(
        ready=not missing,
        missing=missing,
        tts=bool(shutil.which("say")),
        engine="MuseTalk 1.5",
    )


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
    with db() as con:
        assets = [
            public_asset(json.loads(r[0]))
            for r in con.execute("SELECT info FROM assets ORDER BY rowid")
        ]
    return jsonify(
        assets=assets,
        jobs=all_jobs(),
        engine=dependencies(),
        demoText=media.DEMO_TEXT,
        exportSizes=SIZES,
        captionBand=CAPTION_BAND,
    )


@app.post("/api/assets")
def upload():
    file = request.files.get("file")
    role = request.form.get("role", "host")
    if not file or not file.filename or role not in ("host", "audio", "insert"):
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
    if not kind or (kind == "audio") != (role == "audio"):
        raise ValueError("文件类型与用途不符。支持常用图片、MP4/MOV 和 WAV/MP3/M4A。")
    ident = token()
    folder = STORE / "assets" / ident
    folder.mkdir(parents=True)
    try:
        path = folder / ("source" + ext)
        file.save(path)
        a = build_asset(path, kind, role, Path(file.filename).stem[:90], ident)
        save_asset(a)
    except Exception:
        shutil.rmtree(folder)
        raise
    return jsonify(public_asset(a)), 201


@app.get("/api/assets/<ident>/<variant>")
def media_file(ident, variant):
    a = asset(ident)
    key = {"source": "path", "poster": "poster_file"}.get(variant)
    if not key or not a.get(key):
        abort(404)
    return send_file(a[key], conditional=True)


@app.route("/api/shots/<ident>", methods=["GET", "POST"])
def shots(ident):
    with asset_lock:
        a = asset(ident)
        if a["role"] != "host":
            raise ValueError("请选择人物母片")
        if request.method == "POST":
            a["shots"] = media.clean_shots(a, request.get_json()["shots"])
            save_asset(a)
        return jsonify(shots=media.shots_for(a))


@app.post("/api/voice")
def voice():
    with voice_lock:
        return jsonify(media.prepare_voice(request.get_json()))


@app.get("/api/voice/<ident>")
def hear(ident):
    if not re.fullmatch("[0-9a-f]{64}", ident):
        abort(404)
    return send_file(STORE / "voices" / ident / "voice.wav", conditional=True)


@app.get("/api/voice/<ident>/info")
def voice_info(ident):
    if not re.fullmatch("[0-9a-f]{64}", ident):
        abort(404)
    return send_file(
        STORE / "voices" / ident / "voice.json", mimetype="application/json"
    )


def job_info(ident):
    with db() as con:
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
        used = collections.Counter(
            r["shot"]["id"] for r in timeline["rows"] if r["shot"]
        )
        info.update(
            status="done",
            progress=100,
            message="成片可播放",
            qc=summary,
            usage=dict(used),
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
    deps = dependencies()
    if not deps["ready"] and any(row["shot"] for row in tl["rows"]):
        raise ValueError("缺少口型依赖：" + ", ".join(deps["missing"]))
    info = dict(
        id=token(),
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
    return jsonify(job_info(ident))


@app.get("/api/jobs/<ident>/<what>")
def result(ident, what):
    info = job_info(ident)
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
