"""Local Qwen3-TTS worker, run in its own MLX-Audio environment."""

import json
import math
import os
from pathlib import Path
import sys
import wave


def synthesize(request, folder):
    import mlx.core as mx
    import numpy as np
    from mlx_audio.tts.utils import load_model

    model = load_model(request["model"])
    if (model.tokenizer is None or model.speech_tokenizer is None
            or not model.speech_tokenizer.has_encoder or model.speaker_encoder is None):
        raise ValueError("个人音色模型或语音分词器不完整，请重新运行个人音色安装步骤")
    with wave.open(request["reference"], "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, model.sample_rate):
            raise ValueError("参考录音格式无效，请重新导入")
        reference = mx.array(np.frombuffer(wav.readframes(wav.getnframes()), "<i2").astype("float32") / 32768)
    remaining = request["maxSeconds"]
    for index, line in enumerate(request["lines"]):
        # This codec generates one frame per 1,920 samples. Keep one second of
        # headroom so an overlength utterance is rejected instead of cut short.
        limit = max(1, math.ceil((remaining + 1) * model.sample_rate / 1920))
        segments = list(model.generate(text=line, ref_audio=reference, ref_text=request["transcript"],
                                       max_tokens=limit))
        if not segments:
            raise ValueError(f"第 {index + 1} 句未合成有效声音")
        audio, = segments
        pcm = np.asarray(audio.audio, dtype="float32").reshape(-1)
        if not pcm.size or not np.isfinite(pcm).all() or np.max(np.abs(pcm)) < 0.0001:
            raise ValueError(f"第 {index + 1} 句未合成有效声音")
        if audio.token_count >= limit:
            raise ValueError(f"第 {index + 1} 句在剩余 {remaining:.1f} 秒的配音时长内未能读完。请核对参考录音与逐字稿，或将文案分段。")
        remaining -= pcm.size / audio.sample_rate + request["pause"]
        if remaining < -1e-6:
            raise ValueError(f"读到第 {index + 1} 句时，实际配音已超过 {request['maxSeconds']} 秒，请分段制作")
        with wave.open(str(folder / f"{index}.wav"), "wb") as wav:
            wav.setparams((1, 2, audio.sample_rate, 0, "NONE", "not compressed"))
            wav.writeframes(np.rint(np.clip(pcm, -1, 1) * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    os.environ.update(HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
    synthesize(json.load(sys.stdin), Path(sys.argv[1]))
