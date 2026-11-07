#!/bin/sh
# Local operations for the talking-head studio.
set -eu
cd "$(dirname "$0")"
if [ "${1:-}" = dev ]; then shift; fi
if [ "${1:-help}" = help ]; then set -- --help; fi
exec python3 tools/studio_service.py "$@"
