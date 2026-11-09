#!/bin/sh
# Local operations for the talking-head studio.
set -eu
cd "$(dirname "$0")"
if [ "${1:-}" = dev ]; then shift; fi
if [ "${1:-help}" = help ]; then set -- --help; fi
for python in python3 python3.12; do
    if command -v "$python" >/dev/null 2>&1; then
        exec "$python" tools/studio_service.py "$@"
    fi
done
echo "未找到 Python 3。请先安装 Python 3.12，再运行 ./optools.sh init。" >&2
exit 1
