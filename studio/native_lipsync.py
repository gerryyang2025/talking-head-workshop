"""Run the pinned audio.cpp portrait and video models on Apple Silicon."""
import io
import json
import math
import os
import signal
import subprocess
import tempfile
import wave
from pathlib import Path

import cv2 as cv
import numpy as np

from .latent_memory import memory_mode
from .media import FPS, MODELS, ff
from .setup_models import NATIVE_CLI, NATIVE_WEIGHTS


LATENTSYNC_BATCH = 96


class NativeMemoryError(ValueError):
    """The native backend explicitly reported a memory allocation failure."""


def allocation_error(text):
    text = text.lower()
    return any(marker in text for marker in (
        "out of memory", "outofmemory", "bad_alloc", "failed to allocate",
        "could not allocate", "cannot allocate memory",
        "insufficient memory", "not enough memory",
    ))


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
        self.legacy_memory = False
        self.allocation_failed = False

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
                "--request-option", f"frames_per_chunk={min(8, length)}",
                "--request-option", "cache_interval=3"]

    def generate(self, folder, audio, options, detail, check_cancel):
        cmd = [MODELS / NATIVE_CLI, "--family", self.model, "--task", "gen",
               "--backend", "metal", "--model", MODELS / NATIVE_WEIGHTS[self.model],
               "--audio", audio, "--out-dir", folder, *options]
        log = folder / "engine.log"
        if self.model == "latentsync":
            cmd.extend(["--log-file", log])
        phases = {"latentsync.detector.wall_ms": "定位人脸",
                  "latentsync.vae_encoder.wall_ms": "编码画面",
                  "latentsync.vae_decoder.wall_ms": "解码画面"}
        with log.open("w+") as events, tempfile.TemporaryFile() as errors:
            check_cancel()
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=errors, start_new_session=True)
            evaluations = 0
            previous = ""
            try:
                while process.poll() is None:
                    check_cancel()
                    try:
                        process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        pass
                    phase = previous
                    for line in events:
                        fields = line.split()
                        if len(fields) >= 4 and fields[0] == "[TIMING":
                            key = fields[-2]
                            if key == "latentsync.unet.wall_ms":
                                evaluations += 1
                                phase = f"去噪运算 {evaluations} 次"
                            elif key in phases:
                                phase = phases[key]
                    if phase != previous:
                        detail(phase)
                        previous = phase
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
            check_cancel()
            if process.returncode:
                errors.seek(max(0, errors.tell() - 8192))
                lines = errors.read().decode(errors="replace").strip().splitlines()
                reason = next((line for line in reversed(lines) if "failed:" in line),
                              lines[-1] if lines else f"退出码 {process.returncode}")
                # ggml may put the allocator diagnostic before the final generic
                # error or in its native log instead of stderr.
                with log.open("rb") as trace:
                    trace.seek(max(0, log.stat().st_size - 8192))
                    diagnostic = trace.read().decode(errors="replace")
                error = NativeMemoryError if allocation_error("\n".join(lines) + diagnostic) else ValueError
                raise error(f"{self.model} 本机推理失败：{reason}")

    def generate_batch(self, folder, audio, options, detail, check_cancel):
        if self.model != "latentsync":
            return self.generate(folder, audio, options, detail, check_cancel)
        if self.legacy_memory or self.allocation_failed:
            saver, reason = True, "继续原批次" if self.legacy_memory else "本轮曾出现内存分配失败"
        else:
            saver, reason = memory_mode()

        def run(saver, reason):
            mode = "节省内存" if saver else "双路合批"
            label = f"{mode}（{reason}）"
            detail(label)
            self.generate(folder, audio, [*options, "--session-option",
                          f"latentsync.mem_saver={str(saver).lower()}"],
                          lambda phase: detail(f"{label} · {phase}"), check_cancel)

        try:
            run(saver, reason)
        except NativeMemoryError:
            if saver:
                raise
            # Keep the exact prepared WAV/MP4, seed and temporal window. Only
            # retry this uncommitted batch; do not retry a cancellation or face error.
            check_cancel()
            self.allocation_failed = True
            for name in ("latentsync_video.json", "latentsync_video_rgb24.rgb"):
                (folder / name).unlink(missing_ok=True)
            run(True, "内存分配失败，重试本批")

    def render_checkpointed(self, source, first, count, output, encoder, report, check_cancel, folder):
        # LatentSync batches have independent audio and source frames. Publish each
        # encoded batch only after FFmpeg closes it, then concatenate without re-encoding.
        folder.mkdir(parents=True, exist_ok=True)
        source_start = source.pos
        reused = 0
        filenames = []
        for offset in range(0, count, LATENTSYNC_BATCH):
            check_cancel()
            length = min(LATENTSYNC_BATCH, count - offset)
            chunk = folder / f"{offset}.mp4"
            filenames.append(chunk.name)
            if chunk.is_file():
                reused += length
                report(offset + length, "已复用本批", reused)
                continue
            source.pos = source_start + offset
            tmp = output.with_name("batch.mp4")

            def batch_progress(done, detail):
                # Commit first so a completed batch reported in the UI can be resumed.
                if done < length:
                    report(offset + done, detail, reused)

            self.render(source, first + offset, length, tmp, encoder, batch_progress, check_cancel,
                        frame_offset=offset)
            tmp.replace(chunk)
            report(offset + length, "本批已保存", reused)
        check_cancel()
        manifest = folder / "list.txt"
        manifest.write_text("".join(f"file '{name}'\n" for name in filenames))
        ff("-f", "concat", "-i", manifest, "-c", "copy", "-movflags", "+faststart", output)
        return reused

    def render(self, source, first, count, output, encoder, report, check_cancel, *, frame_offset=0):
        frame = source.next()
        size = frame.shape[1::-1]
        # Both runtimes collect raw output before returning. Bound peak memory for
        # long takes. FlashHead continues from its last generated portrait.
        limit = 192 if self.model == "soulx_flashhead" else LATENTSYNC_BATCH
        with encoder(output, size) as sink:
            for offset in range(0, count, limit):
                check_cancel()
                length = min(count - offset, limit)
                batch = f"本段第 {frame_offset + offset + 1}–{frame_offset + offset + length} 帧"
                report(offset, batch)
                with tempfile.TemporaryDirectory(dir=output.parent) as work:
                    folder = Path(work)
                    audio = folder / "speech.wav"
                    write_audio(audio, self.samples, first + offset, length)
                    options = self.request_options(folder, frame, source, offset, length, size, encoder)
                    self.generate_batch(folder, audio, options,
                                        lambda phase: report(offset, f"{batch} · {phase}"), check_cancel)
                    frames = output_frames(self.model, folder)
                    try:
                        for _ in range(length):
                            check_cancel()
                            generated = next(frames, None)
                            if generated is None:
                                raise ValueError("模型输出帧数少于配音所需帧数")
                            frame = cv.resize(generated, size) if generated.shape[1::-1] != size else generated
                            sink.write(frame.tobytes())
                    except (OSError, KeyError, TypeError) as exc:
                        raise ValueError(f"{self.model} 输出无法解码：{exc}") from exc
                    finally:
                        frames.close()
                    report(offset + length, "本批完成")
