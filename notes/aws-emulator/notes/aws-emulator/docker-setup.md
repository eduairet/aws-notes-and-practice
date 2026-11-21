# Running the AWS Emulator with Docker

This repo runs the emulator with Docker Compose. The files involved:

- [`compose.yaml`](../../../../compose.yaml): the service. It listens on `127.0.0.1:9297` with a 2 GB memory cap, telemetry off, and a health check.
- [`emulator/Dockerfile`](../../../../emulator/Dockerfile): AWS publishes no prebuilt image, so this downloads the LTS RPM at build time. It picks the x86_64 or Arm build to match your machine.
- [`emulator/env.ps1`](../../../../emulator/env.ps1) and [`emulator/env.sh`](../../../../emulator/env.sh): point the current shell's AWS CLI and SDKs at the emulator.

## Start It

From the repo root:

```powershell
docker compose up -d   # builds the image the first time (~1 min)
docker compose ps      # wait for STATUS "healthy"
```

To update to the newest emulator release, run `docker compose up -d --build`.

When it starts, the emulator writes four files to `~/.aws/emulator/9297/` on the host, through the bind mount:

- `emulator_credentials`: a new random key pair on every start.
- `config`: Region and endpoint.
- `ca.pem`: the self-signed CA. It's regenerated on every start.
- `truststore.p12`: for Java.

## Point Your Shell at It

```powershell
. ./emulator/env.ps1      # PowerShell (note the leading dot)
```

```bash
source emulator/env.sh    # bash / zsh / Git Bash
```

The scripts set the variables from [the official guide](https://docs.aws.amazon.com/emulator/latest/userguide/point-sdk-to-emulator.html). Each line in them has a comment. Three things are worth knowing:

- They unset your real credentials (`AWS_ACCESS_KEY_ID`, `AWS_PROFILE`, ...). Real credentials take precedence over the emulator's, and the emulator rejects them.
- The endpoint is `https://127.0.0.1:9297`, not `localhost`. S3 requires the IP address.
- `AWS_DISABLE_HOST_PREFIX_INJECTION=true` is needed for calls like Step Functions `StartSyncExecution`.

The variables only last for that terminal. Open a new terminal to go back to real AWS.

> The generated `config` contains `ca_bundle = /home/emulator/...`, which is a path inside the container. That's fine: `AWS_CA_BUNDLE` overrides it. Don't use the generated config without the script.

Check it:

```powershell
aws sts get-caller-identity
# Account 000000000000, Arn arn:aws:iam::000000000000:user/emulator
```

## Examples

```powershell
aws s3api create-bucket --bucket demo-bucket
aws dynamodb create-table --table-name demo `
  --attribute-definitions AttributeName=pk,AttributeType=S `
  --key-schema AttributeName=pk,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name demo   # tables start in CREATING, like real AWS
aws sesv2 create-email-identity --email-identity test@example.com
```

Lambda runs your code for real. This example deploys the handler from the [hello world exercise](../../../../practice/aws-lambda/exercises/01-hello-world-lambda/README.md):

```powershell
Compress-Archive -Force practice/aws-lambda/exercises/01-hello-world-lambda/hello-world/hello_world/app.py fn.zip
'{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' | Set-Content trust.json
aws iam create-role --role-name lambda-role --assume-role-policy-document file://trust.json
aws lambda create-function --function-name hello --runtime python3.13 `
  --handler app.lambda_handler --role arn:aws:iam::000000000000:role/lambda-role `
  --zip-file fileb://fn.zip
aws lambda wait function-active-v2 --function-name hello
aws lambda invoke --function-name hello out.json; Get-Content out.json
```

## Stop, Reset and Clean Up

```powershell
docker compose restart      # fresh, empty state (and new credentials/CA: re-run env script)
docker compose down         # stop and remove the container
docker image rm aws-emulator
```

There is no reset API. A restart is the only way to clear state. To stop automatically when idle, add `--idle-timeout <seconds>` to `command` in `compose.yaml`.

## Troubleshooting

- **`SSL validation failed ... unable to get local issuer certificate`**:
  - First, re-run the env script after every emulator restart, because the CA changes each time.
  - If it still fails, check who signed the certificate you receive:

    ```bash
    echo | openssl s_client -connect 127.0.0.1:9297 2>/dev/null | openssl x509 -noout -issuer
    ```

  - If the issuer is your antivirus (for example `Norton Web/Mail Shield Self-signed Root`), its HTTPS scanning is intercepting localhost traffic. Exclude `127.0.0.1` or port `9297` from encrypted-connection scanning, or turn that scanning off.
  - Don't add the antivirus's "self-signed root" to a trust store. It exists so that untrusted sites stay untrusted.
- **Requests rejected with `AccessDenied` / `InvalidClientTokenId`**: real credentials are still set in the shell, or the emulator restarted and you didn't re-run the env script.
- **Container exits with code 137**: it ran out of memory. Raise `mem_limit` / `memswap_limit`.
- **Linux host, permission denied on `~/.aws/emulator`**: the container runs as UID 1000. Add `user: "<your uid>:<your gid>"` to the service.
- **Port already in use**: start on another port with `$env:EMULATOR_PORT = 9300; docker compose up -d` (bash: `EMULATOR_PORT=9300 docker compose up -d`). Then run the env script with that port: `. ./emulator/env.ps1 -Port 9300` or `source emulator/env.sh 9300`.
