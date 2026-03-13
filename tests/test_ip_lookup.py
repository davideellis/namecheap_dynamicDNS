from __future__ import annotations

from unittest.mock import Mock, call, patch

import pytest
import requests

from namecheap_dynamicdns.ip_lookup import PublicIpLookupError, discover_public_ip


def test_discover_public_ip_returns_first_valid_result() -> None:
    first_response = Mock()
    first_response.raise_for_status.return_value = None
    first_response.text = "203.0.113.8"

    with patch("namecheap_dynamicdns.ip_lookup.requests.get", return_value=first_response) as get_mock:
        result = discover_public_ip(timeout_seconds=7)

    assert result == "203.0.113.8"
    get_mock.assert_called_once_with("https://api.ipify.org", timeout=7)


def test_discover_public_ip_falls_back_after_failure() -> None:
    bad_response = Mock()
    bad_response.raise_for_status.return_value = None
    bad_response.text = "not-an-ip"

    good_response = Mock()
    good_response.raise_for_status.return_value = None
    good_response.text = "203.0.113.9"

    with patch(
        "namecheap_dynamicdns.ip_lookup.requests.get",
        side_effect=[bad_response, good_response],
    ) as get_mock:
        result = discover_public_ip(timeout_seconds=5)

    assert result == "203.0.113.9"
    assert get_mock.call_args_list == [
        call("https://api.ipify.org", timeout=5),
        call("https://ifconfig.me/ip", timeout=5),
    ]


def test_discover_public_ip_raises_after_all_providers_fail() -> None:
    with patch(
        "namecheap_dynamicdns.ip_lookup.requests.get",
        side_effect=requests.RequestException("offline"),
    ):
        with pytest.raises(PublicIpLookupError, match="ipify: offline"):
            discover_public_ip(timeout_seconds=3)
