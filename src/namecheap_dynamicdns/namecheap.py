from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests


LOGGER = logging.getLogger(__name__)
UPDATE_URL = "https://dynamicdns.park-your-domain.com/update"


@dataclass(frozen=True)
class UpdateResult:
    ip: str
    success: bool
    error_count: int


class NamecheapUpdateError(RuntimeError):
    pass


def update_a_record(domain: str, host: str, password: str, ip: str, timeout_seconds: int) -> UpdateResult:
    response = requests.get(
        UPDATE_URL,
        params={
            "host": host,
            "domain": domain,
            "password": password,
            "ip": ip,
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()

    return _parse_update_response(response.text)


def _parse_update_response(xml_text: str) -> UpdateResult:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise NamecheapUpdateError("Namecheap returned invalid XML.") from exc

    try:
        error_count = int(_required_text(root, "ErrCount"))
    except ValueError as exc:
        raise NamecheapUpdateError("Invalid ErrCount in Namecheap response.") from exc
    response_ip = _required_text(root, "IP")

    if error_count != 0:
        errors = [node.text.strip() for node in root.findall(".//errors/*") if node.text]
        message = errors[0] if errors else "Unknown Namecheap error."
        raise NamecheapUpdateError(message)

    LOGGER.info("Namecheap record now points to %s", response_ip)
    return UpdateResult(ip=response_ip, success=True, error_count=error_count)


def _required_text(root: ET.Element, tag_name: str) -> str:
    element = root.find(f".//{tag_name}")
    if element is None or element.text is None:
        raise NamecheapUpdateError(f"Missing {tag_name} in Namecheap response.")
    return element.text.strip()
