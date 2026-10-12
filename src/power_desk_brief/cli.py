"""Run the local briefing workflow from the command line."""

import argparse
import json
import os
from pathlib import Path

from .aws.bedrock_invoke import generate_brief
from .aws.bedrock_request import build_request_body
from .aws.s3_storage import upload_brief
from .brief_validation import validate_brief
from .identity_setup import DEMO_USER
from .source_access import check_access
from .source_loader import load_sources


def main() -> None:
    """Inspect source access, prepare, generate, or upload a briefing."""
    # 1. Select the local input directory and the configured demo identity.
    parser = argparse.ArgumentParser(description="Prepare a power-desk briefing from fictional sources.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/synthetic"),
        help="fixture directory (default: data/synthetic, relative to the working directory)",
    )
    action_options = parser.add_mutually_exclusive_group()
    action_options.add_argument(
        "--prepare-request",
        type=Path,
        metavar="FILE",
        help="save a private request-body JSON file without calling AWS; must be a new file",
    )
    action_options.add_argument(
        "--generate-brief",
        type=Path,
        metavar="FILE",
        help="call AWS and save a private Markdown briefing; must be a new file",
    )
    action_options.add_argument(
        "--upload-brief",
        type=Path,
        metavar="FILE",
        help="check and upload an existing Markdown briefing to S3 without calling Bedrock",
    )
    parser.add_argument("--s3-bucket", help="destination bucket, required with --upload-brief")
    parser.add_argument("--aws-profile", default="powerdesk", help="local AWS profile (default: powerdesk)")
    parser.add_argument("--aws-region", default="eu-central-1", help="AWS Region (default: eu-central-1)")
    parser.add_argument("--model-id", default="eu.amazon.nova-lite-v1:0", help="Bedrock model or inference profile ID")
    args = parser.parse_args()
    if args.upload_brief is not None and not args.s3_bucket:
        parser.error("--s3-bucket is required with --upload-brief.")
    if args.s3_bucket is not None and args.upload_brief is None:
        parser.error("--s3-bucket is only used with --upload-brief.")
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

    # 5. Optionally check and upload an existing brief, then finish without inference.
    if args.upload_brief is not None:
        try:
            brief = args.upload_brief.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            parser.exit(1, "Cannot read the briefing. Use an existing UTF-8 Markdown file.\n")
        try:
            validate_brief(brief, {source["id"] for source in eligible_sources})
            uri = upload_brief(
                brief,
                args.upload_brief.name,
                bucket=args.s3_bucket,
                profile=args.aws_profile,
                region=args.aws_region,
            )
        except (ValueError, RuntimeError) as error:
            parser.exit(1, f"{error}\n")
        print(f"\nUploaded briefing: {uri}")
        print("The local file was kept. No request was sent to Bedrock.")
        return

    # 6. Reserve a new private file before a potentially chargeable model call.
    output_path = args.prepare_request or args.generate_brief
    if output_path is None:
        print("Use --prepare-request FILE, --generate-brief FILE, or --upload-brief FILE --s3-bucket BUCKET.")
        return
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError:
        parser.exit(1, "Cannot create output. Use a new writable output file. No AWS call was made.\n")

    # 7. Prepare offline JSON or call the model using only eligible sources.
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            if args.prepare_request is not None:
                json.dump(build_request_body(eligible_sources, user), file, indent=2, ensure_ascii=False)
                file.write("\n")
            else:
                print(f"\nCalling Bedrock: {args.model_id} in {args.aws_region} (profile: {args.aws_profile})")
                brief, usage = generate_brief(
                    eligible_sources,
                    user,
                    profile=args.aws_profile,
                    region=args.aws_region,
                    model_id=args.model_id,
                )
                # Check application rules locally before saving model output.
                validate_brief(brief, {source["id"] for source in eligible_sources})
                file.write("# Power Desk Morning Brief\n\nFictional demonstration data.\n\n")
                file.write(brief + "\n")
    except (ValueError, RuntimeError, OSError) as error:
        # Remove the new file if generation, validation, or writing fails.
        output_path.unlink(missing_ok=True)
        message = "Cannot write the output file." if isinstance(error, OSError) else str(error)
        parser.exit(1, f"{message}\n")

    # 8. Report paths and usage metadata, keeping source and briefing text out of logs.
    if args.prepare_request is not None:
        print(f"\nPrepared request body: {output_path}")
        print("No request was sent to AWS.")
    else:
        print(f"Saved briefing: {output_path}")
        print(f"Tokens: {usage['inputTokens']} input, {usage['outputTokens']} output")
        print("Format and source IDs checked. Review the briefing for factual accuracy.")
