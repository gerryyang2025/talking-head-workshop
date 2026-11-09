"""Run the pinned audio.cpp portrait and video models on Apple Silicon."""
import io
import json
import math
import subprocess
import tempfile
import wave
from pathlib import Path

import cv2 as cv
import numpy as np

from .media import FPS, MODELS
from .setup_models import NATIVE_CLI, NATIVE_WEIGHTS


def write_audio(path, samples, first, count):
    per_frame = 16000 // FPS
    start, stop = first * per_frame, (first + count) * per_frame
    pcm = np.zeros(count * per_frame, dtype="<i2")
    lo, hi = max(start, 0), min(stop, len(samples))
    if lo < hi:
        pcm[lo - start:hi - start] = np.rint(np.clip(samples[lo:hi], -1, 1) * 32767)
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        wav.writeframes(pcm.tobytes())


def rgb_frames(stream, meta, nbytes):
    w, h, frames = (int(meta[key]) for key in ("width", "height", "frames"))
    stride = w * h * 3
    if (min(w, h, frames) < 1 or int(meta["fps"]) != FPS or meta["format"] != "rgb24"
            or frames * stride != nbytes):
        raise ValueError("模型输出的视频尺寸、帧率或数据长度异常")
    for _ in range(frames):
        raw = stream.read(stride)
        if len(raw) != stride:
            raise ValueError("模型输出的视频帧不完整")
        yield cv.cvtColor(np.frombuffer(raw, np.uint8).reshape(h, w, 3), cv.COLOR_RGB2BGR)


def output_frames(model, folder):
    if model == "latentsync":
        meta = json.loads((folder / "latentsync_video.json").read_text())
        path = folder / "latentsync_video_rgb24.rgb"
        with path.open("rb") as stream:
            yield from rgb_frames(stream, meta, path.stat().st_size)
    else:
        files = sorted(folder.glob("soulx_flashhead_video_*.json"),
                       key=lambda p: int(p.stem.rsplit("_", 1)[1]))
        for index, path in enumerate(files):
            chunk = json.loads(path.read_text())
            if int(chunk["meta"]["chunk_index"]) != index:
                raise ValueError("SoulX 输出缺少连续视频片段")
            payload = bytes.fromhex(chunk["payload_hex"])
            yield from rgb_frames(io.BytesIO(payload), chunk["meta"], len(payload))


class NativeLipEngine:
    def __init__(self, model, samples):
        self.model = model
        self.samples = samples

    def request_options(self, folder, frame, source, offset, length, size, encoder):
        if self.model == "soulx_flashhead":
            reference = folder / "portrait.png"
            # Retain the model's 512-square pixel budget in wide and vertical shots.
            scale = min(512 / math.sqrt(size[0] * size[1]), 768 / max(size))
            w, h = (max(32, round(side * scale / 32) * 32) for side in size)
            if not cv.imwrite(str(reference), cv.resize(frame, (w, h))):
                raise ValueError("无法准备 SoulX 参考照片")
            return ["--request-option", f"reference_image_file={reference}",
                    "--request-option", f"width={w}", "--request-option", f"height={h}"]

        reference = folder / "reference.mp4"
        with encoder(reference, size) as video:
            for i in range(length):
                original = frame if offset == 0 and i == 0 else source.next()
                video.write(original.tobytes())
        return ["--request-option", f"reference_video_file={reference}",
                "--session-option", "latentsync.mem_saver=true",
                "--request-option", f"frames_per_chunk={min(8, length)}",
                "--request-option", "cache_interval=3"]

    def generate(self, folder, audio, options):
        cmd = [MODELS / NATIVE_CLI, "--family", self.model, "--task", "gen",
               "--backend", "metal", "--model", MODELS / NATIVE_WEIGHTS[self.model],
               "--audio", audio, "--out-dir", folder, *options]
        run = subprocess.run(cmd, capture_output=True)
        if run.returncode:
            lines = run.stderr.decode(errors="replace").strip().splitlines()
            reason = next((line for line in reversed(lines) if "failed:" in line),
                          lines[-1] if lines else f"退出码 {run.returncode}")
            raise ValueError(f"{self.model} 本机推理失败：{reason}")

    def render(self, source, first, count, output, encoder):
        frame = source.next()
        size = frame.shape[1::-1]
        # Both runtimes collect raw output before returning. Bound peak memory for
        # long takes. FlashHead continues from its last generated portrait.
        limit = 192 if self.model == "soulx_flashhead" else 96
        with encoder(output, size) as sink:
            for offset in range(0, count, limit):
                length = min(count - offset, limit)
                with tempfile.TemporaryDirectory(dir=output.parent) as work:
                    folder = Path(work)
                    audio = folder / "speech.wav"
                    write_audio(audio, self.samples, first + offset, length)
                    options = self.request_options(folder, frame, source, offset, length, size, encoder)
                    self.generate(folder, audio, options)
                    frames = output_frames(self.model, folder)
                    try:
                        for _ in range(length):
                            generated = next(frames, None)
                            if generated is None:
                                raise ValueError("模型输出帧数少于配音所需帧数")
                            frame = cv.resize(generated, size) if generated.shape[1::-1] != size else generated
                            sink.write(frame.tobytes())
                    except (OSError, KeyError, TypeError) as exc:
                        raise ValueError(f"{self.model} 输出无法解码：{exc}") from exc
                    finally:
                        frames.close()
