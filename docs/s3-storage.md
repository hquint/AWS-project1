# Private S3 storage setup

## Chosen bucket configuration

- Bucket name: `powerdesk-briefings-517777395961-eu-central-1-an`.
- Region: Frankfurt (`eu-central-1`).
- Type: general purpose, account regional namespace.
- Object Ownership: Bucket owner enforced; ACLs disabled.
- Block Public Access: all four settings enabled.
- Versioning: disabled for the prototype.
- Default encryption: SSE-S3, with S3-managed keys.
- Object Lock: disabled.

The bucket name was reported after creation in the console. The configuration above records the settings chosen during setup; bucket-level configuration verification is still pending. The developer ran the first upload command successfully; object contents and SSE-S3 encryption were verified below.

## Developer access policy

Policy JSON: [`infra/iam/powerdesk-s3-briefings-policy.json`](../infra/iam/powerdesk-s3-briefings-policy.json).

Create a customer-managed IAM policy named `PowerDeskS3Briefings`, then attach it to the existing `PowerDeskDevelopers` group. The policy must be attached before the developer profile can use it; keeping a JSON file in Git does not grant AWS permissions. Attachment to `PowerDeskDevelopers` was reported in the console and prefix-listing access was verified below.

The two statements grant:

1. `s3:ListBucket`: list object names only when the request specifies a prefix matching `briefings/*`.
2. `s3:GetObject` and `s3:PutObject`: download and upload objects whose keys begin with `briefings/` in this exact bucket.

S3 displays prefixes like folders, but `briefings/morning-brief.md` is one object key. An empty folder does not need to be created before uploading.

This policy adds no deletion, bucket administration, public-access changes, or permissions to other prefixes or buckets. Other policies attached to the same identity can also grant access; verify the combined permissions when changing this setup.

The developer's S3 console bucket listing may be unavailable because the policy does not grant `s3:ListAllMyBuckets`. The intended access is through Python and the CLI with an explicit bucket and prefix.

For a read-only listing after attachment and developer login:

```bash
aws s3api list-objects-v2 \
  --bucket powerdesk-briefings-517777395961-eu-central-1-an \
  --prefix briefings/ \
  --profile powerdesk \
  --region eu-central-1
```

The Python upload integration and its live verification are described below. See [AWS S3 identity-based policy examples](https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-policies-s3.html).

## Access verification — 11 October 2026

The temporary `powerdesk` login was renewed, and STS confirmed the IAM identity `power-desk-developer`.

- Listing with prefix `briefings/` succeeded and returned zero objects.
- Listing with prefix `other/` returned `AccessDenied`, as intended.
- No upload, deletion, or model inference was performed during these checks.

These checks verify the allowed and denied listing boundaries. Object upload/download verification is documented below. Bucket-level security settings still need separate verification.

## Upload an existing briefing

From the project root, with a valid developer login:

```bash
uv run power-desk-brief \
  --upload-brief outputs/morning-brief.md \
  --s3-bucket powerdesk-briefings-517777395961-eu-central-1-an \
  --aws-profile powerdesk \
  --aws-region eu-central-1
```

The application performs this sequence:

1. `cli.py` loads the synthetic fixtures and finds the current demo user's eligible source IDs.
2. The CLI reads the existing UTF-8 Markdown file and calls `brief_validation.py`. Missing or invalid input fails before any upload.
3. `aws/s3_storage.py` builds the key `briefings/` plus the local filename.
4. Boto3 reads the selected local AWS profile and calls S3 `put_object` with the briefing bytes and Markdown content type. `AES256` requests SSE-S3 encryption. No public ACL is supplied.
5. `IfNoneMatch="*"` requires a new object name; S3 atomically refuses to overwrite an existing object. A different upload requires a differently named local file.
6. The CLI reports the S3 URI without printing the brief. The local file remains in place, and no Bedrock request is made.

The upload command is separate from `--generate-brief` and `--prepare-request`; those options are mutually exclusive. `--s3-bucket` is explicit and required for upload. The default AWS profile and Region are still `powerdesk` and `eu-central-1`. The existing IAM policy grants access only to the chosen bucket's `briefings/` prefix.

Only use fictional demonstration briefings. Structural and citation checks do not prove factual accuracy or detect every kind of sensitive text. Do not use this command to upload real company data.

After a successful upload, open the bucket in the administrator console and select `briefings/`, then `morning-brief.md`. The developer console's bucket list may still be unavailable with the narrow API policy. To inspect object metadata as the developer:

```bash
aws s3api head-object \
  --bucket powerdesk-briefings-517777395961-eu-central-1-an \
  --key briefings/morning-brief.md \
  --profile powerdesk \
  --region eu-central-1 \
  --query '{Bytes:ContentLength,Encryption:ServerSideEncryption}'
```

This should show the file size and `AES256`. A repeat upload with the same name should report that it already exists. If a network error occurs after sending, check whether the object was stored before retrying. The client uses bounded timeouts and makes no automatic retries. AWS error bodies and briefing contents are kept out of application logs.

No live upload was performed by the assistant while implementing this step. Temporary SDK responses were used for manual checks; no unit-test files were added. The developer then ran the live upload, as recorded below. S3 storage/request charges apply when the developer runs the command. See [AWS PutObject documentation](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html) for conditional writes and encryption parameters.

## First live upload verification — 11 October 2026

The developer ran the upload command and supplied a console screenshot showing `briefings/morning-brief.md`, size 583 bytes.

A read-only Boto3 `get_object` request using the `powerdesk` developer profile and the expected bucket owner verified:

- The S3 object is byte-for-byte identical to `outputs/morning-brief.md`.
- Size: 583 bytes.
- Server-side encryption: `AES256` (SSE-S3).
- Content type: `text/markdown; charset=utf-8`.
- The developer identity can download the uploaded object.

No object was modified during verification, and no Bedrock call was made. Overwrite protection was checked with temporary SDK responses during implementation; a second live upload was not attempted.
