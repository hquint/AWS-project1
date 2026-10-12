"""Check briefing format and permitted source references locally."""

import re


def validate_brief(text: str, eligible_ids: set[str]) -> None:
    """Check basic format and source references, not factual accuracy."""
    if not text.strip():
        raise ValueError("The briefing is empty.")
    for heading in ("Market developments", "Priority emails", "Follow-up items"):
        if heading.casefold() not in text.casefold():
            raise ValueError("The briefing is missing a required section.")
    bullets = re.findall(r"^\s*[-*]\s+(.+)$", text, re.MULTILINE)
    if not 1 <= len(bullets) <= 8:
        raise ValueError("The briefing must contain between one and eight bullets.")
    # Every bullet needs a citation, and every cited ID must be eligible.
    for bullet in bullets:
        citations = re.findall(r"\[([^\]]+)\]", bullet)
        if not citations:
            raise ValueError("A briefing bullet is missing its source citation.")
        for citation in citations:
            if not set(re.split(r",\s*", citation)).issubset(eligible_ids):
                raise ValueError("The briefing cites an unknown or excluded source.")
    mentioned_ids = set(re.findall(r"\b(?:email|news)-\d+\b", text))
    if not mentioned_ids.issubset(eligible_ids):
        raise ValueError("The briefing refers to an unknown or excluded source.")
