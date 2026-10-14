# Writing One Item with Temporary Credentials from an OIDC Role

Code running outside AWS (for example a serverless function on Vercel) can write to DynamoDB without any stored AWS key. Each request trades a short-lived identity token for temporary credentials, then signs the write with them.

## The Flow

1. The host gives each request an **OIDC token** that says which project and environment it comes from (on Vercel, the `x-vercel-oidc-token` header).
2. The code calls **STS `AssumeRoleWithWebIdentity`** with the role ARN and that token. STS checks the role's trust policy and returns temporary credentials: an access key ID, a secret, and a **session token**. Ask for 15 minutes (`DurationSeconds=900`). That's the shortest allowed, and plenty for one request.
3. The code signs a `PutItem` request with those credentials (Signature Version 4, service name `dynamodb`) and sends it.

- Get the credentials **once per request** and reuse them for every AWS call in it, for example sending an email and saving a copy.
- Setting up the identity provider and the role is covered in [Sending with a Vercel OIDC role](../../../amazon-ses/notes/amazon-ses/oidc-role.md).

## The Permission

A separate policy, attached to the role the code already uses:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PutContactMessages",
      "Effect": "Allow",
      "Action": "dynamodb:PutItem",
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/contact-messages",
      "Condition": {
        "StringEqualsIfExists": { "dynamodb:ReturnValues": "NONE" }
      }
    }
  ]
}
```

- **Action** `dynamodb:PutItem`: add or replace one item. No reading, scanning, updating or deleting.
- **Resource**: one table ARN, which includes the region and account ID.
- **Condition** `dynamodb:ReturnValues`: without it, a PutItem can ask for `ALL_OLD` and get back the item it replaced, which turns a write into a read. With it, the role is truly write-only.
- A separate policy leaves the role's other permissions untouched, and each one can be removed on its own.

## The Request

```http
POST https://dynamodb.us-east-1.amazonaws.com/
Content-Type: application/x-amz-json-1.0
X-Amz-Target: DynamoDB_20120810.PutItem
X-Amz-Date: 20261013T120000Z
X-Amz-Security-Token: <session token>
Authorization: AWS4-HMAC-SHA256 Credential=ASIA.../20261013/us-east-1/dynamodb/aws4_request, SignedHeaders=content-type;host;x-amz-date;x-amz-security-token;x-amz-target, Signature=...

{
  "TableName": "contact-messages",
  "Item": {
    "id": { "S": "3f6c2b1e-8a4d-4f7e-9c2a-1b5d7e9f0a12" },
    "createdAt": { "S": "2026-10-13T12:00:00.000Z" },
    "expiresAt": { "N": "1799668800" },
    "email": { "S": "hello@example.com" },
    "message": { "S": "Hi there" }
  }
}
```

- The session token must be sent **and** signed. Temporary credentials fail without it.
- Sign the exact body string you send. Re-serializing it after signing breaks the signature.
- A success is HTTP 200 with an empty `{}`.
- An error body looks like `{"__type":"com.amazonaws.dynamodb.v20120810#ResourceNotFoundException","message":"..."}`. Log only the status and the part after `#`. The message can name the table or echo data.

## When the Item Is Only a Backup

If the main job is something else (here, the email) and the item is a safety copy, the save must never get in the way:

- Run it **after the response** is sent. In Next.js that's `after(() => save())`, which keeps the function alive until the save ends without making the visitor wait.
- Catch every error inside the save and log one line. A missing table or a refused permission then never changes what the visitor sees.
- Store only what you need. A form copy needs the form fields, a time, an ID and an expiry. Skip IP addresses and tokens.

## Checking It Worked

- **DynamoDB > Tables > (table) > Explore table items** lists the items. Open one to see every attribute.
- **CloudTrail > Event history** shows the `AssumeRoleWithWebIdentity` call (a management event), with the token's subject as the user name.
- It does **not** show `PutItem`. Item reads and writes are data events, which CloudTrail logs only if you turn on data events for a trail, and that costs extra. The item itself is the proof.
