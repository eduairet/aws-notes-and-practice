# Amazon SES

- Amazon SES (Simple Email Service) is a cloud email service for sending transactional and marketing email from your own domain, without running a mail server.
- You call it from code through the SES API (v2) or SMTP, and you pay per email sent.
- Typical uses:
  - Contact form notifications and confirmations.
  - Password resets, receipts and other transactional email.
  - Newsletters and marketing campaigns (with stricter rules about consent and unsubscribes).
- Why use it instead of sending through a personal mailbox (for example Gmail SMTP with an app password):
  - The credential can only send email. A leaked mailbox password can also read your inbox.
  - Mail is signed for your own domain (DKIM), so it lands in the inbox more often.
  - Bounces and complaints are tracked and suppressed automatically.

## Content

- [Setting up SES for a domain](notes/amazon-ses/setup.md)
  - [Protecting a contact form from abuse](notes/amazon-ses/setup.md#protecting-a-contact-form-from-abuse)
- [Least-privilege IAM credentials for sending](notes/amazon-ses/iam-credentials.md)
- [Email authentication: SPF, DKIM, DMARC and MAIL FROM](notes/amazon-ses/email-authentication.md)

## Reference

- [Amazon SES Developer Guide](https://docs.aws.amazon.com/ses/latest/dg/Welcome.html)
- [Amazon SES Pricing](https://aws.amazon.com/ses/pricing/)
- [SES API v2 SendEmail](https://docs.aws.amazon.com/ses/latest/APIReference-V2/API_SendEmail.html)
