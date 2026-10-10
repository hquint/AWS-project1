"""Decide which source records may enter the demo briefing workflow."""

from typing import Any

from .identity import DemoUser


def check_access(source: dict[str, Any], user: DemoUser) -> tuple[bool, str]:
    """Return eligibility and a content-free reason; deny uncertain permissions."""
    # 1. Restricted content never enters this workflow, even with a group match.
    classification = source.get("classification")
    if classification == "restricted":
        return False, "restricted content is excluded from AI processing"
    if classification not in ("public", "desk-confidential"):
        return False, "missing or unknown classification"

    # 2. Validate access metadata rather than treating missing data as public.
    groups = source.get("access_groups")
    if not isinstance(groups, list) or any(
        not isinstance(group, str) or not group.strip() for group in groups
    ):
        return False, "missing or invalid access groups"

    # 3. Public sources need no private group membership.
    if classification == "public":
        return True, "public source"

    # 4. Internal sources require at least one exact group match.
    if any(group in user.groups for group in groups):
        return True, "authorised group membership"
    return False, "no authorised group membership"
