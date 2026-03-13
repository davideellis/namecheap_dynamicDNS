from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
import requests

from namecheap_dynamicdns.namecheap import (
    NamecheapUpdateError,
    UpdateResult,
    _parse_update_response,
    update_a_record,
)


def test_parse_successful_update_response() -> None:
    xml_text = """
    <interface-response>
      <Command>SETDNSHOST</Command>
      <Language>eng</Language>
      <IP>203.0.113.10</IP>
      <ErrCount>0</ErrCount>
      <errors />
      <ResponseCount>0</ResponseCount>
      <Done>true</Done>
      <debug><![CDATA[]]></debug>
    </interface-response>
    """

    result = _parse_update_response(xml_text)

    assert result == UpdateResult(ip="203.0.113.10", success=True, error_count=0)


def test_parse_update_response_raises_on_invalid_xml() -> None:
    with pytest.raises(NamecheapUpdateError, match="invalid XML"):
        _parse_update_response("<interface-response>")


def test_parse_update_response_raises_on_namecheap_error() -> None:
    xml_text = """
    <interface-response>
      <IP>203.0.113.10</IP>
      <ErrCount>1</ErrCount>
      <errors>
        <Err1>Domain not found</Err1>
      </errors>
    </interface-response>
    """

    with pytest.raises(NamecheapUpdateError, match="Domain not found"):
        _parse_update_response(xml_text)


def test_parse_update_response_raises_on_missing_ip() -> None:
    xml_text = """
    <interface-response>
      <ErrCount>0</ErrCount>
    </interface-response>
    """

    with pytest.raises(NamecheapUpdateError, match="Missing IP"):
        _parse_update_response(xml_text)


def test_update_a_record_calls_namecheap_endpoint() -> None:
    response = Mock()
    response.raise_for_status.return_value = None
    response.text = """
    <interface-response>
      <IP>203.0.113.12</IP>
      <ErrCount>0</ErrCount>
    </interface-response>
    """

    with patch("namecheap_dynamicdns.namecheap.requests.get", return_value=response) as get_mock:
        result = update_a_record(
            domain="example.com",
            host="@",
            password="secret",
            ip="203.0.113.12",
            timeout_seconds=10,
        )

    assert result.ip == "203.0.113.12"
    get_mock.assert_called_once_with(
        "https://dynamicdns.park-your-domain.com/update",
        params={
            "host": "@",
            "domain": "example.com",
            "password": "secret",
            "ip": "203.0.113.12",
        },
        timeout=10,
    )


def test_update_a_record_propagates_http_error() -> None:
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("bad status")

    with patch("namecheap_dynamicdns.namecheap.requests.get", return_value=response):
        with pytest.raises(requests.HTTPError, match="bad status"):
            update_a_record(
                domain="example.com",
                host="@",
                password="secret",
                ip="203.0.113.12",
                timeout_seconds=10,
            )
