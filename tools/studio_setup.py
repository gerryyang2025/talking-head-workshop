"""Install the local studio runtime. Called by optools before importing the web app."""
import os
from pathlib import Path
import platform
import shutil
import subprocess

from check_environment import ffmpeg_errors


ROOT = Path(__file__).resolve().parents[1]


def brew_bin(formula, executable):
    brew = shutil.which("brew")
    if not brew:
        raise RuntimeError(f"缺少 {executable}，请先安装 Homebrew 或手动安装 {formula}，再重试。")
    prefix = subprocess.check_output([brew, "--prefix", formula], text=True).strip()
    binary = Path(prefix) / "bin" / executable
    if not os.access(binary, os.X_OK):
        subprocess.run([brew, "install", formula], check=True)
    return binary


def environment(folder):
    python = folder / "bin/python"
    if not python.is_file():
        if folder.exists() and not (folder / "pyvenv.cfg").is_file():
            raise RuntimeError(f"{folder} 已存在且不是虚拟环境，请检查此目录。")
        base = shutil.which("python3.12") or brew_bin("python@3.12", "python3.12")
        subprocess.run([base, "-m", "venv", folder], check=True)
    subprocess.run([python, "-c", "import sys; sys.exit(0 if sys.prefix != sys.base_prefix "
                    "and sys.version_info[:2] == (3, 12) else '请使用 Python 3.12 创建工程虚拟环境')"],
                   check=True)
    if not (folder / "bin/pip").is_file():
        subprocess.run([python, "-m", "ensurepip", "--default-pip"], check=True)
    return python


def configure_ffmpeg(python):
    directories = [python.parent]
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        directories.append(Path(system_ffmpeg).parent)
    for directory in directories:
        ffmpeg, ffprobe = directory / "ffmpeg", directory / "ffprobe"
        if os.access(ffprobe, os.X_OK) and os.access(ffmpeg, os.X_OK) and not ffmpeg_errors(ffmpeg):
            break
    else:
        ffmpeg = brew_bin("ffmpeg-full", "ffmpeg")
        ffprobe = ffmpeg.with_name("ffprobe")

    for binary in (ffmpeg, ffprobe):
        link = python.parent / binary.name
        if link == binary or (link.exists() and link.samefile(binary)):
            continue
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            raise RuntimeError(f"请检查项目内已有的 {link}，它缺少工作台需要的功能。")
        link.symlink_to(binary)
    env = dict(os.environ, PATH=str(python.parent) + os.pathsep + os.environ.get("PATH", ""))
    subprocess.run([python, "tools/check_environment.py", "--render"], cwd=ROOT, env=env, check=True)


def install(python, requirements):
    subprocess.run([python, "-m", "pip", "--disable-pip-version-check", "install", "-r",
                    ROOT / "studio" / requirements], check=True)


def initialize():
    if (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        raise RuntimeError("本地模型需要 Apple Silicon Mac 和原生 arm64 终端。")

    python = environment(ROOT / ".venv")
    configure_ffmpeg(python)
    install(python, "web-requirements.txt")
    subprocess.run([python, "-c", "from studio.__main__ import app"], cwd=ROOT, check=True)
    ensure_musetalk(python)
    voice_python = environment(ROOT / "build/voice-env")
    install(voice_python, "voice-requirements.txt")
    subprocess.run([voice_python, "-c", "from mlx_audio.tts.utils import load_model"], check=True)
    subprocess.run([voice_python, "-m", "pip", "check"], check=True)
    subprocess.run([python, "-m", "studio.setup_models"], cwd=ROOT, check=True)
    subprocess.run([python, "-m", "pip", "check"], check=True)
    print("环境已就绪。运行 ./optools.sh start 启动工作台。")


def ensure_musetalk(python):
    # pip fetches direct URL requirements even when already satisfied. Record the
    # installed pin only after the engine imports successfully.
    pin = (ROOT / "studio/requirements.txt").read_text()
    receipt = python.parent.parent / ".studio-musetalk-requirement"
    probe = [python, "-c", "from musetalk_mlx.pipeline_mlx import MuseTalkPipeline; "
             "from studio.edtalk import EDTalkEngine"]
    if receipt.is_file() and receipt.read_text() == pin:
        healthy = subprocess.run([python, "-m", "pip", "check"], stdout=subprocess.DEVNULL)
        if healthy.returncode == 0 and subprocess.run(probe, cwd=ROOT).returncode == 0:
            return
    install(python, "requirements.txt")
    subprocess.run(probe, cwd=ROOT, check=True)
    receipt.write_text(pin)
