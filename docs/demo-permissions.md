# Demo identity and intended permissions

## 1. Who is using the application?

The local demo uses one fictional user, defined in `src/power_desk_brief/identity.py`:

- User ID: `demo-head-of-power`.
- Display name: Bobby Axelrod, Head of Power Trading.
- Group membership: `power-desk` only.

The frozen dataclass keeps this small identity record from being accidentally changed while the workflow runs. It is not a security boundary: anyone able to edit the application can change the demo configuration.

Step 2 defines the identity. Step 3 enforces its permissions when selecting eligible sources. Sign-in is not implemented. A real deployment must obtain verified identity and group membership from a trusted identity provider. A job title, email recipient, or claim in a message must never grant permission.

## 2. What may enter this user's AI briefing workflow?

Step 3 applies these rules when selecting eligible sources. A later model request must use only that eligible list:


| Source classification                                                          | Decision                                                                  |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `public`                                                                       | Eligible without a private group membership.                                       |
| `desk-confidential`                                                            | Eligible only when at least one source `access_groups` entry matches a user group. |
| `restricted`                                                                   | Always excluded from this AI workflow, even if a user group matches.               |
| Missing or unknown classification; missing or invalid required access metadata | Excluded.                                                                          |


For non-public sources, an empty group list grants no access. Permission is determined from trusted fixture metadata, not from the text of the source. These are application-level briefing permissions; they are separate from AWS IAM permissions.

## 3. Examples for the demo user


| Source                     | Result in step 3      | Reason                                                                                                                                    |
| -------------------------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `news-001` and `email-001` | Eligible                       | Public sources.                                                                                                                           |
| `email-002`                | Eligible                       | Its `power-desk` group matches the user.                                                                                                  |
| `email-005`                | Eligible                       | It allows `power-desk` or `risk`; one match is sufficient.                                                                                |
| `email-007`                | Excluded                       | It requires `risk`, which the demo user does not have.                                                                                    |
| `email-008`                | Excluded                       | Restricted, despite its `power-desk` group.                                                                                               |
| `email-009`                | Excluded                       | Restricted.                                                                                                                               |
| `email-010`                | Eligible by access policy only | The group matches, but the embedded instructions remain untrusted. Access eligibility does not make content safe or authorise any action. |


Across the current 14 fixtures, the workflow makes 11 sources eligible and excludes 3. Only source IDs and decision reasons are printed. Prompt-injection handling is a separate later concern.

## 4. Inspect the configured user

From the project root:

```bash
uv run power-desk-brief
```

The command prints the demo user's name, ID, and groups, then loads the fixtures and reports access decisions. It does not print source titles or bodies or call AWS. Run from the project root, or provide `--data-dir` with the fixture directory. Invalid input files stop execution with a short error that does not include source contents.
