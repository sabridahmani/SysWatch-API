"""Detection des alertes et incidents systeme."""


def detect_alerts(config, host, disks, services):
    """Detecte les depassements de seuils."""
    incidents = []
    thresholds = config["thresholds"]

    def add_incident(category, resource, value, threshold, description):
        incidents.append({
            "category": category,
            "severity": "WARNING",
            "resource_name": resource,
            "metric_value": value,
            "threshold_value": threshold,
            "description": description
        })

    if host["cpu_pct"] >= thresholds["cpu_pct"]:
        add_incident(
            "CPU", host["hostname"],
            host["cpu_pct"], thresholds["cpu_pct"],
            "Utilisation CPU excessive"
        )

    if host["ram_pct"] >= thresholds["ram_pct"]:
        add_incident(
            "RAM", host["hostname"],
            host["ram_pct"], thresholds["ram_pct"],
            "Utilisation RAM excessive"
        )

    for disk in disks:
        if disk["usage_pct"] >= thresholds["disk_pct"]:
            add_incident(
                "DISK", disk["mountpoint"],
                disk["usage_pct"], thresholds["disk_pct"],
                "Espace disque insuffisant"
            )

    for service in services:
        if not service["is_healthy"]:
            add_incident(
                "SERVICE", service["service_name"],
                0, 1, "Service indisponible"
            )
            incidents[-1]["severity"] = "CRITICAL"

        days = service.get("ssl_days_left")

        if days is not None and days <= thresholds["ssl_days"]:
            add_incident(
                "SSL", service["service_name"],
                days, thresholds["ssl_days"],
                "Expiration prochaine du certificat SSL"
            )

    return incidents


def detect_memory_growth(processes, history, samples=10):
    """Detecte une croissance continue de la memoire."""
    incidents = []
    active_pids = set()

    for process in processes:
        pid = process["pid"]
        memory = process["rss_mb"]
        active_pids.add(pid)

        values = history.setdefault(pid, [])
        values.append(memory)

        if len(values) > samples:
            values.pop(0)

        if len(values) == samples and all(
            b > a for a, b in zip(values, values[1:])
        ):
            incidents.append({
                "category": "MEMORY_LEAK",
                "severity": "WARNING",
                "resource_name": process["name"],
                "metric_value": memory,
                "threshold_value": values[0],
                "description": "Croissance continue de la memoire"
            })

    for pid in list(history):
        if pid not in active_pids:
            del history[pid]

    return incidents
