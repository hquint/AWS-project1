"""Run the local briefing workflow from the command line."""

import argparse
import json
import os
from pathlib import Path

from .source_access import check_access
from .bedrock_request import build_request_body
from .identity_setup import DEMO_USER
from .source_loader import load_sources


def main() -> None:
    """Show which fictional sources are eligible for the demo user's briefing."""
    # 1. Select the local input directory and the configured demo identity.
    parser = argparse.ArgumentParser(description="Inspect demo briefing access.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/synthetic"),
        help="fixture directory (default: data/synthetic, relative to the working directory)",
    )
    parser.add_argument(
        "--prepare-request",
        type=Path,
        metavar="FILE",
        help="save a private request-body JSON file without calling AWS; must be a new file",
    )
    args = parser.parse_args()
    user = DEMO_USER

    # 2. Load the fixtures, stopping cleanly if their structure is invalid.
    try:
        sources = load_sources(args.data_dir)
    except ValueError as error:
        parser.exit(1, f"{error} Check --data-dir and the fixture files.\n")

    # 3. Retain eligible records separately; decision metadata contains no bodies.
    eligible_sources = []
    decisions = []
    for source in sources:
        allowed, reason = check_access(source, user)
        if allowed:
            eligible_sources.append(source)
        decisions.append((source["id"], allowed, reason))

    # 4. Show the access report without printing titles or source bodies.
    print("Power Desk Morning Brief")
    print(f"Demo user: {user.display_name}")
    print(f"User ID: {user.user_id}")
    print(f"Groups: {', '.join(user.groups)}")
    print(f"\nLoaded: {len(sources)} sources")
    print(f"Eligible: {len(eligible_sources)}")
    print(f"Excluded: {len(sources) - len(eligible_sources)}\n")
    for source_id, allowed, reason in decisions:
        status = "ELIGIBLE" if allowed else "EXCLUDED"
        print(f"{source_id}: {status} — {reason}")
    print("\nAccess eligibility does not make embedded instructions trustworthy.")

    # 5. Optionally prepare the request using only the eligible source list.
    if args.prepare_request is not None:
        try:
            request_body = build_request_body(eligible_sources, user)
            args.prepare_request.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            # Create a new owner-only file; do not overwrite an existing request.
            descriptor = os.open(
                args.prepare_request, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
            )
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                json.dump(request_body, file, indent=2, ensure_ascii=False)
                file.write("\n")
        except (ValueError, OSError):
            parser.exit(
                1,
                "Cannot prepare request. Use a new writable output file "
                "and valid eligible sources.\n",
            )
        print(f"\nPrepared request body: {args.prepare_request}")
        print("No request was sent to AWS.")
    else:
        print("Use --prepare-request FILE to prepare an offline model request body.")
    print("Live model inference is not configured yet.")
