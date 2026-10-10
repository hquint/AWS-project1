"""Power Desk Morning Brief application."""

import argparse
from pathlib import Path

from .access import check_access
from .identity import DEMO_USER
from .sources import load_sources


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
    print("Brief generation and AWS integration are not implemented yet.")
