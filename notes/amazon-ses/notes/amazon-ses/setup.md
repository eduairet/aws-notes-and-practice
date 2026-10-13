# Setting up SES for a Domain

Walkthrough for sending email from `hello@example.com` through SES, for a low-volume use like a website contact form.

## Key Concepts

- **Region**: SES settings (identities, quotas, sandbox status) are per region. Pick one and do every step there. A good default is the region closest to where your code runs.
- **Identity**: proof that you own an address or a domain. SES only sends as verified identities.
  - **Email address identity**: verified by clicking a link SES emails you. Covers that one address.
  - **Domain identity**: verified with DNS records. Covers every address on the domain.
- **Sandbox**: every new account starts here. You can only send to verified addresses, with a small daily quota (200 emails per day and 1 per second when I set it up). You leave it by requesting production access.

## Steps

1. Sign in to the console with an admin IAM user or an IAM Identity Center role, not the root user.
2. Select the region (for example `us-east-1`) and open **Amazon SES**. The first visit opens a setup wizard.
3. **Add your email address**: SES sends a verification link to it. Click it.
4. **Add your sending domain**: enter `example.com`.
   - Leave **Custom MAIL FROM domain** empty for now. It can be added later (see [email authentication](email-authentication.md)).
5. **Select pricing plan**: as of October 2026 there are plans (Essentials, Pro, Enterprise) and an à la carte option.
   - Essentials has no monthly fee and charges per email. Pro and Enterprise add a fixed monthly fee per account and region.
   - For a contact form, Essentials or à la carte cost a few cents a month. Check the [pricing page](https://aws.amazon.com/ses/pricing/) for current numbers.
6. **Deliverability enhancements**:
   - **Virtual Deliverability Manager (VDM)**: dashboard for delivery, bounce and complaint rates, plus an advisor. Included in Essentials.
   - **Engagement tracking**: adds a tracking pixel and rewrites links to count opens and clicks. Turn it off for transactional mail. It doesn't help, it's not kind to the recipient, and the pixel doesn't work in plain-text emails anyway.
   - **Optimized shared delivery**: SES picks the best shared IP for each send. Keep it on.
   - **Auto Validation**: checks recipient addresses before sending and skips likely-invalid ones. Very cheap per check, and useful when users type their own address into a form.
7. Skip **Dedicated IP pool** (monthly cost, only for large senders) and **Tenant management** (for apps that send for many customers).
8. Review and click **Get started**.

## Verify the Domain (DKIM)

1. Go to **Configuration > Identities > example.com > Authentication** and expand **Publish DNS records**.
2. Add the three **CNAME** records at your DNS provider:
   - Name: `<token>._domainkey.example.com`
   - Value: `<token>.dkim.amazonses.com`
3. Watch out: many DNS providers append the domain to the **Name** field automatically. Enter only `<token>._domainkey`, or you'll end up with `<token>._domainkey.example.com.example.com` and verification never passes.
4. SES checks DNS on its own. The identity changes to **Verified** within minutes (up to 72 hours).
5. Check the records yourself:
   ```bash
   nslookup -type=CNAME <token>._domainkey.example.com 8.8.8.8
   ```

## Send a Test Email

1. **Identities > Send test email**, from `hello@example.com`.
2. Send it to an inbox **outside** your own domain's mail provider. Mail from your domain to itself may be delivered internally, which skips the authentication checks (or hides the message in an old thread).
3. Use a unique subject so it doesn't get threaded with older tests.
4. In Gmail, open **Show original** or download the `.eml` and read the `Authentication-Results` header. See [email authentication](email-authentication.md#reading-the-headers).

## Request Production Access

1. **Get set up > Request production access** (enabled once the domain is verified).
2. Fill in:
   - **Mail type**: Transactional (sent because a user did something) or Marketing.
   - **Website URL**.
   - **Additional contacts** and preferred language.
3. The acknowledgement commits you to two things:
   - Only send to people who asked for the email.
   - Have a process for bounces and complaints. For a small sender, the **account-level suppression list** (Configuration > Suppression list, reasons: bounces and complaints) plus Auto Validation covers it.
4. AWS may follow up with questions. A good use-case answer says: what triggers each email, the expected volume, that recipients enter their own address (no bought lists), how bots are blocked (CAPTCHA, validation) and how bounces are handled.
5. Approval can take minutes to a day. Afterwards you can send to any address, and the quota goes up.

## Protecting a Contact Form from Abuse

- **The risk**: if the form sends a confirmation to the address the visitor typed, a bot that passes the CAPTCHA can make you send that email to strangers. Even with fixed content, people who never wrote to you may mark it as spam.
- **Why it matters**: SES puts the account under review at a 5% bounce rate or a 0.1% complaint rate, and may pause sending at 10% or 0.5% (as of October 2026). A pause also stops the copy the form sends to you.
- **Rate limit the endpoint**: add a firewall rule in front of the form's API, for example 5 `POST` requests per IP every 10 minutes, answered with `429`. A real person never hits it. Keep it in the firewall, not in memory: serverless instances don't share memory.
- **Gate the confirmation on the CAPTCHA score**: reCAPTCHA v3 gives a score from 0.0 (bot) to 1.0 (human). Without a billing account Google only returns 0.1, 0.3, 0.7 or 0.9.
  - Accept the message at the usual threshold (0.5), so your copy still arrives.
  - Send the visitor's confirmation only at the top score (0.9).
  - Return the same success response either way, so a bot learns nothing.
- **Alarm on reputation before SES acts**:
  1. Create an **SNS** topic (Standard) in the same region as SES, add an **Email** subscription and confirm it from the inbox.
  2. Go to **SES > Reputation metrics > Account-level**, choose **View in CloudWatch** on **Bounce rate**, then the bell icon to create an alarm.
  3. Set **Maximum**, **1 hour**, **Greater/Equal** `0.025` (half the review level), **2 out of 2** datapoints, and **Treat missing data as ignore**. Notify the SNS topic **In alarm**.
  4. Repeat for **Complaint rate** with `0.0005` and **1 out of 1**. At low volume one complaint can cross the review level, so you want to hear about the first one.
  - The metrics are `AWS/SES` `Reputation.BounceRate` and `Reputation.ComplaintRate`, as fractions (`0.025` = 2.5%).
  - Two alarms fit in the CloudWatch free tier (10 alarm metrics), and the first 1,000 SNS emails a month are free.

## Gotchas

- **Email identity beats domain identity**: if you verify both `hello@example.com` and `example.com`, SES uses the most specific one. Settings like a custom MAIL FROM set on the domain are ignored for that address. Once the domain is verified, delete the email-address identity so there's only one place to configure.
- **The wizard's configuration set needs IAM permission**: the setup wizard can create a configuration set (`my-first-configuration-set`) that SES applies to every send. A least-privilege IAM user then gets `403 AccessDeniedException` until its policy also allows that configuration set. See [IAM credentials](iam-credentials.md#403-accessdeniedexception-on-a-configuration-set).
- **Don't let a form relay arbitrary text**: if your form sends a confirmation to the address the visitor typed, make that email fixed content. Echoing the visitor's message or name lets anyone use your domain to send their text to any address.
