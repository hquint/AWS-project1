"""Power Desk Morning Brief application."""

from .identity import DEMO_USER


def main() -> None:
    """Show the fixed identity for the local demonstration."""
    # 1. Use the configured demo identity; no sign-in is implemented yet.
    user = DEMO_USER

    # 2. Display identity metadata, without reading any source contents.
    print("Power Desk Morning Brief")
    print(f"Demo user: {user.display_name}")
    print(f"User ID: {user.user_id}")
    print(f"Groups: {', '.join(user.groups)}")
    print("Access checks and brief generation are not implemented yet.")
