"""Agent principal de supervision SysWatch-API."""

import asyncio
import time

from src.config import load_config
from src.logger import setup_logger
from src.collector import (
    collect_host_metrics,
    collect_disk_metrics,
    collect_disk_io
)
from src.process_monitor import collect_processes
from src.healthcheck import check_services
from src.alerts import detect_alerts, detect_memory_growth
from src.database import (
    init_database,
    save_metrics,
    save_healthchecks,
    save_incidents,
    purge_old_data
)


def main():
    """Lance la supervision continue."""
    config = load_config()
    logger = setup_logger(config)
    database_path = config["database_path"]
    memory_history = {}

    init_database(database_path)

    logger.info("Demarrage de SysWatch-API")

    try:
        while True:
            start = time.monotonic()

            try:
                host = collect_host_metrics()
                host.update(collect_disk_io())

                disks = collect_disk_metrics()
                processes = collect_processes(config["processes"])
                services = asyncio.run(check_services(config))

                timestamp = host["timestamp"]

                save_metrics(database_path, host, disks, processes)
                save_healthchecks(database_path, timestamp, services)

                incidents = detect_alerts(
                    config, host, disks, services
                )

                incidents.extend(
                    detect_memory_growth(
                        processes,
                        memory_history,
                        config["thresholds"]["memory_growth_samples"]
                    )
                )

                save_incidents(database_path, timestamp, incidents)

                for incident in incidents:
                    logger.warning(incident["description"])

                purge_old_data(
                    database_path,
                    config["retention_days"]
                )

                logger.info(
                    "Collecte OK | CPU: %.1f%% | RAM: %.1f%% | "
                    "Processus: %d | Incidents: %d",
                    host["cpu_pct"],
                    host["ram_pct"],
                    len(processes),
                    len(incidents)
                )

            except Exception:
                logger.exception("Erreur pendant la collecte")

            elapsed = time.monotonic() - start

            time.sleep(
                max(0, config["collection_interval"] - elapsed)
            )

    except KeyboardInterrupt:
        logger.info("Arret de SysWatch-API")


if __name__ == "__main__":
    main()
