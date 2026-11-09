"""Check local dependencies without calling any model or remote service."""
import argparse
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys


def ffmpeg_errors(binary):
    errors = []
    filters = subprocess.run([binary, "-hide_banner", "-filters"], capture_output=True, text=True, check=True).stdout
    encoders = subprocess.run([binary, "-hide_banner", "-encoders"], capture_output=True, text=True, check=True).stdout
    for feature in ("drawtext", "subtitles"):
        if not any(line.split()[1:2] == [feature] for line in filters.splitlines()):
            errors.append("FFmpeg is missing the " + feature + " filter")
    if "libx264" not in encoders:
        errors.append("FFmpeg is missing the libx264 encoder")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true", help="also require FFmpeg filters, encoder and CJK font")
    args = parser.parse_args()
    errors = []
    if sys.version_info < (3, 10):
        errors.append("Python 3.10+ is required")
    print("Python:", sys.version.split()[0])
    print("NumPy (optional for slicing):", "available" if importlib.util.find_spec("numpy") else "not installed")
    if args.render:
        for binary in ("ffmpeg", "ffprobe"):
            if not shutil.which(binary):
                errors.append(binary + " is not on PATH")
        if shutil.which("ffmpeg"):
            errors.extend(ffmpeg_errors("ffmpeg"))
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from istream.render import FONT
        if not FONT:
            errors.append("CJK font missing; install Noto CJK or set ISTREAM_FONT")
        else:
            print("CJK font:", FONT)
    for error in errors:
        print("ERROR:", error, file=sys.stderr)
    if errors:
        print("On macOS use ffmpeg-full and its bin directory on PATH; see README.md.", file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
