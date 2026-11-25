"""Supervision de la disponibilité des services HTTP."""

import asyncio
import time
from typing import Any

import aiohttp


async def check_http(
    session: aiohttp.ClientSession,
    service: dict[str, Any]
) -> dict[str, Any]:
    """Vérifie la disponibilité d'un service HTTP."""

    result = {
        "service_name": service["name"],
        "url": service["url"],
        "status_code": None,
        "response_time_ms": None,
        "is_healthy": 0,
        "ssl_days_left": None,
        "error_msg": None
    }

    start = time.monotonic()

    try:
        async with session.get(service["url"]) as response:
            result["status_code"] = response.status

            healthy = (
                response.status == service["expected_status"]
            )

            if not healthy:
                result["error_msg"] = "Statut HTTP inattendu"

            if healthy and "expected_json" in service:
                data = await response.json()

                for key, value in service["expected_json"].items():
                    if data.get(key) != value:
                        healthy = False
                        result["error_msg"] = "JSON inattendu"
                        break

            result["is_healthy"] = int(healthy)

    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as error:
        result["error_msg"] = str(error) or type(error).__name__

    finally:
        result["response_time_ms"] = round(
            (time.monotonic() - start) * 1000, 2
        )

    return result


async def check_services(config: dict[str, Any]) -> list:
    """Supervise les services HTTP, TCP et SSL."""

    delay = config["healthcheck_timeout"]
    timeout = aiohttp.ClientTimeout(total=delay)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [
            check_http(session, service)
            for service in config["services"]
        ]

        results = await asyncio.gather(*tasks)

    for service in config.get("tcp_services", []):
        result = await check_tcp(
            service["host"], service["port"], delay
        )

        results.append({
            "service_name": service["name"],
            "url": f"tcp://{service['host']}:{service['port']}",
            "status_code": None,
            "response_time_ms": result["response_time_ms"],
            "is_healthy": result["is_healthy"],
            "ssl_days_left": None,
            "error_msg": result["error_msg"]
        })

    for service in config.get("ssl_services", []):
        start = time.monotonic()

        result = await asyncio.to_thread(
            check_ssl,
            service["host"],
            service["port"],
            delay
        )

        results.append({
            "service_name": service["name"],
            "url": f"ssl://{service['host']}:{service['port']}",
            "status_code": None,
            "response_time_ms": round(
                (time.monotonic() - start) * 1000, 2
            ),
            "is_healthy": result["is_healthy"],
            "ssl_days_left": result["ssl_days_left"],
            "error_msg": result["error_msg"]
        })

    return results


async def check_tcp(
    host: str,
    port: int,
    timeout: float = 5
) -> dict[str, Any]:
    """Verifie la disponibilite d'un port TCP."""

    start = time.monotonic()

    result = {
        "host": host,
        "port": port,
        "is_healthy": 0,
        "response_time_ms": None,
        "error_msg": None
    }

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )

        writer.close()
        await writer.wait_closed()

        result["is_healthy"] = 1

    except (OSError, asyncio.TimeoutError) as error:
        result["error_msg"] = str(error) or type(error).__name__

    finally:
        result["response_time_ms"] = round(
            (time.monotonic() - start) * 1000, 2
        )

    return result


def check_ssl(host: str, port: int = 443, timeout: float = 5):
    """Verifie la validite et l'expiration du certificat SSL."""
    import socket
    import ssl
    from datetime import datetime, timezone

    result = {
        "host": host,
        "port": port,
        "is_healthy": 0,
        "ssl_days_left": None,
        "error_msg": None
    }

    try:
        context = ssl.create_default_context()

        with socket.create_connection(
            (host, port), timeout=timeout
        ) as sock:
            with context.wrap_socket(
                sock, server_hostname=host
            ) as secure_sock:
                cert = secure_sock.getpeercert()

                expiration = datetime.fromtimestamp(
                    ssl.cert_time_to_seconds(cert["notAfter"]),
                    tz=timezone.utc
                )

                remaining = expiration - datetime.now(timezone.utc)

                result["ssl_days_left"] = remaining.days
                result["is_healthy"] = int(
                    remaining.total_seconds() > 0
                )

    except (OSError, ValueError) as error:
        result["error_msg"] = str(error)

    return result
