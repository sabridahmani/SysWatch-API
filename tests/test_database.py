"""Tests unitaires de la base SQLite."""

import json
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from src import database


@pytest.fixture
def db(monkeypatch):
    """Crée une base SQLite temporaire en mémoire."""
    connect = sqlite3.connect

    keeper = connect(
        "file:test_syswatch?mode=memory&cache=shared",
        uri=True
    )

    monkeypatch.setattr(
        database.sqlite3,
        "connect",
        lambda *args, **kwargs: connect(
            "file:test_syswatch?mode=memory&cache=shared",
            uri=True
        )
    )

    database.init_database(":memory:")

    yield keeper

    keeper.close()


def test_create_tables(db):
    """Vérifie la création des cinq tables."""
    tables = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    names = {row[0] for row in tables}

    assert "host_metrics" in names
    assert "disk_partitions" in names
    assert "process_metrics" in names
    assert "service_health" in names
    assert "system_incidents" in names


def test_save_metrics(db):
    """Vérifie l'insertion des métriques."""
    host = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": "TEST-PC",
        "cpu_pct": 25,
        "cpu_per_core": [20, 30],
        "ram_pct": 40
    }

    disks = [{
        "mountpoint": "C:",
        "total_gb": 500,
        "used_gb": 200,
        "usage_pct": 40
    }]

    processes = [{
        "pid": 1234,
        "name": "python",
        "status": "running",
        "cpu_pct": 10,
        "rss_mb": 150,
        "num_threads": 4,
        "open_files": 5
    }]

    database.save_metrics(
        ":memory:", host, disks, processes
    )

    row = db.execute(
        "SELECT hostname, cpu_pct, cpu_per_core "
        "FROM host_metrics"
    ).fetchone()

    assert row[0] == "TEST-PC"
    assert row[1] == 25
    assert json.loads(row[2]) == [20, 30]

    assert db.execute(
        "SELECT COUNT(*) FROM disk_partitions"
    ).fetchone()[0] == 1

    assert db.execute(
        "SELECT COUNT(*) FROM process_metrics"
    ).fetchone()[0] == 1


def test_save_healthchecks_and_sla(db):
    """Vérifie les healthchecks et le calcul du SLA."""
    timestamp = datetime.now(timezone.utc).isoformat()

    results = [{
        "service_name": "Grafana",
        "url": "http://localhost:3000",
        "status_code": 200,
        "response_time_ms": 50,
        "is_healthy": True,
        "ssl_days_left": None,
        "error_msg": None
    }]

    database.save_healthchecks(
        ":memory:", timestamp, results
    )

    sla = database.calculate_sla(":memory:")

    assert len(sla) == 1
    assert sla[0]["service_name"] == "Grafana"
    assert sla[0]["sla_pct"] == 100

    results[0]["is_healthy"] = False
    results[0]["status_code"] = 503

    database.save_healthchecks(
        ":memory:", timestamp, results
    )

    sla = database.calculate_sla(":memory:")

    assert sla[0]["total_checks"] == 2
    assert sla[0]["successful_checks"] == 1
    assert sla[0]["sla_pct"] == 50


def test_save_incidents(db):
    """Vérifie l'enregistrement des incidents."""
    timestamp = datetime.now(timezone.utc).isoformat()

    incidents = [{
        "category": "CPU",
        "severity": "WARNING",
        "resource_name": "TEST-PC",
        "metric_value": 95,
        "threshold_value": 90,
        "description": "CPU excessif"
    }]

    database.save_incidents(
        ":memory:", timestamp, incidents
    )

    row = db.execute(
        "SELECT category, severity FROM system_incidents"
    ).fetchone()

    assert row == ("CPU", "WARNING")


def test_purge_old_data(db):
    """Vérifie la suppression des données anciennes."""
    old = (
        datetime.now(timezone.utc) - timedelta(days=10)
    ).isoformat()

    recent = datetime.now(timezone.utc).isoformat()

    with db:
        db.executemany(
            "INSERT INTO host_metrics (timestamp) VALUES (?)",
            [(old,), (recent,)]
        )

    deleted = database.purge_old_data(
        ":memory:", retention_days=7
    )

    assert deleted == 1

    remaining = db.execute(
        "SELECT timestamp FROM host_metrics"
    ).fetchall()

    assert remaining == [(recent,)]