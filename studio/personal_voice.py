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
        raise ValueError("个人音色模型或语音分词器不完整，请在工程目录运行 ./optools.sh init 补齐")
    with wave.open(request["reference"], "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, model.sample_rate):
            raise ValueError("参考录音格式无效，请重新导入")
        reference = mx.array(np.frombuffer(wav.readframes(wav.getnframes()), "<i2").astype("float32") / 32768)
    remaining = request["maxSeconds"]
    for index, line in enumerate(request["lines"]):
        # Keep short lines bounded if the model repeats. Allow longer lines more
        # room, up to the remaining project budget plus one second to detect overflow.
        line_seconds = max(120, len(line))
        limit = max(1, math.ceil((min(remaining, line_seconds) + 1) * model.sample_rate / 1920))
        segments = list(model.generate(text=line, ref_audio=reference, ref_text=request["transcript"],
                                       max_tokens=limit))
        if not segments:
            raise ValueError(f"第 {index + 1} 句未合成有效声音")
        audio, = segments
        pcm = np.asarray(audio.audio, dtype="float32").reshape(-1)
        if not pcm.size or not np.isfinite(pcm).all() or np.max(np.abs(pcm)) < 0.0001:
            raise ValueError(f"第 {index + 1} 句未合成有效声音")
        duration = pcm.size / audio.sample_rate + request["pause"]
        if duration > remaining + 1e-6 or (audio.token_count >= limit and remaining <= line_seconds):
            raise ValueError(f"第 {index + 1} 句无法在整篇配音的 {request['maxSeconds']} 秒上限内读完，请拆分文案后分别生成。")
        if audio.token_count >= limit:
            raise ValueError(f"第 {index + 1} 句合成达到单句生成上限，请将这句话拆成两个短句后重新生成。")
        remaining -= duration
        with wave.open(str(folder / f"{index}.wav"), "wb") as wav:
            wav.setparams((1, 2, audio.sample_rate, 0, "NONE", "not compressed"))
            wav.writeframes(np.rint(np.clip(pcm, -1, 1) * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    os.environ.update(HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
    synthesize(json.load(sys.stdin), Path(sys.argv[1]))
