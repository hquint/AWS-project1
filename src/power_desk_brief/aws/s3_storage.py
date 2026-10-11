"""Upload an already checked Markdown briefing to private S3 storage."""

from contextlib import closing

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


def upload_brief(
    text: str,
    filename: str,
    *,
    bucket: str,
    profile: str,
    region: str,
) -> str:
    """Upload a new object under briefings/ and return its S3 URI."""
    # 1. Accept a Markdown filename, keeping every upload in briefings/.
    if (
        not text.strip()
        or not filename.lower().endswith(".md")
        or "/" in filename
        or "\\" in filename
    ):
        raise ValueError("Use a non-empty briefing and a Markdown filename without folders.")
    key = f"briefings/{filename}"

    # 2. Use the same named local profile as Bedrock; credentials stay outside Git.
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        with closing(
            session.client(
                "s3",
                config=Config(
                    connect_timeout=10,
                    read_timeout=60,
                    retries={"mode": "standard", "total_max_attempts": 1},
                ),
            )
        ) as client:
            # 3. Encrypt with S3-managed keys and atomically refuse overwrites.
            # No ACL is supplied: IAM and bucket settings control access.
            client.put_object(
                Bucket=bucket,
                Key=key,
                Body=text.encode("utf-8"),
                ContentType="text/markdown; charset=utf-8",
                ServerSideEncryption="AES256",
                IfNoneMatch="*",
            )
    except ClientError as error:
        # Print only our own messages, never raw AWS errors or briefing content.
        code = error.response.get("Error", {}).get("Code")
        if code == "PreconditionFailed":
            message = "That S3 filename already exists. Use a different local filename."
        elif code == "AccessDenied":
            message = "AWS denied the upload. Check the selected profile and S3 permissions."
        elif code == "NoSuchBucket":
            message = "The S3 bucket was not found. Check --s3-bucket and --aws-region."
        elif code in {"ExpiredToken", "InvalidToken", "InvalidAccessKeyId"}:
            message = "AWS credentials are invalid or expired. Run aws login for the selected profile."
        elif code == "ConditionalRequestConflict":
            message = "Another upload conflicted with this request. Check S3 before trying again."
        else:
            message = "S3 rejected the upload. Check the bucket, Region, and account access."
        raise RuntimeError(message) from None
    except BotoCoreError:
        raise RuntimeError(
            "Cannot connect to S3. Check your connection and profile; "
            "run aws login --profile PROFILE if the session has expired. "
            "If the connection failed after sending, check S3 before trying again."
        ) from None

    # 4. Return the object location without logging its contents.
    return f"s3://{bucket}/{key}"
