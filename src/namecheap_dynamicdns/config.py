from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    domain: str
    host: str
    ddns_password: str
    check_interval_seconds: int
    log_level: str
    log_file: Path | None
    ip_discovery_timeout_seconds: int
    cache_file: Path
    status_file: Path


def load_settings() -> Settings:
    load_dotenv()

    domain = _required_env("NAMECHEAP_DOMAIN")
    host = os.getenv("NAMECHEAP_HOST", "@").strip() or "@"
    ddns_password = _required_env("NAMECHEAP_DDNS_PASSWORD")

    log_file_value = os.getenv("LOG_FILE", "").strip()
    log_file = Path(log_file_value) if log_file_value else None

    return Settings(
        domain=domain,
        host=host,
        ddns_password=ddns_password,
        check_interval_seconds=_int_env("CHECK_INTERVAL_SECONDS", 300),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        log_file=log_file,
        ip_discovery_timeout_seconds=_int_env("IP_DISCOVERY_TIMEOUT_SECONDS", 10),
        cache_file=Path(os.getenv("CACHE_FILE", "/var/lib/namecheap-dynamicdns/last_ip.txt").strip()),
        status_file=Path(os.getenv("STATUS_FILE", "/var/lib/namecheap-dynamicdns/status.json").strip()),
    )


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer.") from exc
