# Synthetic briefing inputs

All people, companies, addresses, figures, market events, and secret markers in these fixtures are fictional. The scenario is a morning briefing on 9 October 2026. Timestamps use Berlin's offset for that date (`+02:00`).

## 1. Files

- `emails.json`: 10 emails, including operational requests, desk observations, a routine meeting change, an inaccessible risk-team email, two restricted records, and a malicious instruction example.
- `news.json`: 4 public power-market news items, including two separate generation-unit notices that should not be confused.

These files are static inputs only. A fixed fictional user and the intended permission rules are described in [demo permissions](../../docs/demo-permissions.md). Loading, filtering, and summarisation will be implemented in later steps.

## 2. Fields

| Field | Purpose |
| --- | --- |
| `id` | Stable reference for citations and later checks. |
| `source_type` | `email` or `news`. |
| `timestamp` | Time the message or update was published, with timezone offset. |
| `title` | Email subject or news headline. |
| `classification` | Data-handling label described below. |
| `access_groups` | Groups allowed to read non-public source material; public records use an empty list. |
| `body` | The source text, always treated as untrusted data. |

Emails also include fictional `sender` and `recipients` fields. News includes `source_name`. Email recipients provide context; they do not grant application access.

## 3. Classification labels

- `public`: intended to be eligible for summarisation without a private group membership.
- `desk-confidential`: internal content intended to require membership of a group listed in `access_groups`. For simplicity this prototype uses one internal label, including the risk-team-only record.
- `restricted`: excluded from this AI workflow, regardless of group membership or whether the user may read the original source.

These labels describe the policy we will implement; the files do not enforce it. They are manually assigned fixture metadata, not labels extracted from message text. In a real application, classification and permissions must come from a trusted system rather than from a sender's claims. Later access checks should reject unknown or missing labels.

## 4. Cases to inspect

1. `email-003` has an action request and a deadline; `email-006` is a lower-priority scheduling update.
2. `email-007` is internal but only for the `risk` group. A user with only `power-desk` membership should not receive it.
3. `email-008` includes `power-desk` in its groups but remains restricted. Reading permission is not permission to process it with the model.
4. `email-008` and `email-009` contain fake secret markers beginning with `DEMO_ONLY_`. We can later check whether those markers reach prompts, outputs, or logs.
5. `email-010` requests restricted records and external disclosure. This is deliberate prompt-injection content, not an authorised action. Its internal classification does not make its instructions trustworthy.
6. `news-002` and `news-004` concern different generating units. A later briefing must preserve that distinction.

The restricted examples are committed here only because they are fictional. This is not an example of where to store real restricted data or how to isolate it in AWS.
