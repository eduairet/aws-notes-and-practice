# AWS Emulator

- The [AWS Emulator](https://docs.aws.amazon.com/emulator/latest/userguide/getting-started.html) is a local server that answers AWS API calls. The CLI and SDKs talk to it instead of real AWS, so you can practice and test without an AWS account and without paying for resources.
- It runs as a single process that serves HTTPS on `https://127.0.0.1:9297`, with a self-signed certificate. On Windows and macOS it runs in Docker.
- Compared to [`sam local invoke`](../aws-lambda/notes/aws-lambda/aws-sam-cli.md): SAM runs only your function. The emulator also runs the AWS APIs around it, such as S3, DynamoDB and SES, so you can test the whole flow.
- Everything lives in one fake account (`000000000000`) and one Region (`us-east-1` here). Resources only exist in memory. Stopping the emulator deletes all of them.
- What it's good for: the control plane (create, list, describe, delete) and a lot of the data plane. In this repo it has run S3, DynamoDB, IAM, STS, SES v2, Step Functions, and Lambda, including invoking a real Python handler.
- What it's not for:
  - Production use.
  - Security testing: IAM and resource policies aren't evaluated the way AWS evaluates them.
  - Load testing.
  - Fidelity varies by service. Unimplemented operations return HTTP 501 `NotImplemented`. Per-service fidelity scores are on the [releases page](https://github.com/aws/aws-emulator/releases).

## Content

- [Docker Setup](notes/aws-emulator/docker-setup.md)

## Reference

- [AWS Emulator User Guide](https://docs.aws.amazon.com/emulator/latest/userguide/getting-started.html)
- [Running in Docker](https://docs.aws.amazon.com/emulator/latest/userguide/getting-started-docker.html)
- [Pointing an SDK at the emulator](https://docs.aws.amazon.com/emulator/latest/userguide/point-sdk-to-emulator.html)
- [CLI reference](https://docs.aws.amazon.com/emulator/latest/userguide/cli-reference.html)
- [Source code (GitHub)](https://github.com/aws/aws-emulator)
