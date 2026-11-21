# AWS Notes and Practice

This repository contains notes and practice exercises related to AWS (Amazon Web Services). It serves as a personal reference for learning and mastering various AWS services and concepts.

## Overview

AWS (Amazon Web Services) is a comprehensive cloud computing platform that provides a wide range of services, including computing power, storage, databases, machine learning, and more its maon advantages is that you use it on-demand and you can scale it up or down based on your needs.

## Notes

- [AWS Lambda](notes/aws-lambda/README.md)
- [Amazon SES](notes/amazon-ses/README.md)
- [Amazon DynamoDB](notes/amazon-dynamodb/README.md)
- [AWS Emulator](notes/aws-emulator/README.md)

## Local Testing (no AWS costs)

Run the [AWS Emulator](notes/aws-emulator/notes/aws-emulator/docker-setup.md) in Docker so the AWS CLI and SDKs create resources locally instead of in a real account:

```powershell
docker compose up -d          # start the emulator on https://127.0.0.1:9297
. ./emulator/env.ps1          # point this shell at it (bash: source emulator/env.sh)
aws sts get-caller-identity   # account 000000000000 = emulator
```

Test every project under `practice/` against it (also runs in CI on each push):

```powershell
docker compose run --rm practice-tests
```

## Practice

- [AWS SAM CLI](practice/aws-lambda/README.md)
