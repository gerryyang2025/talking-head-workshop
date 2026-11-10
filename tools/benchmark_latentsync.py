"""Measure both LatentSync memory modes on the same 32 frames (Apple Silicon)."""
import argparse
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import time
import wave

from studio.latent_memory import memory_mode
from studio.media import FPS, MODELS, STORE, ff
from studio.setup_models import NATIVE_CLI, NATIVE_WEIGHTS


def require_headroom():
    database = STORE / "studio.sqlite3"
    if database.exists():
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
            busy = db.execute("""SELECT 1 FROM jobs WHERE json_extract(info, '$.status')
                IN ('queued','running','pausing','cancelling') LIMIT 1""").fetchone()
        if busy:
            raise SystemExit("工作台有导出任务，未启动测速。请在导出队列空闲时运行。")
    saver, reason = memory_mode()
    if saver:
        raise SystemExit(f"当前只适合节省内存模式（{reason}），未启动测速。")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="单人母片，至少 1.28 秒")
    parser.add_argument("audio", type=Path, help="配音，至少 1.28 秒")
    args = parser.parse_args()
    require_headroom()
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        video, audio = folder / "reference.mp4", folder / "speech.wav"
        ff("-i", args.video, "-an", "-vf", "fps=25,scale='min(1280,iw)':'min(1280,ih)':force_original_aspect_ratio=decrease:"
           "force_divisible_by=2", "-frames:v", "32", "-c:v", "libx264", "-pix_fmt", "yuv420p", video)
        ff("-i", args.audio, "-vn", "-t", "1.28", "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", audio)
        count = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                         "stream=nb_frames", "-of", "csv=p=0", video], text=True)
        with wave.open(str(audio), "rb") as wav:
            if count.strip() != "32" or wav.getnframes() != 32 * 16000 // FPS:
                raise SystemExit("母片和配音都需要至少 1.28 秒。")
        for saver in (True, False):
            require_headroom()
            mode = "节省内存" if saver else "双路合批"
            out = folder / str(saver)
            out.mkdir()
            print(f"{mode}：开始推理 32 帧…", flush=True)
            start = time.monotonic()
            proc = subprocess.run(["/usr/bin/time", "-l", MODELS / NATIVE_CLI, "--family", "latentsync",
                "--task", "gen", "--backend", "metal", "--model", MODELS / NATIVE_WEIGHTS["latentsync"],
                "--audio", audio, "--out-dir", out, "--request-option", f"reference_video_file={video}",
                "--session-option", f"latentsync.mem_saver={str(saver).lower()}", "--request-option",
                "frames_per_chunk=8", "--request-option", "cache_interval=3", "--request-option",
                "seed=1247", "--request-option", "num_inference_steps=20"], stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, text=True)
            elapsed = time.monotonic() - start
            if proc.returncode:
                raise SystemExit(proc.stderr[-4000:])
            meta = json.loads((out / "latentsync_video.json").read_text())
            raw = out / "latentsync_video_rgb24.rgb"
            if (meta["fps"] != FPS or meta["frames"] < 32 or
                    raw.stat().st_size != meta["width"] * meta["height"] * 3 * meta["frames"]):
                raise SystemExit("模型输出的帧率、帧数或长度异常。")
            peak = next((line.split()[0] for line in proc.stderr.splitlines()
                         if "peak memory footprint" in line), None)
            memory = f"，进程峰值 {int(peak) / 1024**3:.2f} GiB" if peak else ""
            print(f"{mode}：{elapsed:.1f} 秒，{32 / elapsed:.4f} 帧/秒{memory}", flush=True)


if __name__ == "__main__":
    main()
