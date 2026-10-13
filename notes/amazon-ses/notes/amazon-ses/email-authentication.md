# Email Authentication: SPF, DKIM, DMARC and MAIL FROM

These DNS records prove that mail claiming to come from your domain really does. Without them, mail lands in spam, and anyone can spoof your domain.

## Two "From" Addresses

Every email has two senders:

- **Header From**: the visible `From: hello@example.com` that people see.
- **Envelope sender (MAIL FROM, Return-Path)**: a hidden address where bounces go. SES uses a unique `...@amazonses.com` address per message by default.

## SPF (Sender Policy Framework)

- A TXT record listing which servers may send for a domain. It checks the **envelope sender's** domain, not the visible From.
- Example for a domain whose inbox is Google Workspace and that also sends through Mailchimp:
  ```
  v=spf1 include:_spf.google.com include:servers.mcsv.net ~all
  ```
- A domain can have **only one** `v=spf1` record. Two records make SPF fail. Edit the existing one.
- Endings:
  - `?all`: neutral, effectively no protection.
  - `~all`: softfail, other servers are suspicious. A good default when DMARC does the enforcing.
  - `-all`: hardfail.
- SES doesn't belong in the root SPF record. SPF checks the envelope sender, which for SES is `amazonses.com` or your custom MAIL FROM subdomain.

## DKIM (DomainKeys Identified Mail)

- The sending server signs each email with a private key. Receivers fetch the public key from DNS at `<selector>._domainkey.example.com` and check the signature.
- **SES Easy DKIM**: three CNAMEs pointing to `<token>.dkim.amazonses.com`. Three keys allow rotation without downtime.
- **Google Workspace**: Admin console > Apps > Google Workspace > Gmail > **Authenticate email**. Generate a 2048-bit key with selector `google`, add the TXT record, and only then click **Start authentication**. If you skip this, Google signs with its own default domain, which doesn't count for your domain.
- Long TXT values (a 2048-bit key) are split into 255-character chunks in DNS. That's normal. Receivers join them back together.
- Each sending service needs its own DKIM record (SES, Google, Mailchimp...).

## DMARC

- A TXT record at `_dmarc.example.com` that tells receivers what to do when mail fails, and where to send reports.
- **Alignment** is the key idea: DMARC passes if **SPF or DKIM** passes **for the same domain as the visible From**.
  - SES with Easy DKIM passes through DKIM alone, because the signature is for `example.com`.
  - SPF for `amazonses.com` doesn't count, because it doesn't match `example.com`.
- Rollout:
  1. Start in monitor mode with reports:
     ```
     v=DMARC1; p=none; rua=mailto:dmarc-reports@example.com
     ```
  2. Read the daily aggregate reports (zipped XML from Google, Microsoft, Yahoo...) for about two weeks. Every legitimate sender should show up passing.
  3. Switch to `p=quarantine` (failing mail goes to spam), and later `p=reject` if you want.
- **Check your own mailbox provider first.** Before setting up DKIM and SPF for Google Workspace, everyday Gmail mail from the domain failed DMARC. With `p=quarantine`, the owner's own email would have gone to spam.
- Gmail and Yahoo expect bulk senders to have a DMARC record.

## Custom MAIL FROM Domain (SES)

- Moves the envelope sender from `amazonses.com` to a subdomain like `mail.example.com`, so SPF also passes for your domain. DMARC then passes two ways instead of one.
- SES: **Identities > example.com > Custom MAIL FROM domain > Edit**. Subdomain `mail`, **Behavior on MX failure**: use default MAIL FROM (mail still goes out if the DNS breaks).
- DNS records on the subdomain:

  | Type | Name | Value |
  |---|---|---|
  | MX (priority 10) | `mail` | `feedback-smtp.us-east-1.amazonses.com` |
  | TXT | `mail` | `v=spf1 include:amazonses.com ~all` |

- The MX here only handles bounces for `mail.example.com`. The root MX records for your inbox don't change, even if the DNS provider warns that editing MX records can break email.
- The subdomain must not already be used for something else.

## Reading the Headers

Send a test to an outside inbox, then in Gmail open **Show original** or download the `.eml`, and look at `Authentication-Results`:

```
dkim=pass header.i=@example.com header.s=<selector>
spf=pass  smtp.mailfrom=<id>@mail.example.com
dmarc=pass (p=NONE) header.from=example.com
```

- `header.i=@example.com` on DKIM: the signature is for your domain (aligned).
- `smtp.mailfrom=...@mail.example.com`: the custom MAIL FROM is in use. If it still says `amazonses.com`, check whether an email-address identity is overriding the domain's settings.
- SES messages also carry a second DKIM signature for `amazonses.com`. That's expected.
- The copy in your **Sent** folder has no `Authentication-Results`. Download the received copy.

## Checking DNS From a Terminal

```bash
nslookup -type=TXT example.com 8.8.8.8                    # SPF
nslookup -type=TXT _dmarc.example.com 8.8.8.8             # DMARC
nslookup -type=TXT google._domainkey.example.com 8.8.8.8  # Google DKIM
nslookup -type=MX mail.example.com 8.8.8.8                # MAIL FROM
nslookup -type=TXT example.com <your-authoritative-ns>    # skip caches
```

- Query your DNS provider's own nameserver (from `nslookup -type=NS example.com`) to see a change right away. Public resolvers like `8.8.8.8` serve cached values until the old record's TTL expires.
- A short TTL (30 minutes) while setting up means mistakes are fixed faster.
