#!/bin/sh
# Local operations for the talking-head studio.
set -eu
cd "$(dirname "$0")"
if [ "${1:-}" = dev ]; then shift; fi
if [ "${1:-help}" = help ]; then set -- --help; fi
# Bootstrap init even when macOS only exposes its developer-tools python3 stub.
if [ "${1:-}" = init ] && [ ! -x .venv/bin/python ] &&
    ! command -v python3.12 >/dev/null 2>&1 && command -v brew >/dev/null 2>&1 &&
    [ "$(uname -sm)" = "Darwin arm64" ]; then
    python_prefix=$(brew --prefix python@3.12)
    if [ ! -x "$python_prefix/bin/python3.12" ]; then
        brew install python@3.12
    fi
    export PATH="$python_prefix/bin:$PATH"
fi
for python in ./.venv/bin/python python3.12 python3; do
    if command -v "$python" >/dev/null 2>&1; then
        exec "$python" tools/studio_service.py "$@"
    fi
done
echo "未找到 Python 3。请先安装 Python 3.12，再运行 ./optools.sh init。" >&2
exit 1
