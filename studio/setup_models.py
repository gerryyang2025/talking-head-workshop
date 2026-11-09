"""Download and verify the local lip-sync and personal voice models."""

import argparse
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from urllib.request import urlopen

BASE = Path(__file__).resolve().parents[1] / "build/models"
MUSE = "https://huggingface.co/mlx-community/MuseTalk-1.5-fp16/resolve/ad54104a0129121fe2ea67471250c0656c985284/"
WEIGHTS = {
    "musetalk-1.5-fp16/config.json": (
        MUSE + "config.json",
        "527702bfd2111adab8b4713d4f70d920a479b5816cbb373731e791f6e3bd47d5",
    ),
    "musetalk-1.5-fp16/unet.safetensors": (
        MUSE + "unet.safetensors",
        "12d1e2f496bc91e4db8c989cffa8aa94b3d6a7098ab9d80ba92a1f38cce362f2",
    ),
    "musetalk-1.5-fp16/vae.safetensors": (
        MUSE + "vae.safetensors",
        "2a7670782dbe0ab66c40833dfd431b193375f0bdfc7c2daf76f5bc4e59070f98",
    ),
    "musetalk-1.5-fp16/whisper_encoder.safetensors": (
        MUSE + "whisper_encoder.safetensors",
        "c04baf7220bbc73393eeba74b6224398ce56caad60e4e0a0f4c28af3180836d3",
    ),
    "studio/yunet.onnx": (
        "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx",
        "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
    ),
    "studio/2dfan4.onnx": (
        "https://huggingface.co/facefusion/models-3.0.0/resolve/main/2dfan4.onnx",
        "678c6fa539d52335a31c980feefdf4a6e02d781d83dce00af8a894f114557285",
    ),
}

VOICE_REVISION = "0d6bb6fe33f92d47a507e23b9148940e8366ab5b"
VOICE_FOLDER = "qwen3-tts-0.6b-base-4bit"
VOICE_URL = f"https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-4bit/resolve/{VOICE_REVISION}/"
VOICE_HASHES = {
    "config.json": "ba59b8d2d47746e844f6a96e2232a969d8d89dcc34450fbad94d912bb9ee2e27",
    "generation_config.json": "f1b90b4513f3b34c62851049e2492d7b4c5940daf1276f89c82b8ef04127f3aa",
    "merges.txt": "599bab54075088774b1733fde865d5bd747cbcc7a547c5bc12610e874e26f5e3",
    "model.safetensors": "07dcb37b323614af64624af687876edd5c9a8b442da2a7b549d62f9ba2770ec1",
    "model.safetensors.index.json": "86f65f69204f3fb9dc5ec22ed94da4865594c901b45d2508c60a5931d12787d4",
    "preprocessor_config.json": "efdde1022ea9d76928bf7a9cd53139138f5ba2e466e837f08f6105ab1af1c119",
    "speech_tokenizer/config.json": "ee65bb901c876664ab8707c487157aa1a6ee57c65969b28fb5ec9dc211e68167",
    "speech_tokenizer/configuration.json": "6bc26d64eb5024b4d1dab5a52371958b429256d6c9d59787f1f5294a54e0cebd",
    "speech_tokenizer/model.safetensors": "836b7b357f5ea43e889936a3709af68dfe3751881acefe4ecf0dbd30ba571258",
    "speech_tokenizer/preprocessor_config.json": "fcb3805e597e786d4067706e602f6688524640f8d3396790e2e09b5942fcbdfb",
    "tokenizer_config.json": "dc3c31c3bdaedd5016382bb3cbe07323026775ad51f5a4fb564505992ae4a670",
    "vocab.json": "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910",
}


def checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    weights = {
        **WEIGHTS,
        **{f"{VOICE_FOLDER}/{name}": (VOICE_URL + name, digest) for name, digest in VOICE_HASHES.items()},
    }
    for name, (url, expected) in weights.items():
        path = BASE / name
        if path.is_file() and checksum(path) == expected:
            print("已校验", name)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as out:
            tmp = Path(out.name)
        try:
            print("下载", name, flush=True)
            with urlopen(url, timeout=90) as src, tmp.open("wb") as out:
                shutil.copyfileobj(src, out)
            if checksum(tmp) != expected:
                raise ValueError(f"{name} 校验失败")
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    main()
