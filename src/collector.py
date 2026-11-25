"""Collecte des métriques système et matérielles."""

import socket
import time
from datetime import datetime, timezone
from typing import Any

import psutil


def collect_host_metrics() -> dict[str, Any]:
    """Collecte les métriques principales de la machine.

    Returns:
        dict: Métriques CPU, mémoire et Swap.
    """
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    cpu_times = psutil.cpu_times_percent(interval=1)

    load_1m, load_5m, load_15m = psutil.getloadavg()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "cpu_pct": psutil.cpu_percent(),
        "cpu_per_core": psutil.cpu_percent(percpu=True),
        "cpu_user": cpu_times.user,
        "cpu_system": cpu_times.system,
        "cpu_iowait": getattr(cpu_times, "iowait", None),
        "load_1m": load_1m,
        "load_5m": load_5m,
        "load_15m": load_15m,
        "ram_total_mb": memory.total / 1024**2,
        "ram_used_mb": memory.used / 1024**2,
        "ram_available_mb": memory.available / 1024**2,
        "ram_cached_mb": getattr(memory, "cached", 0) / 1024**2,
        "ram_buffers_mb": getattr(memory, "buffers", 0) / 1024**2,
        "ram_pct": memory.percent,
        "swap_pct": swap.percent
    }


def collect_disk_metrics() -> list[dict[str, Any]]:
    """Collecte les informations des partitions montées.

    Returns:
        list: Métriques des partitions accessibles.
    """
    disks = []

    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)

            disks.append({
                "mountpoint": partition.mountpoint,
                "total_gb": usage.total / 1024**3,
                "used_gb": usage.used / 1024**3,
                "usage_pct": usage.percent
            })

        except OSError:
            continue

    return disks


def collect_disk_io(interval: float = 1.0) -> dict[str, Any]:
    """Mesure les débits disque et les IOPS."""
    before = psutil.disk_io_counters()
    start = time.monotonic()

    time.sleep(interval)

    after = psutil.disk_io_counters()
    elapsed = time.monotonic() - start

    if before is None or after is None:
        return {
            "disk_read_mb_s": None,
            "disk_write_mb_s": None,
            "read_iops": None,
            "write_iops": None
        }

    return {
        "disk_read_mb_s": max(
            0, after.read_bytes - before.read_bytes
        ) / elapsed / 1024**2,
        "disk_write_mb_s": max(
            0, after.write_bytes - before.write_bytes
        ) / elapsed / 1024**2,
        "read_iops": max(
            0, after.read_count - before.read_count
        ) / elapsed,
        "write_iops": max(
            0, after.write_count - before.write_count
        ) / elapsed
    }