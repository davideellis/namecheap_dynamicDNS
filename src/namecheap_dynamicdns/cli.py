from __future__ import annotations

import argparse
import logging
import sys
import time

from namecheap_dynamicdns.config import Settings, load_settings
from namecheap_dynamicdns.ip_lookup import PublicIpLookupError, discover_public_ip
from namecheap_dynamicdns.logging_utils import configure_logging
from namecheap_dynamicdns.namecheap import NamecheapUpdateError, update_a_record


LOGGER = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Update a single Namecheap A record using Dynamic DNS.")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously and check for updates every CHECK_INTERVAL_SECONDS.",
    )
    args = parser.parse_args()

    try:
        settings = load_settings()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    configure_logging(settings.log_level, settings.log_file)

    if args.loop:
        return _run_forever(settings)

    return _run_once(settings)


def _run_forever(settings: Settings) -> int:
    while True:
        exit_code = _run_once(settings)
        if exit_code != 0:
            LOGGER.warning("Updater run finished with exit code %s", exit_code)
        time.sleep(settings.check_interval_seconds)


def _run_once(settings: Settings) -> int:
    try:
        public_ip = discover_public_ip(settings.ip_discovery_timeout_seconds)
        result = update_a_record(
            domain=settings.domain,
            host=settings.host,
            password=settings.ddns_password,
            ip=public_ip,
            timeout_seconds=settings.ip_discovery_timeout_seconds,
        )
    except (PublicIpLookupError, NamecheapUpdateError) as exc:
        LOGGER.error("%s", exc)
        return 1
    except Exception:
        LOGGER.exception("Unexpected failure during update.")
        return 1

    record_name = settings.domain if settings.host == "@" else f"{settings.host}.{settings.domain}"
    LOGGER.info("Successful update for %s -> %s", record_name, result.ip)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
