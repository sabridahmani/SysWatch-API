"""Tests unitaires du collecteur système."""

from types import SimpleNamespace

import pytest

from src.collector import (
    collect_host_metrics,
    collect_disk_metrics,
    collect_disk_io
)


def test_host_metrics():
    """Vérifie la collecte CPU et RAM."""
    metrics = collect_host_metrics()

    assert 0 <= metrics["cpu_pct"] <= 100
    assert 0 <= metrics["ram_pct"] <= 100
    assert 0 <= metrics["swap_pct"] <= 100
    assert metrics["ram_total_mb"] > 0
    assert metrics["hostname"]
    assert metrics["timestamp"]


def test_disk_metrics():
    """Vérifie les métriques des partitions."""
    disks = collect_disk_metrics()

    assert isinstance(disks, list)
    assert len(disks) > 0

    for disk in disks:
        assert disk["total_gb"] > 0
        assert 0 <= disk["usage_pct"] <= 100
        assert disk["used_gb"] <= disk["total_gb"]


def test_disk_io(monkeypatch):
    """Vérifie les calculs de débit et des IOPS."""
    counters = iter([
        SimpleNamespace(
            read_bytes=0,
            write_bytes=0,
            read_count=0,
            write_count=0
        ),
        SimpleNamespace(
            read_bytes=2 * 1024**2,
            write_bytes=4 * 1024**2,
            read_count=100,
            write_count=200
        )
    ])

    timestamps = iter([0.0, 2.0])

    monkeypatch.setattr(
        "src.collector.psutil.disk_io_counters",
        lambda: next(counters)
    )

    monkeypatch.setattr(
        "src.collector.time.monotonic",
        lambda: next(timestamps)
    )

    monkeypatch.setattr(
        "src.collector.time.sleep",
        lambda _: None
    )

    metrics = collect_disk_io()

    assert metrics["disk_read_mb_s"] == pytest.approx(1)
    assert metrics["disk_write_mb_s"] == pytest.approx(2)
    assert metrics["read_iops"] == pytest.approx(50)
    assert metrics["write_iops"] == pytest.approx(100)