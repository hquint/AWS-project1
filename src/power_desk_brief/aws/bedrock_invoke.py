"""Call Bedrock and extract the returned briefing text and token counts."""

from contextlib import closing
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from .bedrock_request import build_request_body
from ..identity_setup import DemoUser


def generate_brief(
    sources: list[dict[str, Any]],
    user: DemoUser,
    *,
    profile: str | None,
    region: str,
    model_id: str,
) -> tuple[str, dict[str, int]]:
    """Return model text and token counts using a local profile or the runtime AWS identity."""
    # 1. Recheck access and build the same body used by offline preparation.
    request_body = build_request_body(sources, user)

    # 2. Use a local profile, or runtime role credentials when profile is None.
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        with closing(
            session.client(
                "bedrock-runtime",
                config=Config(
                    connect_timeout=10,
                    read_timeout=90,
                    retries={"mode": "standard", "total_max_attempts": 1},
                ),
            )
        ) as client:
            # 3. Make one non-streaming call; the request has no model tools.
            response = client.converse(modelId=model_id, **request_body)
    except ClientError as error:
        # Do not print AWS error bodies: they can contain request information.
        code = error.response.get("Error", {}).get("Code")
        if code == "AccessDeniedException":
            message = "AWS denied the model call. Check the profile and Bedrock IAM permissions."
        elif code in {
            "ExpiredTokenException", "InvalidClientTokenId", "UnrecognizedClientException"
        }:
            message = "AWS credentials are invalid or expired. Refresh the local login or check the execution role."
        elif code in {"ThrottlingException", "ServiceUnavailableException"}:
            message = "Bedrock is temporarily unavailable or throttled. Try again later."
        else:
            message = "Bedrock rejected the call. Check model availability, Region, and account access."
        raise RuntimeError(message) from None
    except BotoCoreError:
        raise RuntimeError(
            "Cannot connect to AWS. Check the connection and credentials; "
            "refresh the local login or check the execution role."
        ) from None

    # 4. Reject incomplete responses and tool requests before saving anything.
    if response.get("stopReason") != "end_turn":
        raise ValueError("Bedrock did not return a complete briefing. No briefing was saved.")
    message = response.get("output", {}).get("message", {})
    content = message.get("content", [])
    if (
        message.get("role") != "assistant"
        or not content
        or any("text" not in block for block in content)
    ):
        raise ValueError("Bedrock returned an unexpected response. No briefing was saved.")
    text = "\n".join(block["text"] for block in content).strip()
    usage = response.get("usage", {})
    return text, {key: usage.get(key, 0) for key in ("inputTokens", "outputTokens")}
