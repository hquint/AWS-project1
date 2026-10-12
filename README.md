# Power Desk Morning Brief

A weekend learning project that simulates an internal AI assistant for a head of power trading in a company with strict data-access controls.

## Intended workflow

Synthetic Outlook emails and power-market news become a concise morning briefing with source references and optional audio.

`Load → Authorise → Filter → Summarise → Validate → Generate optional audio → Save`

## Planned stack

- Python and boto3 for the workflow and AWS integration.
- Amazon Bedrock for model inference.
- Private Amazon S3 storage for approved inputs and generated outputs.
- AWS Lambda for execution, IAM for permissions, and CloudWatch for operational metadata.
- Streamlit for a simple interface and Amazon Polly for optional audio.

## Data and security boundaries

Use fictional data throughout the prototype.

- Public market news can be summarised.
- Desk-confidential content requires an authorised user and an approved model.
- Restricted customer records, contracts, source code, and planted fake secrets must be excluded before model invocation.
- Emails and documents are untrusted source material, never instructions authorising actions.
- Sensitive input and output content must not be written to logs.
- The workflow has no external email-sending capability.

Application controls and IAM alone do not provide full network isolation. Private networking and centrally managed identity are later production considerations.

## Milestones

1. Build a local Python prototype with synthetic fixtures and access-control checks.
2. Generate a source-referenced briefing through Amazon Bedrock.
3. Deploy the workflow to Lambda with private S3 storage and narrow IAM permissions.
4. Add the Streamlit interface and optional Polly audio.
5. Test restricted-data exclusion, prompt injection, logging, and error handling; document the architecture.

Real Outlook integration and autonomous agents are outside the initial prototype scope. AWS Region, model availability, routing, and costs must be checked before deployment.

## Current status

**The first backend prototype is ready for demonstration.** It loads fictional
emails and news, checks the demo user's access, generates a cited briefing using
Bedrock Nova Lite, validates the result, and saves it locally or in private S3
storage. Both the local workflow and a live Lambda run have been exercised.

The user completed a one-time EventBridge Scheduler trial. A read-only check of
the resulting S3 briefing confirmed SSE-S3 encryption and valid format and source
references. CloudWatch logs have seven-day retention, as confirmed by the user.
Manual Lambda runs remain available. The schedule's automatic deletion has not
been independently verified through the developer profile.

Start with the [prototype demo guide](docs/prototype-demo.md) to repeat the demo.
The [Lambda deployment guide](docs/lambda-deployment.md) records configuration
and the first live run. The input data and application identity are fictional;
Streamlit, optional audio, and broader automated tests remain later milestones.

## Python files

- `cli.py`: run the command-line workflow, save requests or briefings, and upload an existing brief.
- `lambda_handler.py`: run the filtered generation and S3 storage workflow inside Lambda using its IAM role.
- `identity_setup.py`: define the fixed fictional user and group membership.
- `source_loader.py`: load and validate the synthetic email and news records.
- `source_access.py`: check which records the demo user may process.
- `brief_validation.py`: check the returned briefing format and permitted source references.
- `aws/bedrock_request.py`: build the AWS Bedrock request from eligible records.
- `aws/bedrock_invoke.py`: use a local profile or runtime role, call Bedrock, and extract the response text and token counts.
- `aws/s3_storage.py`: upload a new briefing object to S3 with encryption and overwrite protection.
- `__init__.py`: identify the Python package; application logic lives in the files above.

These files live in `src/power_desk_brief/`. The `aws/` subpackage contains AWS-specific code; the CLI coordinates local access checks, model invocation, briefing validation, and saving. The demo identity is separate from the AWS identity used to authenticate model calls.

## Development

`main` holds the reviewed project baseline. Initial implementation takes place on `codex/morning-brief-prototype`.

Use Python 3.12 and [uv](https://docs.astral.sh/uv/) to manage the environment and dependencies:

```bash
uv sync --locked
uv run power-desk-brief
```

The command displays the demo user and an access report: 14 sources loaded, 11 eligible, and 3 excluded with the current fixtures. It prints source IDs and decision reasons, without printing source titles or bodies. It does not call AWS or generate a briefing.

Run from the project root, or set an explicit input directory:

```bash
uv run power-desk-brief --data-dir /path/to/data/synthetic
```

The local loader reads all fictional fixture records before filtering. Request preparation accepts only the eligible list and rechecks it; the original loaded list must never be passed to a model. Later AWS storage and IAM controls will also restrict which objects the workflow can read.

Add dependencies with `uv add <package>` and development tools with `uv add --dev <package>`. Commit `pyproject.toml`, `.python-version`, and `uv.lock`; the local `.venv` is ignored.

Keep credentials and real company data out of this repository.

Prepare the model request offline:

```bash
uv run power-desk-brief --prepare-request outputs/bedrock-request.json
```

This saves eligible source text in a new private file; it does not call AWS. See the request preparation guide for the remaining configuration.

Generate a live briefing with the configured developer profile:

```bash
uv run power-desk-brief --generate-brief outputs/morning-brief.md
```

This sends the 11 eligible fictional sources to Amazon Nova Lite and incurs Bedrock usage charges. The Markdown output must be a new file and is ignored by Git. This command saves it on your computer; uploading to S3 is a separate command. This local command does not invoke Lambda. See the live generation guide for configuration, error handling, and validation limits.

Upload the existing brief to the configured private S3 bucket:

```bash
uv run power-desk-brief \
  --upload-brief outputs/morning-brief.md \
  --s3-bucket powerdesk-briefings-517777395961-eu-central-1-an
```

This checks the brief against the current eligible source IDs, then uploads it as `briefings/morning-brief.md`. It does not call Bedrock. Existing object names are refused, and the local file is kept. S3 storage and requests have their own usage charges.

Prepare the Lambda deployment package:

```bash
uv run --locked python scripts/build_lambda_package.py
```

This builds `dist/powerdesk-lambda.zip` for Python 3.12 / Linux x86_64 without
calling AWS. The Lambda handler reuses the source filtering, Bedrock generation,
and validation code, then writes the result directly to S3. See the Lambda guide
for the execution role, environment variables, and console deployment settings.
