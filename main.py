#!/usr/bin/env python3
"""Export all MISP events to a JSON file."""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv


def load_config(env_file=None):
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    url = os.environ.get("MISP_URL", "").strip()
    api_key = os.environ.get("MISP_API_KEY", "").strip()
    verify_ssl_raw = os.environ.get("MISP_VERIFY_SSL", "true").strip().lower()
    timeout_raw = os.environ.get("MISP_TIMEOUT", "120").strip()

    if not url:
        print("ERROR: MISP_URL is not set. Copy .env.example to .env and fill in your details.", file=sys.stderr)
        sys.exit(1)
    if not api_key:
        print("ERROR: MISP_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)
    if not url.startswith(("http://", "https://")):
        print("ERROR: MISP_URL must start with http:// or https://", file=sys.stderr)
        sys.exit(1)

    verify_ssl = verify_ssl_raw not in ("false", "0", "no", "off")
    try:
        timeout = int(timeout_raw)
    except ValueError:
        timeout = 120

    return url.rstrip("/"), api_key, verify_ssl, timeout


def fetch_all_events(url, api_key, verify_ssl, timeout):
    """Fetch all events from MISP using the REST search endpoint with pagination."""
    headers = {
        "Authorization": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    all_events = []
    page = 1
    page_size = 100

    while True:
        payload = {
            "returnFormat": "json",
            "metadata": False,
            "enforceWarninglist": False,
            "page": page,
            "limit": page_size,
        }

        response = requests.post(
            f"{url}/events/restSearch",
            json=payload,
            headers=headers,
            verify=verify_ssl,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()

        events_page = data.get("response", [])
        if not events_page:
            break

        for event in events_page:
            if isinstance(event, dict) and "Event" in event:
                all_events.append(event["Event"])
            elif isinstance(event, dict):
                all_events.append(event)

        print(f"  Fetched {len(all_events)} events so far...", file=sys.stderr)

        if len(events_page) < page_size:
            break

        page += 1

    return all_events


def main():
    parser = argparse.ArgumentParser(description="Export all MISP events to a JSON file.")
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Output JSON file path (default: misp_events_export_YYYY-MM-DD_HHMMSS.json)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON with indentation",
    )
    parser.add_argument(
        "--env-file",
        metavar="FILE",
        help="Path to .env file (default: .env in current directory)",
    )
    args = parser.parse_args()

    url, api_key, verify_ssl, timeout = load_config(args.env_file)

    output_path = Path(args.output) if args.output else Path(
        f"misp_events_export_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    )

    print(f"MISP URL:    {url}")
    print(f"Output file: {output_path.resolve()}")
    print(f"Pretty:      {args.pretty}")
    print()

    if not verify_ssl:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Connecting to MISP...", file=sys.stderr)
    try:
        events = fetch_all_events(url, api_key, verify_ssl, timeout)
    except requests.exceptions.SSLError:
        print("SSL Error: certificate verification failed.", file=sys.stderr)
        print("  Tip: set MISP_VERIFY_SSL=false for self-signed certificates.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"Connection failed: unable to reach {url}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Authentication failed: MISP_API_KEY is invalid or expired.", file=sys.stderr)
        else:
            print(f"HTTP {e.response.status_code}: {e.response.text[:300]}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"Request timed out after {timeout}s.", file=sys.stderr)
        sys.exit(1)

    total_attributes = sum(len(e.get("Attribute", [])) for e in events)
    total_objects = sum(len(e.get("Object", [])) for e in events)

    print(f"\nExport summary:")
    print(f"  Events:     {len(events)}")
    print(f"  Attributes: {total_attributes}")
    print(f"  Objects:    {total_objects}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            if args.pretty:
                json.dump(events, f, indent=2, ensure_ascii=False)
            else:
                json.dump(events, f, ensure_ascii=False)
    except IOError as e:
        print(f"Failed to write output file: {e}", file=sys.stderr)
        sys.exit(1)

    file_size = output_path.stat().st_size
    if file_size < 1024:
        size_str = f"{file_size} B"
    elif file_size < 1024 * 1024:
        size_str = f"{file_size / 1024:.1f} KB"
    else:
        size_str = f"{file_size / (1024 * 1024):.1f} MB"

    print(f"\nExport complete: {output_path.resolve()} ({size_str})")
    sys.exit(0)


if __name__ == "__main__":
    main()
