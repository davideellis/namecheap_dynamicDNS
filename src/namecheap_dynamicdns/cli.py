from __future__ import annotations

import argparse
import json
import logging
import sys
import time

from namecheap_dynamicdns.config import Settings, load_settings
from namecheap_dynamicdns.ip_lookup import PublicIpLookupError, discover_public_ip
from namecheap_dynamicdns.logging_utils import configure_logging
from namecheap_dynamicdns.namecheap import NamecheapUpdateError, update_a_record
from namecheap_dynamicdns.state import read_cached_ip, read_status, write_cached_ip, write_status


LOGGER = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Update a single Namecheap A record using Dynamic DNS.")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously and check for updates every CHECK_INTERVAL_SECONDS.",
    )
    parser.add_argument(
        "--force-update",
        action="store_true",
        help="Call Namecheap even if the discovered IP matches the cached IP.",
    )
    parser.add_argument(
        "--print-status",
        action="store_true",
        help="Print the latest status JSON and exit.",
    )
    args = parser.parse_args()

    try:
        settings = load_settings()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    configure_logging(settings.log_level, settings.log_file)

    if args.print_status:
        return _print_status(settings)

    if args.loop:
        return _run_forever(settings)

    return _run_once(settings, force_update=args.force_update)


def _run_forever(settings: Settings) -> int:
    while True:
        exit_code = _run_once(settings)
        if exit_code != 0:
            LOGGER.warning("Updater run finished with exit code %s", exit_code)
        time.sleep(settings.check_interval_seconds)


def _run_once(settings: Settings, force_update: bool = False) -> int:
    record_name = settings.domain if settings.host == "@" else f"{settings.host}.{settings.domain}"

    try:
        public_ip = discover_public_ip(settings.ip_discovery_timeout_seconds)
        cached_ip = read_cached_ip(settings.cache_file)

        if not force_update and cached_ip == public_ip:
            message = f"Public IP unchanged for {record_name}; skipping Namecheap update."
            LOGGER.info(message)
            write_status(
                settings.status_file,
                record_name=record_name,
                success=True,
                message=message,
                public_ip=public_ip,
                updated=False,
            )
            return 0

        result = update_a_record(
            domain=settings.domain,
            host=settings.host,
            password=settings.ddns_password,
            ip=public_ip,
            timeout_seconds=settings.ip_discovery_timeout_seconds,
        )
        write_cached_ip(settings.cache_file, result.ip)
    except (PublicIpLookupError, NamecheapUpdateError) as exc:
        LOGGER.error("%s", exc)
        write_status(
            settings.status_file,
            record_name=record_name,
            success=False,
            message=str(exc),
            public_ip=None,
            updated=False,
        )
        return 1
    except Exception:
        LOGGER.exception("Unexpected failure during update.")
        write_status(
            settings.status_file,
            record_name=record_name,
            success=False,
            message="Unexpected failure during update.",
            public_ip=None,
            updated=False,
        )
        return 1

    message = f"Successful update for {record_name} -> {result.ip}"
    LOGGER.info(message)
    write_status(
        settings.status_file,
        record_name=record_name,
        success=True,
        message=message,
        public_ip=result.ip,
        updated=True,
    )
    return 0


def _print_status(settings: Settings) -> int:
    status = read_status(settings.status_file)
    if status is None:
        print(f"No status file found at {settings.status_file}", file=sys.stderr)
        return 1

    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
