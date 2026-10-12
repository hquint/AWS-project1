# First prototype: Power Desk Morning Brief

## What works

The fictional briefing workflow runs both locally and in AWS Lambda:

`Load fictional sources → filter access → call Nova Lite → check the response → save Markdown`

- Local entry point: `uv run power-desk-brief`.
- AWS entry point: `power_desk_brief.lambda_handler.handler`.
- Lambda function: `powerdesk-morning-brief`, Frankfurt (`eu-central-1`).
- Model: Amazon Bedrock EU Nova Lite inference profile `eu.amazon.nova-lite-v1:0`.
- Storage: private S3 bucket `powerdesk-briefings-517777395961-eu-central-1-an`, under `briefings/`.
- Operational logs: `/aws/lambda/powerdesk-morning-brief`, with seven-day retention confirmed by the user.

AWS authentication and the fixed fictional application identity are separate.
Local runs use the `powerdesk` profile. Lambda uses its execution role.
The application removes ineligible records before inference and checks the
returned format and citation IDs before storing a briefing. These checks do not
prove factual accuracy or complete resistance to malicious source instructions.

## Repeat the demo manually

1. In the Frankfurt Lambda console, open `powerdesk-morning-brief`.
2. Select the private test event `manual-briefing`, with JSON `{}`.
3. Run Test once. This incurs AWS usage and may create a new output object.
4. Check the execution result: normally 14 loaded, 11 eligible, and 3 excluded.
5. Follow the returned S3 location and download the Markdown briefing.
6. Compare its claims with the fictional fixture records.
7. Inspect CloudWatch for operational counts and token usage; our code excludes source and briefing bodies from logs.

Each invocation uses the fictional inputs bundled in the ZIP. To change those
inputs or application code, rebuild and upload the deployment package:

```bash
uv run --locked python scripts/build_lambda_package.py
```

Use Python 3.12 and the x86_64 architecture for the current ZIP. Configure
`S3_BUCKET` and `MODEL_ID` as described in `docs/lambda-deployment.md`.

## Verification recorded on 12 October 2026

The first live manual Lambda run succeeded on 11 October. The user subsequently
reported that the one-time scheduled job ran and that the previous output files
were deleted. A read-only S3 check found the following remaining output:

- Key: `briefings/morning-brief-20261011T180021Z-296acbce-a05f-40da-af5e-82bfdab0f007.md`.
- Last modified: 11 October 2026, 20:00:23 Europe/Berlin (18:00:23 UTC).
- Size: 614 bytes.
- Encryption: SSE-S3 (`AES256`).
- Content type: `text/markdown; charset=utf-8`.

A downloaded copy passed the prototype's basic format and citation checks:
three required sections, eight cited bullets, only eligible source IDs, and no
planted restricted markers. This verification made no model calls or uploads.
The user confirmed changing the EventBridge test schedule after the original
12 October 07:00 plan. The new S3 object records the actual output time above.
The schedule was configured for one-time execution with deletion after
completion; its final removal has not been independently checked because the
developer role cannot read Scheduler settings.

## Scope of this first prototype

This is a working backend demonstration with fictional inputs and a fixed demo
user. It does not yet include real Outlook feeds, centrally verified application
identity, a trader-facing interface, audio, or production network isolation.
Unit tests remain deferred at the user's request. The configured schedule is a
one-time experiment; ongoing automatic runs are not part of this baseline.
