"""Supervision des processus actifs."""

from typing import Any

import psutil


def collect_processes(
    targets: list[str]
) -> list[dict[str, Any]]:
    """Collecte les processus surveillés et les plus gourmands.

    Args:
        targets: Noms des processus à surveiller.

    Returns:
        list: Métriques des processus sélectionnés.
    """
    processes = []

    for proc in psutil.process_iter():
        try:
            with proc.oneshot():
                name = proc.name()

                if hasattr(proc, "num_handles"):
                    open_files = proc.num_handles()
                else:
                    open_files = proc.num_fds()

                processes.append({
                    "pid": proc.pid,
                    "name": name,
                    "status": proc.status(),
                    "cpu_pct": proc.cpu_percent(),
                    "rss_mb": proc.memory_info().rss / 1024**2,
                    "num_threads": proc.num_threads(),
                    "open_files": open_files
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    monitored = [
        p for p in processes
        if any(
            target.lower() in p["name"].lower()
            for target in targets
        )
    ]

    top_cpu = sorted(
        processes,
        key=lambda p: p["cpu_pct"],
        reverse=True
    )[:5]

    top_ram = sorted(
        processes,
        key=lambda p: p["rss_mb"],
        reverse=True
    )[:5]

    unique = {
        p["pid"]: p
        for p in monitored + top_cpu + top_ram
    }

    return list(unique.values())