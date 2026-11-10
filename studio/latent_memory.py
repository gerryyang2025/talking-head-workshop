"""Choose LatentSync's CFG execution mode from current macOS memory headroom."""
import re
import subprocess
import sys


GIB = 1024 ** 3
# Admission thresholds, not a reservation. Leave room for the OS, Metal graphs,
# frame buffers, and other apps. Never change the system's Metal memory limit.
MIN_TOTAL = 32 * GIB
MIN_AVAILABLE = 12 * GIB


def available_bytes(vm_stat):
    """Conservative estimate: don't count compressed or all inactive memory."""
    match = re.search(r"page size of (\d+) bytes", vm_stat)
    if not match:
        raise ValueError("missing page size")
    page_size = int(match[1])
    pages = {key: int(value) for key, value in
             re.findall(r"^([^:\n]+):\s*(\d+)\.", vm_stat, re.MULTILINE)}
    # Cap reclaimable pages at file-backed pages; the inactive queue can also
    # contain anonymous data that would have to be written to swap.
    reclaimable = min(pages["Pages inactive"], pages["File-backed pages"])
    if page_size <= 0:
        raise ValueError("invalid page size")
    return (pages["Pages free"] + reclaimable) * page_size


def _read(*command):
    return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL, timeout=2)


def memory_mode():
    """Return (mem_saver, explanation). Probe failures must never fail an export."""
    if sys.platform == "darwin":
        try:
            total, pressure = map(int, _read("/usr/sbin/sysctl", "-n", "hw.memsize",
                                            "kern.memorystatus_vm_pressure_level").split())
            if pressure in (2, 4):
                return True, "系统内存压力偏高"
            if pressure != 1 or total <= 0:
                return True, "无法确认内存压力"
            if total < MIN_TOTAL:
                return True, "物理内存不足 32 GiB"
            available = available_bytes(_read("/usr/bin/vm_stat"))
            if available < MIN_AVAILABLE:
                return True, f"预计可用 {available / GIB:.1f} GiB"
            return False, f"预计可用 {available / GIB:.1f} GiB"
        except (OSError, subprocess.SubprocessError, KeyError, ValueError):
            pass
    return True, "无法读取本机内存余量"
