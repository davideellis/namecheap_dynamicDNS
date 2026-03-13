from __future__ import annotations

from pathlib import Path

import pytest

from namecheap_dynamicdns.config import Settings, _int_env, load_settings


def test_load_settings_reads_required_and_optional_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NAMECHEAP_DOMAIN", "example.com")
    monkeypatch.setenv("NAMECHEAP_HOST", "home")
    monkeypatch.setenv("NAMECHEAP_DDNS_PASSWORD", "secret")
    monkeypatch.setenv("CHECK_INTERVAL_SECONDS", "600")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("LOG_FILE", "/tmp/updater.log")
    monkeypatch.setenv("IP_DISCOVERY_TIMEOUT_SECONDS", "15")

    settings = load_settings()

    assert settings == Settings(
        domain="example.com",
        host="home",
        ddns_password="secret",
        check_interval_seconds=600,
        log_level="DEBUG",
        log_file=Path("/tmp/updater.log"),
        ip_discovery_timeout_seconds=15,
    )


def test_load_settings_defaults_blank_host_to_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NAMECHEAP_DOMAIN", "example.com")
    monkeypatch.setenv("NAMECHEAP_HOST", "   ")
    monkeypatch.setenv("NAMECHEAP_DDNS_PASSWORD", "secret")
    monkeypatch.delenv("LOG_FILE", raising=False)

    settings = load_settings()

    assert settings.host == "@"
    assert settings.log_file is None


def test_load_settings_requires_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NAMECHEAP_DOMAIN", raising=False)
    monkeypatch.setenv("NAMECHEAP_DDNS_PASSWORD", "secret")

    with pytest.raises(ValueError, match="NAMECHEAP_DOMAIN"):
        load_settings()


def test_int_env_rejects_non_integer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHECK_INTERVAL_SECONDS", "five")

    with pytest.raises(ValueError, match="CHECK_INTERVAL_SECONDS"):
        _int_env("CHECK_INTERVAL_SECONDS", 300)
