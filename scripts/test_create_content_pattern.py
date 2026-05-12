#!/usr/bin/env python3
"""Minimal test for the CrowdStrike Falcon DLP content-pattern create API.

POSTs one hardcoded content pattern and prints the exact request body
sent and the exact response received. Use this to verify the schema
CrowdStrike actually accepts -- much easier to iterate on than the
Ansible role.

Credentials: set FALCON_CLIENT_ID and FALCON_CLIENT_SECRET in the
environment (or paste them into the constants below). The script
deliberately does NOT load them from a file; do not commit credentials.

Cloud region: set FALCON_CLOUD (default us-1).

Usage:
    export FALCON_CLIENT_ID=...
    export FALCON_CLIENT_SECRET=...
    python3 scripts/test_create_content_pattern.py

To test a different body shape, edit the PATTERN dict or swap in one of
the variants in the if __name__ == '__main__' block at the bottom. No
third-party dependencies -- pure stdlib.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# Credentials -- prefer env vars; do NOT commit literal secrets here.
# ---------------------------------------------------------------------------
CLIENT_ID = os.environ.get("FALCON_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("FALCON_CLIENT_SECRET", "")

# ---------------------------------------------------------------------------
# Cloud region
# ---------------------------------------------------------------------------
CLOUD = os.environ.get("FALCON_CLOUD", "us-1")
BASE_URLS = {
    "us-1": "https://api.crowdstrike.com",
    "us-2": "https://api.us-2.crowdstrike.com",
    "eu-1": "https://api.eu-1.crowdstrike.com",
    "us-gov-1": "https://api.laggar.gcw.crowdstrike.com",
    "us-gov-2": "https://api.us-gov-2.crowdstrike.mil",
}

# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
ENDPOINT = "/data-protection/entities/content-patterns/v1"

# ---------------------------------------------------------------------------
# Hardcoded pattern -- the body shape we are testing.
# Per the API documentation example:
#   {"name":"...","description":"","category":"Custom","region":"ALL",
#    "min_match_threshold":1,"regexes":["myregex"]}
# Bare object, no `resources` wrapper, regexes is a flat array of strings.
# ---------------------------------------------------------------------------
PATTERN = {
    "name": "iac-test-ssn-pattern",
    "description": "Created via test_create_content_pattern.py -- safe to delete",
    "category": "Custom",
    "region": "ALL",
    "min_match_threshold": 1,
    "regexes": [r"\b\d{3}-\d{2}-\d{4}\b"],
}


def get_token(base_url: str) -> str:
    url = f"{base_url}/oauth2/token"
    data = urllib.parse.urlencode(
        {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    ).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"OAuth status: {e.code}", file=sys.stderr)
        print(e.read().decode(), file=sys.stderr)
        sys.exit(1)
    return payload["access_token"]


def post_pattern(base_url: str, token: str, body: dict) -> None:
    url = f"{base_url}{ENDPOINT}"
    body_bytes = json.dumps(body).encode()

    print("-" * 70)
    print(f"POST {url}")
    print(f"Content-Length: {len(body_bytes)}")
    print("Request body (pretty):")
    print(json.dumps(body, indent=2))
    print()
    print("Equivalent curl:")
    print(
        f"curl -sS -X POST '{url}' \\\n"
        f"  -H 'Authorization: Bearer ***' \\\n"
        f"  -H 'Content-Type: application/json' \\\n"
        f"  --data '{json.dumps(body)}'"
    )
    print("-" * 70)

    req = urllib.request.Request(
        url,
        data=body_bytes,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            resp_headers = dict(resp.headers)
            resp_body = resp.read().decode()
    except urllib.error.HTTPError as e:
        status = e.code
        resp_headers = dict(e.headers)
        resp_body = e.read().decode()

    print(f"Status: {status}")
    print("Response headers:")
    for k, v in resp_headers.items():
        print(f"  {k}: {v}")
    print("Response body:")
    try:
        parsed = json.loads(resp_body)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        print(resp_body)


def main() -> None:
    if not CLIENT_ID or not CLIENT_SECRET:
        print(
            "ERROR: set FALCON_CLIENT_ID and FALCON_CLIENT_SECRET in the environment.",
            file=sys.stderr,
        )
        sys.exit(2)
    if CLOUD not in BASE_URLS:
        print(f"ERROR: unknown FALCON_CLOUD={CLOUD!r}", file=sys.stderr)
        sys.exit(2)
    base_url = BASE_URLS[CLOUD]
    print(f"Cloud: {CLOUD}  base: {base_url}")
    token = get_token(base_url)
    print(f"Got OAuth token (len={len(token)})")
    print()
    post_pattern(base_url, token, PATTERN)


if __name__ == "__main__":
    main()
