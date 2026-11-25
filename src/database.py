"""Gestion de la base de données SQLite."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path


def init_database(database_path: str) -> None:
    """Initialise la base et les tables de supervision.

    Args:
        database_path: Chemin de la base SQLite.
    """
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(path)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")

        with conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS host_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    hostname TEXT,
                    cpu_pct REAL,
                    cpu_per_core TEXT,
                    cpu_user REAL,
                    cpu_system REAL,
                    cpu_iowait REAL,
                    load_1m REAL,
                    load_5m REAL,
                    load_15m REAL,
                    ram_total_mb REAL,
                    ram_used_mb REAL,
                    ram_available_mb REAL,
                    ram_cached_mb REAL,
                    ram_buffers_mb REAL,
                    ram_pct REAL,
                    swap_pct REAL,
                    disk_read_mb_s REAL,
                    disk_write_mb_s REAL,
                    read_iops REAL,
                    write_iops REAL
                );

                CREATE TABLE IF NOT EXISTS disk_partitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    mountpoint TEXT,
                    total_gb REAL,
                    used_gb REAL,
                    usage_pct REAL
                );

                CREATE TABLE IF NOT EXISTS process_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    pid INTEGER,
                    name TEXT,
                    status TEXT,
                    cpu_pct REAL,
                    rss_mb REAL,
                    num_threads INTEGER,
                    open_files INTEGER
                );

                CREATE TABLE IF NOT EXISTS service_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    service_name TEXT,
                    url TEXT,
                    status_code INTEGER,
                    response_time_ms REAL,
                    is_healthy INTEGER,
                    ssl_days_left INTEGER,
                    error_msg TEXT
                );

                CREATE TABLE IF NOT EXISTS system_incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    category TEXT,
                    severity TEXT,
                    resource_name TEXT,
                    metric_value REAL,
                    threshold_value REAL,
                    description TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_host_time
                ON host_metrics(timestamp);

                CREATE INDEX IF NOT EXISTS idx_disk_time
                ON disk_partitions(timestamp);

                CREATE INDEX IF NOT EXISTS idx_process_time
                ON process_metrics(timestamp);

                CREATE INDEX IF NOT EXISTS idx_service_time
                ON service_health(timestamp);

                CREATE INDEX IF NOT EXISTS idx_incident_time
                ON system_incidents(timestamp);

                CREATE INDEX IF NOT EXISTS idx_service_name
                ON service_health(service_name, timestamp);

                CREATE INDEX IF NOT EXISTS idx_mountpoint
                ON disk_partitions(mountpoint, timestamp);

                CREATE INDEX IF NOT EXISTS idx_process_pid
                ON process_metrics(pid, timestamp);
            """)


def save_metrics(database_path, host, disks, processes):
    """Enregistre les métriques collectées dans SQLite."""

    host = host.copy()
    timestamp = host["timestamp"]
    host["cpu_per_core"] = json.dumps(host["cpu_per_core"])

    with closing(sqlite3.connect(database_path)) as conn:
        with conn:
            columns = ", ".join(host.keys())
            placeholders = ", ".join("?" for _ in host)

            conn.execute(
                f"INSERT INTO host_metrics ({columns}) "
                f"VALUES ({placeholders})",
                tuple(host.values())
            )

            for disk in disks:
                conn.execute("""
                    INSERT INTO disk_partitions (
                        timestamp, mountpoint, total_gb,
                        used_gb, usage_pct
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    disk["mountpoint"],
                    disk["total_gb"],
                    disk["used_gb"],
                    disk["usage_pct"]
                ))

            for process in processes:
                conn.execute("""
                    INSERT INTO process_metrics (
                        timestamp, pid, name, status,
                        cpu_pct, rss_mb, num_threads, open_files
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    process["pid"],
                    process["name"],
                    process["status"],
                    process["cpu_pct"],
                    process["rss_mb"],
                    process["num_threads"],
                    process["open_files"]
                ))   


def save_healthchecks(database_path, timestamp, results):
    """Enregistre les resultats des healthchecks."""

    with closing(sqlite3.connect(database_path)) as conn:
        with conn:
            for result in results:
                conn.execute("""
                    INSERT INTO service_health (
                        timestamp, service_name, url,
                        status_code, response_time_ms,
                        is_healthy, ssl_days_left, error_msg
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    result["service_name"],
                    result["url"],
                    result["status_code"],
                    result["response_time_ms"],
                    result["is_healthy"],
                    result["ssl_days_left"],
                    result["error_msg"]
                ))


def save_incidents(database_path, timestamp, incidents):
    """Enregistre les incidents dans SQLite."""

    with closing(sqlite3.connect(database_path)) as conn:
        with conn:
            for incident in incidents:
                conn.execute("""
                    INSERT INTO system_incidents (
                        timestamp, category, severity,
                        resource_name, metric_value,
                        threshold_value, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    incident["category"],
                    incident["severity"],
                    incident["resource_name"],
                    incident["metric_value"],
                    incident["threshold_value"],
                    incident["description"]
                ))


def purge_old_data(database_path, retention_days=7):
    """Supprime les donnees anciennes."""
    from datetime import datetime, timedelta, timezone

    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(days=retention_days)
    ).isoformat()

    tables = [
        "host_metrics",
        "disk_partitions",
        "process_metrics",
        "service_health",
        "system_incidents"
    ]

    deleted = 0

    with closing(sqlite3.connect(database_path)) as conn:
        with conn:
            for table in tables:
                cursor = conn.execute(
                    f"DELETE FROM {table} WHERE timestamp < ?",
                    (cutoff,)
                )
                deleted += cursor.rowcount

    return deleted


def calculate_sla(database_path):
    """Calcule le taux de disponibilite des services."""

    with closing(sqlite3.connect(database_path)) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT
                service_name,
                COUNT(*) AS total_checks,
                SUM(is_healthy) AS successful_checks,
                ROUND(AVG(is_healthy) * 100, 2) AS sla_pct,
                ROUND(AVG(response_time_ms), 2) AS avg_response_ms
            FROM service_health
            GROUP BY service_name
        """).fetchall()

        return [dict(row) for row in rows]
