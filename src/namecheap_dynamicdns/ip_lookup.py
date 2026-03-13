from __future__ import annotations

import ipaddress
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class DiscoveryEndpoint:
    name: str
    url: str


DEFAULT_ENDPOINTS = (
    DiscoveryEndpoint("ipify", "https://api.ipify.org"),
    DiscoveryEndpoint("ifconfig.me", "https://ifconfig.me/ip"),
    DiscoveryEndpoint("ident.me", "https://ident.me"),
)


class PublicIpLookupError(RuntimeError):
    pass


def discover_public_ip(timeout_seconds: int) -> str:
    errors: list[str] = []

    for endpoint in DEFAULT_ENDPOINTS:
        try:
            response = requests.get(endpoint.url, timeout=timeout_seconds)
            response.raise_for_status()
            ip = response.text.strip()
            ipaddress.ip_address(ip)
            return ip
        except (requests.RequestException, ValueError) as exc:
            errors.append(f"{endpoint.name}: {exc}")

    joined_errors = "; ".join(errors)
    raise PublicIpLookupError(f"Failed to discover public IP. {joined_errors}")

