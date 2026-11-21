# Contact Form

Practice for the SES notes ([setup](../../../../notes/amazon-ses/notes/amazon-ses/setup.md) and [least-privilege IAM credentials](../../../../notes/amazon-ses/notes/amazon-ses/iam-credentials.md)), plus the DynamoDB note's "[when the item is only a backup](../../../../notes/amazon-dynamodb/notes/amazon-dynamodb/put-item-oidc-role.md#when-the-item-is-only-a-backup)" idea.

[`contact-form/template.yaml`](contact-form/template.yaml) creates:

- **`SenderIdentity`**: the SES domain identity, `SenderDomain`. SES verifies it once its DKIM records resolve.
  - If the domain is already an identity in your account, deploy with `CreateSenderIdentity=false`.
- **`ContactFormFunction`**: it validates the form, then:
  1. Sends one email with SES v2 `SendEmail`, from `FromAddress` to `ContactEmail`. Reply-To is the visitor, so hitting Reply just works.
  2. Saves a backup copy to `MessageCopiesTable`, with TTL. This step catches every error and logs one line with the error code only. A missing table or a refused permission never changes the response.
  - If SES refuses the send, the function returns 502 and logs only the HTTP status and the error type, because SES messages can include addresses.
- **The function's IAM policy** is the one from the IAM note:
  - `ses:SendEmail` on the identity ARN only.
  - Condition `ses:FromAddress` equal to `FromAddress`.
  - Plus `dynamodb:PutItem` on the copies table.

## Differences from Real AWS

The AWS Emulator verifies a domain identity by itself after a few seconds and accepts the send. These real-AWS rules are **not** enforced by the emulator, so check them yourself after a real deployment:

- **Sandbox**: a new account can only send to verified addresses, so `ContactEmail` must be verified too.
- **The `ses:FromAddress` condition**: on AWS, sending as any other address is denied.
- **Configuration sets**: if a default configuration set applies to the identity, SES also checks `ses:SendEmail` on the configuration set's ARN. A missing ARN gives the 403 `AccessDeniedException` described in the IAM note. Add the ARN to `Resource` in that case.

## Run It

```bash
cd contact-form
sam build
sam deploy --guided --parameter-overrides SenderDomain=yourdomain.com FromAddress=hello@yourdomain.com ContactEmail=you@yourdomain.com
sam remote invoke ContactFormFunction --event-file events/event.json
```

On real AWS, the domain must be verified first. Add the three DKIM CNAME records from the SES console, then wait for the identity to show **Verified**.

Or run it against the local emulator, with the other practice projects: `docker compose run --rm practice-tests` from the repo root.

## Tests

- `tests/unit`, with mocked clients:
  - What gets sent (From, To, Reply-To) and the copy's TTL.
  - A failed copy (missing table or access denied) still returns 200, and its log line has no form data.
  - A refused send returns 502.
- `tests/integration`: waits for SES to verify the domain, sends through the deployed function, and checks that the copy was saved.
