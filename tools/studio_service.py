"""Manage the local studio, including an instance started with python -m studio."""

import argparse
import fcntl
import http.client
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
STORE = Path(os.environ.get("KOUBO_STUDIO_DATA", ROOT / "build/studio")).resolve()
SERVICE_LOCK = STORE / "service.lock"
LOG = STORE / "service.log"
PYTHON = ROOT / ".venv/bin/python"
DEFAULT_PORT = 8765


def workspace_locked():
    with SERVICE_LOCK.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return False
        except BlockingIOError:
            return True


def current():
    # The studio holds this lock for its entire lifetime, including for manual starts.
    if not workspace_locked():
        return None

    pids = subprocess.run(
        ["lsof", "-t", str(SERVICE_LOCK)], capture_output=True, text=True
    ).stdout.split()
    if len(pids) == 1 and pids[0].isdigit():
        command = subprocess.run(
            ["ps", "-ww", "-p", pids[0], "-o", "command="], capture_output=True, text=True
        ).stdout
        studio = re.search(r"\s-m\s+studio(?:\s+--port(?:=|\s+)(\d+))?\s*$", command)
        if studio:
            return int(pids[0]), int(studio[1] or DEFAULT_PORT)
    if not workspace_locked():
        return None  # The process exited during discovery.
    raise RuntimeError("工作区已加锁，但无法确认工作台进程。请稍后重试。")


def url(port):
    return f"http://127.0.0.1:{port}/"


def ready(pid, port):
    # A different application can already be serving HTTP on the requested port.
    listener = subprocess.run(
        ["lsof", "-nP", "-a", "-p", str(pid), f"-iTCP@127.0.0.1:{port}", "-sTCP:LISTEN", "-t"],
        capture_output=True, text=True,
    )
    if listener.stdout.strip() != str(pid):
        return False
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
    try:
        conn.request("HEAD", "/")
        return conn.getresponse().status == 200
    except (OSError, http.client.HTTPException):
        return False
    finally:
        conn.close()


def start(port):
    with LOG.open("ab") as log:
        child = subprocess.Popen(
            [str(PYTHON), "-u", "-m", "studio", "--port", str(port)],
            cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    deadline = time.monotonic() + 60
    while child.poll() is None:
        if ready(child.pid, port):
            print(f"工作台已启动（PID {child.pid}） {url(port)}")
            return
        if time.monotonic() >= deadline:
            child.terminate()
            child.wait(timeout=10)
            raise RuntimeError(f"工作台启动超时。日志见 {LOG}")
        time.sleep(0.2)
    raise RuntimeError(f"工作台启动失败（退出码 {child.returncode}）。日志见 {LOG}")


def stop(pid):
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if not workspace_locked():
            print("工作台已停止。")
            return
        time.sleep(0.2)
    raise RuntimeError(f"工作台尚未停止（PID {pid}）。")


def main():
    parser = argparse.ArgumentParser(prog="./optools.sh", description="管理口播工坊的本地服务")
    commands = parser.add_subparsers(dest="action", required=True)
    init_help = "安装工作台运行依赖及全部口型、个人音色模型"
    init = commands.add_parser("init", help=init_help, description=init_help)
    init.add_argument("--web-only", action="store_true", help="仅配置网页运行环境，跳过本地推理引擎和模型")
    commands.add_parser("start", help="后台启动")
    commands.add_parser("stop", help="停止服务")
    commands.add_parser("restart", help="重启服务")
    commands.add_parser("status", help="查看状态和访问地址")
    logs = commands.add_parser("logs", help="查看最近 80 行后台日志")
    logs.add_argument("-f", "--follow", action="store_true", help="持续跟踪日志")
    args = parser.parse_args()

    if args.action == "logs":
        if not LOG.exists():
            print("暂无后台日志。通过 optools 启动后会写入", LOG)
            return 0
        os.execlp("tail", "tail", "-n", "80", *(["-f"] if args.follow else []), str(LOG))

    # The runtime is shared across all data stores in this checkout.
    lock_dir = ROOT / "build/studio" if args.action == "init" else STORE
    lock_dir.mkdir(parents=True, exist_ok=True)
    with (lock_dir / "optools.lock").open("a") as operations:
        fcntl.flock(operations, fcntl.LOCK_EX)
        if args.action == "init":
            from studio_setup import initialize

            initialize(web_only=args.web_only)
            return 0
        service = current()
        if args.action == "status" or (args.action == "start" and service):
            if not service:
                print("工作台已停止。")
                return 3
            pid, port = service
            if not ready(pid, port):
                raise RuntimeError(f"工作台进程存在（PID {pid}），网页尚未就绪。")
            print(f"工作台运行中（PID {pid}） {url(port)}")
            return 0

        if args.action in ("start", "restart"):
            if not os.access(PYTHON, os.X_OK):
                raise RuntimeError(f"缺少工程虚拟环境 {PYTHON}，请先运行 ./optools.sh init。")
            port = int(os.environ.get("KOUBO_STUDIO_PORT", service[1] if service else DEFAULT_PORT))
            if not 1 <= port <= 65535:
                raise ValueError("KOUBO_STUDIO_PORT 须为 1 至 65535 的整数。")
            if not service or port != service[1]:
                try:
                    with socket.create_server(("127.0.0.1", port)):
                        pass
                except OSError as exc:
                    raise RuntimeError(f"无法使用端口 {port}：{exc}") from exc
        if service:
            stop(service[0])
        if args.action == "stop":
            if not service:
                print("工作台已停止。")
        else:
            start(port)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        sys.exit(f"错误：{exc}")
