"""Populate the optional Apple Silicon inference cache from pinned or checksummed public weights."""

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


def checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    for name, (url, expected) in WEIGHTS.items():
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
    main()
