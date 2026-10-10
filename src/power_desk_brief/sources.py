"""Load the fictional briefing sources from local JSON files."""

import json
from pathlib import Path
from typing import Any


def load_sources(data_dir: Path) -> list[dict[str, Any]]:
    """Read source records; report malformed inputs without exposing contents."""
    sources = []
    seen_ids = set()

    # 1. Read only the two expected fixture files.
    for filename, source_type in (("emails.json", "email"), ("news.json", "news")):
        path = data_dir / filename
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            # Never include source text or a JSON excerpt in an error message.
            raise ValueError(f"Cannot read valid JSON from {filename}.") from None

        # 2. Require a list of records with the fields needed by this workflow.
        if not isinstance(records, list):
            raise ValueError(f"{filename} must contain a JSON list.")
        for record in records:
            if not isinstance(record, dict):
                raise ValueError(f"{filename} contains an invalid source record.")
            for field in ("id", "title", "body"):
                value = record.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{filename} has a missing or invalid {field}.")
            if record.get("source_type") != source_type:
                raise ValueError(f"{filename} contains an invalid source_type.")

            # 3. Keep citation IDs unique across both files.
            if record["id"] in seen_ids:
                raise ValueError("Source IDs must be unique across input files.")
            seen_ids.add(record["id"])
            sources.append(record)

    # Access metadata is checked separately, so invalid permissions deny access.
    return sources
