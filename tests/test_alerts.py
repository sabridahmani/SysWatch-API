"""Tests unitaires du moteur d'alertes."""

from src.alerts import detect_alerts, detect_memory_growth


CONFIG = {
    "thresholds": {
        "cpu_pct": 90,
        "ram_pct": 90,
        "disk_pct": 85,
        "ssl_days": 15
    }
}


def test_cpu_alert():
    host = {
        "hostname": "TEST-PC",
        "cpu_pct": 95,
        "ram_pct": 40
    }

    incidents = detect_alerts(CONFIG, host, [], [])

    assert len(incidents) == 1
    assert incidents[0]["category"] == "CPU"


def test_ram_alert():
    host = {
        "hostname": "TEST-PC",
        "cpu_pct": 20,
        "ram_pct": 95
    }

    incidents = detect_alerts(CONFIG, host, [], [])

    assert len(incidents) == 1
    assert incidents[0]["category"] == "RAM"


def test_disk_alert():
    host = {
        "hostname": "TEST-PC",
        "cpu_pct": 20,
        "ram_pct": 40
    }

    disks = [{"mountpoint": "C:", "usage_pct": 90}]

    incidents = detect_alerts(CONFIG, host, disks, [])

    assert len(incidents) == 1
    assert incidents[0]["category"] == "DISK"


def test_ssl_alert():
    host = {
        "hostname": "TEST-PC",
        "cpu_pct": 20,
        "ram_pct": 40
    }

    services = [{
        "service_name": "HTTPS",
        "is_healthy": True,
        "ssl_days_left": 10
    }]

    incidents = detect_alerts(CONFIG, host, [], services)

    assert len(incidents) == 1
    assert incidents[0]["category"] == "SSL"


def test_service_unavailable():
    host = {
        "hostname": "TEST-PC",
        "cpu_pct": 20,
        "ram_pct": 40
    }

    services = [{
        "service_name": "Grafana",
        "is_healthy": False
    }]

    incidents = detect_alerts(CONFIG, host, [], services)

    assert len(incidents) == 1
    assert incidents[0]["category"] == "SERVICE"
    assert incidents[0]["severity"] == "CRITICAL"


def test_memory_growth():
    history = {}

    for memory in range(100, 200, 10):
        processes = [{
            "pid": 1234,
            "name": "python",
            "rss_mb": memory
        }]

        incidents = detect_memory_growth(
            processes, history, samples=10
        )

    assert len(incidents) == 1
    assert incidents[0]["category"] == "MEMORY_LEAK"


def test_no_alert():
    host = {
        "hostname": "TEST-PC",
        "cpu_pct": 20,
        "ram_pct": 40
    }

    incidents = detect_alerts(CONFIG, host, [], [])

    assert incidents == []