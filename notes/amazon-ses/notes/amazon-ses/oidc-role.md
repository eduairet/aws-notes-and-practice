# Sending with a Vercel OIDC Role Instead of an Access Key

The [IAM credentials note](iam-credentials.md) used a long-lived access key. This replaces it with OIDC federation: each request trades a short-lived token from Vercel for 15-minute AWS credentials. No AWS secret is stored anywhere.

## How It Works

1. Vercel gives each function request an **OIDC token**, a signed statement of which team, project and environment the request comes from. Route handlers get it in the `x-vercel-oidc-token` request header.
2. The code sends that token to **STS `AssumeRoleWithWebIdentity`** with the ARN of an IAM role.
3. STS checks the token's signature against the **identity provider** you registered, and checks its claims against the role's **trust policy**.
4. If both pass, STS returns temporary credentials: an access key ID (starting with `ASIA`), a secret, and a session token.
5. The code signs the SES request with them, including the session token.

- Locally there is no token, so sends fail by design. Tests stub AWS instead.

## 1. Register Vercel as an Identity Provider

**IAM > Identity providers > Add provider > OpenID Connect**:

- **Provider URL**: `https://oidc.vercel.com/my-team`. This is for Vercel's **Team** issuer mode. In Global mode it's `https://oidc.vercel.com`.
- **Audience**: `https://vercel.com/my-team`.
- Do this once per AWS account. Every role that trusts Vercel reuses it.

## 2. Create the Role

**IAM > Roles > Create role > Web identity**, pick the provider and audience above, then replace the trust policy with an exact one:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.vercel.com/my-team"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.vercel.com/my-team:aud": "https://vercel.com/my-team",
          "oidc.vercel.com/my-team:sub": [
            "owner:my-team:project:my-project:environment:production",
            "owner:my-team:project:my-project:environment:preview"
          ]
        }
      }
    }
  ]
}
```

- **`aud`**: the token must be meant for your team.
- **`sub`**: only this project's production and preview deployments can assume the role. A list means "any of these".
  - Leave out `preview` if previews should never send real email. Keeping it lets you test on a preview first.
  - Vercel's docs also show a looser version with `StringLike` and `project:*`, which trusts every project in the team. The exact form is safer.
- **Permissions**: attach the same `SendEmail` policy the access key's user had. The role replaces the user, not the policy.
- Leave **Maximum session duration** at 1 hour. The code asks for less.

## 3. Point the Site at the Role

```dotenv
SES_REGION=us-east-1
SES_ROLE_ARN=arn:aws:iam::123456789012:role/website-ses-role
CONTACT_EMAIL=hello@example.com
```

- Vercel reserves `AWS_*` names, so use your own prefix.
- Set the variables on **Production** and **Preview** only, the same environments the trust policy allows.
- The role ARN isn't a secret. The trust policy is what protects the role.

## 4. Call STS

`AssumeRoleWithWebIdentity` needs no AWS signature, because the web identity token is the credential. A plain form POST works:

```http
POST https://sts.us-east-1.amazonaws.com/
Content-Type: application/x-www-form-urlencoded

Action=AssumeRoleWithWebIdentity&Version=2011-06-15
&RoleArn=arn:aws:iam::123456789012:role/website-ses-role
&RoleSessionName=website-contact
&WebIdentityToken=<token from x-vercel-oidc-token>
&DurationSeconds=900
```

- The reply is XML. Read `AccessKeyId`, `SecretAccessKey` and `SessionToken` from it. On failure, log only the HTTP status and the `<Code>`, since the message can include the role ARN.
- `DurationSeconds=900` (15 minutes) is the shortest allowed and plenty for one request.
- Use the regional endpoint in the same region as SES.
- Get the credentials once per request and reuse them for every AWS call in it.

## 5. Sign with Temporary Credentials

- Sign as usual with Signature Version 4, and add the session token as the `X-Amz-Security-Token` header. Include it in the signed headers.
- Without the session token, AWS rejects temporary credentials.

## 6. Roll Out Without Breaking Email

1. Keep the access key path as a fallback: use the role only when `SES_ROLE_ARN` is set. Each Vercel environment then switches on its own, and removing the variable rolls back.
2. Set `SES_ROLE_ARN` on **Preview**, deploy a preview and send one test. If the form uses reCAPTCHA with a domain list, add the preview's hostname for the test and remove it after.
3. Set it on **Production** before the production build, then send one real message.
4. Confirm the role was used in **CloudTrail > Event history**, filtered by event name `AssumeRoleWithWebIdentity`:
   - **User name** is the token's `sub`, for example `owner:my-team:project:my-project:environment:production`.
   - `requestParameters` shows the role ARN, the session name and `durationSeconds: 900`.
   - The event shows part of a session token. It expires in 15 minutes, but don't share screenshots of it publicly.
5. **Deactivate** the old access key (don't delete it yet) and send another message. If it still arrives, nothing depends on the key.
6. Delete the IAM user and its key, remove the key variables from the host and from `.env`, then remove the fallback from the code.

## Why Bother

- **Nothing to leak**: no secret sits in the host's settings, in `.env` files or in a password manager.
- **Short-lived**: stolen credentials stop working after 15 minutes.
- **Scoped by deployment**: a token from another project, or from local development, can't assume the role.
- **Visible**: every exchange shows in CloudTrail with the project and environment as the user name.
