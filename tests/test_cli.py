from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from namecheap_dynamicdns.cli import _run_once, main
from namecheap_dynamicdns.config import Settings
from namecheap_dynamicdns.ip_lookup import PublicIpLookupError
from namecheap_dynamicdns.namecheap import UpdateResult


def _settings() -> Settings:
    return Settings(
        domain="example.com",
        host="@",
        ddns_password="secret",
        check_interval_seconds=300,
        log_level="INFO",
        log_file=Path("/tmp/updater.log"),
        ip_discovery_timeout_seconds=10,
    )


def test_main_returns_error_when_config_is_invalid() -> None:
    with patch("namecheap_dynamicdns.cli.load_settings", side_effect=ValueError("bad config")), patch(
        "sys.argv", ["namecheap-dynamicdns"]
    ):
        assert main() == 2


def test_main_runs_once_successfully() -> None:
    with patch("namecheap_dynamicdns.cli.load_settings", return_value=_settings()), patch(
        "namecheap_dynamicdns.cli.configure_logging"
    ), patch("namecheap_dynamicdns.cli._run_once", return_value=0) as run_once, patch(
        "sys.argv", ["namecheap-dynamicdns"]
    ):
        assert main() == 0
        run_once.assert_called_once()


def test_main_runs_forever_mode_when_requested() -> None:
    with patch("namecheap_dynamicdns.cli.load_settings", return_value=_settings()), patch(
        "namecheap_dynamicdns.cli.configure_logging"
    ), patch("namecheap_dynamicdns.cli._run_forever", return_value=0) as run_forever, patch(
        "sys.argv", ["namecheap-dynamicdns", "--loop"]
    ):
        assert main() == 0
        run_forever.assert_called_once()


def test_run_once_updates_record_successfully() -> None:
    with patch("namecheap_dynamicdns.cli.discover_public_ip", return_value="203.0.113.20"), patch(
        "namecheap_dynamicdns.cli.update_a_record",
        return_value=UpdateResult(ip="203.0.113.20", success=True, error_count=0),
    ) as update_record:
        assert _run_once(_settings()) == 0
        update_record.assert_called_once()


def test_run_once_returns_error_on_lookup_failure() -> None:
    with patch(
        "namecheap_dynamicdns.cli.discover_public_ip",
        side_effect=PublicIpLookupError("lookup failed"),
    ):
        assert _run_once(_settings()) == 1
