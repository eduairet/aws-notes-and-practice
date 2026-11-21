# Contact Messages

Practice for the DynamoDB notes: [Tables, Keys, Time to Live and Pricing](../../../../notes/amazon-dynamodb/notes/amazon-dynamodb/basics.md) and [Writing One Item with Temporary Credentials](../../../../notes/amazon-dynamodb/notes/amazon-dynamodb/put-item-oidc-role.md).

[`contact-messages/template.yaml`](contact-messages/template.yaml) creates:

- **`ContactMessagesTable`**: the small table from the notes.
  - On-demand billing.
  - Partition key `id` (string), with no sort key.
  - TTL on `expiresAt`.
  - Deletion protection on.
- **`SaveMessageFunction`**: writes one message per call.
  - The key is a random UUID, so two writes never collide.
  - `expiresAt` is a **Number** in Unix epoch **seconds**, 90 days out.
  - It never asks for `ReturnValues`.
  - Its role can only `dynamodb:PutItem` on this table.
- **`ContactWriterRole`**: stands in for the notes' OIDC role. Code outside AWS assumes it and gets 15-minute credentials that can only add items. The tests use `sts:AssumeRole`, because the emulator can't check a real OIDC token from Vercel. What comes back is the same kind of credentials: access key, secret and **session token**.

## The Write-Only Condition

Both policies carry the condition from the notes, which makes them truly write-only. Without it, a `PutItem` can ask for `ReturnValues: ALL_OLD` and read back the item it replaced:

```yaml
Condition:
  StringEqualsIfExists:
    dynamodb:ReturnValues: NONE
```

- It's on by default (parameter `EnforceWriteOnly`).
- The AWS Emulator evaluates this condition wrongly: it denies even a plain `PutItem`. So the test run deploys with `EnforceWriteOnly=false`, set in `samconfig.toml` under `[emulator.deploy.parameters]`.
- The test that checks `ALL_OLD` is denied is marked `real_aws_only`. It's skipped on the emulator and runs against a real deployment.

## Run It

```bash
cd contact-messages
sam build
sam deploy --guided                         # real AWS
sam remote invoke SaveMessageFunction --event-file events/event.json
```

Deletion protection blocks `sam delete`. Turn it off first: `sam deploy --parameter-overrides DeletionProtection=false`, then `sam delete`.

Or run it against the local emulator, with the other practice projects: `docker compose run --rm practice-tests` from the repo root.

## Tests

- `tests/unit`: the item's shape (types, and TTL in seconds) and the handler's validation, with a mocked client.
- `tests/integration`: against the deployed stack. Covers the saved item, TTL, replace-on-same-key, what the writer role's temporary credentials can and can't do, and deletion protection.
