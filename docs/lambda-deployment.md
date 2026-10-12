# Run the fictional workflow in Lambda

## Current deployment

The deployment ZIP is `dist/powerdesk-lambda.zip`. It is generated and ignored by Git.
The user deployed `powerdesk-morning-brief` in Frankfurt through the AWS console
and successfully invoked it with the private `manual-briefing` test event (`{}`).
The execution-result and S3 screenshots confirm the first cloud run and output.
The user subsequently completed a one-time EventBridge Scheduler trial.
See [the prototype demo guide](prototype-demo.md) for the later read-only output
verification and how to repeat the demo manually.

The user created `PowerDeskBriefLambdaRole` in IAM and attached the existing
`PowerDeskBedrockNovaLite`, `PowerDeskS3Briefings`, and AWS-managed
`AWSLambdaBasicExecutionRole` policies. The successful invocation demonstrates working
Bedrock invocation and S3 write permissions. The complete role policy and trust
configuration have not been independently retrieved.

## Follow the Python sequence

1. AWS calls `power_desk_brief.lambda_handler.handler` with an event and runtime context.
2. `lambda_handler.py` reads deployment configuration and uses the fixed fictional
   user in `identity_setup.py`. It ignores event payload fields, so the trigger
   cannot supply permissions, identity, model selection, bucket, or source text.
3. `source_loader.py` reads the two JSON fixtures bundled inside the deployment.
   `source_access.py` filters the 14 records to 11 eligible records.
4. `aws/bedrock_invoke.py` uses `profile=None` to obtain runtime role credentials.
   `aws/bedrock_request.py` rechecks access before sending eligible records to Nova Lite.
5. `brief_validation.py` checks the returned Markdown and permitted citation IDs.
   A failed check stops the workflow before upload. These checks do not establish
   factual accuracy or complete prompt-injection resistance.
6. `aws/s3_storage.py` writes the validated brief directly to S3 using role
   credentials, SSE-S3, and the existing conditional overwrite protection.
   Object names contain a UTC timestamp and Lambda request ID:
   `briefings/morning-brief-<timestamp>-<request-id>.md`.
7. Lambda returns and logs only counts, token usage, and the S3 URI. Source bodies,
   briefing text, credentials, and trigger payloads are not logged by our code.

The packaged fixtures include all fictional records, including the excluded
records used to demonstrate filtering. They are not production data. Restricted
records are filtered in the application before inference; this does not constitute
separate storage isolation. Real Outlook integration remains outside this step.

## Rebuild with uv

From the repository root:

```bash
uv run --locked python scripts/build_lambda_package.py
```

The script exports dependency versions and hashes from `uv.lock`, installs
Python 3.12 Linux x86_64 wheels into a fresh temporary directory, copies the
application and the two fictional JSON fixtures, and writes the ZIP. It includes
Boto3 and its dependencies instead of relying on the runtime's SDK version.
It does not copy the macOS virtual environment, credentials, generated briefs,
or repository metadata. No Docker build is needed for the available wheels.

The build needs uv on PATH and may download dependencies from PyPI. The local
`boto3[crt]` dependency is included using its Linux wheel rather than its macOS
binary. Do not change the Lambda architecture to arm64 without changing and
rebuilding the package for that architecture.

See [AWS Python deployment packages](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html).

## Console deployment settings

The user applied the following settings during the guided console deployment:

| Setting | Value |
| --- | --- |
| Region | Frankfurt (`eu-central-1`) |
| Function name | `powerdesk-morning-brief` |
| Runtime | Python 3.12 |
| Architecture | x86_64 |
| Execution role | `PowerDeskBriefLambdaRole` |
| Handler | `power_desk_brief.lambda_handler.handler` |
| Memory | 256 MB |
| Timeout | 180 seconds |
| Environment variable `S3_BUCKET` | `powerdesk-briefings-517777395961-eu-central-1-an` |
| Environment variable `MODEL_ID` | `eu.amazon.nova-lite-v1:0` |

`AWS_REGION` is supplied by Lambda; do not manually add it as an environment
variable. No profile name or access keys are configured in Lambda.
The user confirmed seven-day retention for
`/aws/lambda/powerdesk-morning-brief`. This setting was reported through the
guided console workflow, not independently read through the AWS API.

To run manually, use the private `manual-briefing` console test event (`{}`). Each invocation
calls Bedrock and, if validation succeeds, creates a new S3 object. Distinct
invocations are separate chargeable runs; this first version does not deduplicate
repeated events. Lambda execution and CloudWatch logging can also incur charges.
The one-time Scheduler trial used `PowerDeskBriefSchedulerRole` to invoke this
function with `{}`, with schedule deletion after completion and Scheduler
retries off. The console guide also requested Lambda asynchronous retry attempts
`0`. Scheduler removal and the final retry settings have not been independently
retrieved through the developer profile. Scheduled delivery does not provide an
exactly-once guarantee; this prototype does not deduplicate events.

See [AWS asynchronous invocation settings](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-configuring.html).

## Local validation completed

A temporary manual check imported the handler from the extracted ZIP and
simulated Bedrock and S3 responses. It confirmed the eligible record IDs,
restricted-content exclusion from the request, role credential selection,
validation before upload, metadata-only logs, missing-configuration rejection,
and continued local profile support. The ZIP integrity, root package layout,
Linux native-library format, and size were checked.
No unit test files were added and the local checks made no live AWS requests.
The subsequent user-triggered Lambda invocation successfully exercised the
deployment on Linux and its Bedrock and S3 integrations.


## First live run: 11 October 2026

The user supplied an execution-result screenshot with status Succeeded:

- Request ID: `cb7d4c52-3dbf-4855-abb7-90d1f06f4944`.
- Sources: 14 loaded, 11 eligible, 3 excluded.
- Bedrock usage: 1,441 input tokens and 167 output tokens.
- Execution duration: 3,437.77 ms; billed duration: 4,332 ms.
- Initialisation: 894.19 ms.
- Memory: 256 MB configured, 109 MB maximum used.
- Output key: `briefings/morning-brief-20261011T135101Z-cb7d4c52-3dbf-4855-abb7-90d1f06f4944.md`.

A separate S3 screenshot confirmed that new object exists, is 578 bytes, and
uses S3 Standard. The earlier local upload `briefings/morning-brief.md` was
583 bytes. The user later deleted the previous output objects before the
scheduled trial. The visible execution logs contain only request/runtime information
and the application's counts, token usage, and S3 location. The first manual output was not independently downloaded during that
verification. A later scheduled-trial output was read back and checked; see
[the prototype demo guide](prototype-demo.md). Review the downloaded brief
against the fictional fixtures for factual accuracy.
