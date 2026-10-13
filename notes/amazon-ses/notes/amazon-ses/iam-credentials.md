# Least-Privilege IAM Credentials for Sending

Code running outside AWS (for example on Vercel or another host) needs credentials to call SES. The goal: a credential that can only send email as one address, and nothing else.

## The Policy

**IAM > Policies > Create policy > JSON**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SendContactFormEmail",
      "Effect": "Allow",
      "Action": "ses:SendEmail",
      "Resource": "arn:aws:ses:us-east-1:123456789012:identity/example.com",
      "Condition": {
        "StringEquals": { "ses:FromAddress": "hello@example.com" }
      }
    }
  ]
}
```

- **Action** `ses:SendEmail`: the only thing allowed. No reading, listing or changing settings.
- **Resource**: the identity ARN. It includes the region and your account ID, so the key works nowhere else.
  - If you also have an email-address identity for the sender, add its ARN too. SES authorizes against the most specific identity.
- **Condition** `ses:FromAddress`: even with the key, nobody can send as another address on the domain.
- The review screen lists **SES**, **SES v2** and **Pinpoint Email**. They share the `ses:` prefix, so it's still one permission, applied to all three APIs.
- IAM is global (the region selector shows "Global"). The region restriction comes from the ARN.

## The User and Access Key

1. **IAM > Users > Create user**, for example `website-ses-sender`.
   - Leave **console access unchecked**. This user is for code only.
2. **Attach policies directly** and pick the policy above. Groups are better for people with shared roles. For one machine user, attaching directly is simpler.
3. Open the user, then **Security credentials > Create access key > Application running outside AWS**. Add a description tag.
4. Copy the **Access key ID** and **Secret access key** straight into your host's environment variables and your local `.env` (git-ignored).
   - The secret is shown only once. If you lose it, delete the key and create a new one.
   - Don't download the `.csv`. That's one more copy of the secret to track.
5. Use one user per purpose. Revoking one key then doesn't break anything else, and CloudTrail shows clearly which key did what.

## Environment Variables

```dotenv
SES_REGION=us-east-1
SES_ACCESS_KEY_ID=
SES_SECRET_ACCESS_KEY=
CONTACT_EMAIL=hello@example.com
```

- Vercel reserves `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_REGION`, so use your own prefix there.
- Mark the secret as sensitive in your host's dashboard.
- Containers read `env_file` values only when they're created. After editing `.env`, recreate the container (`docker compose up -d`). A plain `restart` keeps the old values.

## Alternatives to Long-Lived Keys

An access key never expires on its own. The narrow policy limits the damage if it leaks (someone could send email as you until you revoke it). These options avoid storing a key at all:

- **OIDC federation**: the host (Vercel, GitHub Actions and others) issues a short-lived identity token, and AWS trades it for temporary credentials through an IAM role (`sts:AssumeRoleWithWebIdentity`). Nothing secret is stored, but you need to learn an identity provider, a role trust policy and STS.
- **IAM Roles Anywhere**: temporary credentials for machines holding an X.509 certificate from a CA you register. It's meant for servers in your own data center, not serverless hosts.
- **Code running on AWS** (Lambda, ECS, EC2): use the execution role. No keys needed.

## Editing a Policy Later

- **IAM > Policies > (policy) > Edit > JSON**, then **Next > Save changes** with **Set as default version** checked.
- IAM keeps up to 5 versions, and you can roll back from the **Policy versions** tab.
- Changes apply immediately. Existing keys keep working with the new permissions.
