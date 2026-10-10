# Prepare the model request offline

## 1. Run the preparation step

From the project root:

```bash
uv run power-desk-brief --prepare-request outputs/bedrock-request.json
```

The command loads and filters the demo records, shows the access report, then saves the request body. The output must be a new file; use a different filename for another run.

`outputs/` is ignored by Git. New output files are created with owner-only permissions (`0600`); a newly created output directory uses `0700`. The JSON contains eligible source text, so treat it as a private artefact. It is not printed to the terminal or sent to AWS.

## 2. Follow the code sequence

`src/power_desk_brief/bedrock_request.py` prepares the input:

1. Recheck source eligibility and refuse the whole request if any source is ineligible.
2. Include only ID, type, timestamp, title, and body; omit sender, recipient, group, and user metadata.
3. Put application instructions in the `system` field and source JSON in a `user` message. Set a maximum of 1,000 output tokens.

The format follows the [Amazon Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html). This file is a request body, not a complete SDK call: the chosen `modelId` must be supplied when invoking Bedrock.

## 3. Handle untrusted content

The instructions request a concise, source-cited Markdown brief and tell the model to ignore commands embedded in source text. `email-010` remains present so we can later observe whether a model follows that instruction.

There is no tool configuration or capability to retrieve files or send emails. Instructions alone do not guarantee resistance to prompt injection or factual accuracy. Live response checks and evaluation are still needed.

The excluded risk email and both restricted records must be absent from the supplied source list. Their fake secret markers must be absent from the prepared body. The malicious email mentions restricted source IDs; those references are untrusted text and do not grant access or include the restricted records themselves.

## 4. Local AWS configuration for the next step

The development connection uses:

- AWS CLI profile: `powerdesk`.
- AWS Region: Frankfurt (`eu-central-1`).
- Model: Amazon Nova Lite, through the `eu.amazon.nova-lite-v1:0` inference profile.
- Authentication: an IAM developer user with MFA and temporary credentials from `aws login`.

Create the local Region setting and sign in with your authorised developer identity:

```bash
aws configure set region eu-central-1 --profile powerdesk
aws login --profile powerdesk
aws sts get-caller-identity --profile powerdesk
```

The configuration and credential cache live in the user's `.aws` directory, outside this repository. Never put credentials in source code, request JSON, or chat. See [AWS CLI login documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html) for credential refresh and login session expiry.

Read-only access to the inference profile has been verified. Its current destination Regions are Frankfurt, Stockholm, Ireland, and Paris; inference is not confined to Germany. See [AWS Nova Lite model details](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-lite.html). An actual model call is still needed to verify invocation access.

Live inference, output validation, and generated briefing storage are the next implementation step. Offline request preparation needs no AWS credentials and creates no AWS resources.
