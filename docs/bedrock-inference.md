# Generate a live Bedrock briefing

## 1. Run from the project root

```bash
uv sync --locked
uv run power-desk-brief --generate-brief outputs/morning-brief.md
```

The defaults are AWS profile `powerdesk`, source Region `eu-central-1`, and inference profile `eu.amazon.nova-lite-v1:0`. You can set `--aws-profile`, `--aws-region`, or `--model-id` explicitly when needed; the selected identity must have permission for that model and routing configuration.

Every generation sends eligible source text to AWS and incurs model usage charges. EU inference can route outside Germany. The default command and `--prepare-request FILE` still work offline.

The output must be a new file. An existing file is refused before calling AWS; choose another filename for subsequent runs. New files use owner-only permissions (`0600`), and a newly created output directory uses `0700`. `outputs/` is ignored by Git. The CLI reports source IDs, decisions, output path, and token counts without printing source bodies or briefing text.

## 2. Follow the Python sequence

1. `cli.py` loads the fixtures and filters the sources using the demo identity.
2. The CLI reserves a new private output file before calling the model.
3. `aws/bedrock_invoke.py` calls `build_request_body`, in `aws/bedrock_request.py`, which rechecks access and includes only eligible source fields.
4. `boto3.Session(profile_name=..., region_name=...)` reads the local AWS configuration. Python uses the same temporary login credentials as the CLI; it does not launch the CLI or copy credentials into the project.
5. The `bedrock-runtime` client calls `converse(modelId=..., **request_body)`. There are no model tools and no automatic inference retries.
6. The AWS module rejects incomplete or non-text responses. Back in the CLI, `brief_validation.py` checks the three requested sections and one to eight bullets with citations to eligible source IDs. Unknown or excluded source IDs are refused.
7. The CLI writes the checked Markdown locally with a fictional-data label and prints token counts. On handled generation or validation failure, it removes the new output file.

`boto3[crt]` includes support required for console-login credentials. See [Boto3 setup](https://docs.aws.amazon.com/boto3/latest/guide/quickstart.html), [the login credential provider](https://docs.aws.amazon.com/sdkref/latest/guide/feature-login-credentials.html), and [the Converse method](https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse.html).

## 3. Handle common failures

If the login session has expired, sign in again as the IAM developer user:

```bash
aws login --profile powerdesk
aws sts get-caller-identity --profile powerdesk --query Arn --output text
```

For an access denial, check the selected identity and permissions for both the inference profile and its destination models. For a transient service error, try again later. If format validation fails, no briefing is saved; a later manual attempt is another chargeable call. AWS error bodies are not printed by the application.

## 4. Review the result

These checks establish format and permitted source references. They cannot prove that each claim is supported by its citation, that the summary is complete, or that prompt injection is always resisted. Review the brief against the fictional fixtures. Restricted records are removed before inference, and the model has no capability to retrieve them or send emails.

The demo application user and AWS login identity remain separate. Centrally managed application identity, S3, Lambda, and broader testing are later steps; no AWS storage or compute resources are created here.
