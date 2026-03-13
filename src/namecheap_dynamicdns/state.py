from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_cached_ip(cache_file: Path) -> str | None:
    try:
        cached_ip = cache_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None

    return cached_ip or None


def write_cached_ip(cache_file: Path, ip: str) -> None:
    _ensure_parent(cache_file)
    cache_file.write_text(f"{ip}\n", encoding="utf-8")


def read_status(status_file: Path) -> dict[str, Any] | None:
    try:
        return json.loads(status_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def write_status(
    status_file: Path,
    *,
    record_name: str,
    success: bool,
    message: str,
    public_ip: str | None,
    updated: bool,
) -> None:
    _ensure_parent(status_file)
    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "record_name": record_name,
        "success": success,
        "message": message,
        "public_ip": public_ip,
        "updated": updated,
    }
    status_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
