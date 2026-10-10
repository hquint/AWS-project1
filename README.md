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

The uv-managed Python package and command-line entry point are ready. Step 1 adds 10 fictional emails and 4 fictional market-news items in `data/synthetic/`; see [the fixture guide](data/synthetic/README.md) for their fields and classification labels. Step 2 defines a fixed fictional desk user; see [demo permissions](docs/demo-permissions.md) for the access rules. Step 3 loads the fixtures and enforces those rules, reporting eligible and excluded source IDs with reasons. Step 4 prepares an offline Bedrock request body from eligible sources; see [request preparation](docs/bedrock-request.md). Live inference and AWS deployment have not been implemented yet.

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
