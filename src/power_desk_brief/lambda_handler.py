"""Run the fictional briefing workflow inside AWS Lambda."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .aws.bedrock_invoke import generate_brief
from .aws.s3_storage import upload_brief
from .brief_validation import validate_brief
from .identity_setup import DEMO_USER
from .source_access import check_access
from .source_loader import load_sources


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Generate one briefing; return operational metadata without its contents."""
    # 1. Read deployment settings, never permissions or source text from the event.
    # The first version ignores the trigger payload and always uses our demo user.
    bucket = os.environ.get("S3_BUCKET", "").strip()
    if not bucket:
        raise ValueError("Configure S3_BUCKET before running the function.")
    region = os.environ.get("AWS_REGION", "eu-central-1")
    model_id = os.environ.get("MODEL_ID", "eu.amazon.nova-lite-v1:0")

    # 2. Load packaged fictional fixtures and exclude unauthorised records.
    data_dir = Path(__file__).resolve().parent.parent / "data" / "synthetic"
    sources = load_sources(data_dir)
    eligible = [source for source in sources if check_access(source, DEMO_USER)[0]]
    if not eligible:
        raise ValueError("No eligible sources are available. No model call was made.")

    # 3. Call Bedrock with Lambda's role credentials; there is no local profile.
    brief, usage = generate_brief(
        eligible, DEMO_USER, profile=None, region=region, model_id=model_id
    )

    # 4. Check format and source references before writing anything to S3.
    validate_brief(brief, {source["id"] for source in eligible})
    text = "# Power Desk Morning Brief\n\nFictional demonstration data.\n\n" + brief + "\n"

    # 5. Use a unique name for each invocation and keep overwrite protection.
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"morning-brief-{timestamp}-{context.aws_request_id}.md"
    uri = upload_brief(text, filename, bucket=bucket, profile=None, region=region)

    # 6. Log and return only counts, token usage, and the output location.
    result = {
        "s3_uri": uri,
        "loaded_sources": len(sources),
        "eligible_sources": len(eligible),
        "excluded_sources": len(sources) - len(eligible),
        "input_tokens": usage["inputTokens"],
        "output_tokens": usage["outputTokens"],
    }
    print(json.dumps(result))
    return result
