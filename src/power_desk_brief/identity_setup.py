"""Fixed fictional identity for the local demo; this is not authentication."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoUser:
    """Identity and group membership used by the local workflow."""

    user_id: str
    display_name: str
    groups: tuple[str, ...]


# 1. Set group membership in application code, never from email contents.
# A real deployment must obtain verified membership from its identity provider.
DEMO_USER = DemoUser(
    user_id="demo-head-of-power",
    display_name="Bobby Axelrod (Head of Power Trading)",
    groups=("power-desk",),
)
