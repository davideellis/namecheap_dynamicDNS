from __future__ import annotations

from pathlib import Path

from namecheap_dynamicdns.state import read_cached_ip, read_status, write_cached_ip, write_status


def test_cached_ip_round_trip(tmp_path: Path) -> None:
    cache_file = tmp_path / "state" / "last_ip.txt"

    write_cached_ip(cache_file, "203.0.113.20")

    assert read_cached_ip(cache_file) == "203.0.113.20"


def test_read_cached_ip_returns_none_when_missing(tmp_path: Path) -> None:
    assert read_cached_ip(tmp_path / "missing.txt") is None


def test_status_round_trip(tmp_path: Path) -> None:
    status_file = tmp_path / "status" / "status.json"

    write_status(
        status_file,
        record_name="nest.example.com",
        success=True,
        message="Updated successfully",
        public_ip="203.0.113.21",
        updated=True,
    )

    status = read_status(status_file)

    assert status is not None
    assert status["record_name"] == "nest.example.com"
    assert status["success"] is True
    assert status["public_ip"] == "203.0.113.21"
    assert status["updated"] is True
