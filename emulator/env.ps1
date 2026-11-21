# Point the current PowerShell session at the local AWS Emulator.
# Usage (dot-source it so the variables stay in your shell):
#   . ./emulator/env.ps1
# Works in PowerShell 7+ on Windows, macOS and Linux.
# Open a new terminal to go back to your real AWS credentials.
param([int]$Port = ($env:EMULATOR_PORT ?? 9297))

# $HOME is set by PowerShell on every OS; one segment per argument keeps separators native.
$dir = Join-Path $HOME '.aws' 'emulator' "$Port"
if (-not (Test-Path (Join-Path $dir 'config'))) {
    Write-Warning "No emulator files in $dir. Start it first: docker compose up -d"
    return
}

# Real credentials/profiles take precedence and make the emulator reject requests.
Remove-Item Env:AWS_ACCESS_KEY_ID, Env:AWS_SECRET_ACCESS_KEY, Env:AWS_SESSION_TOKEN, Env:AWS_PROFILE -ErrorAction SilentlyContinue

$env:AWS_ENDPOINT_URL = "https://127.0.0.1:$Port"   # 127.0.0.1, not localhost (S3 needs it)
$env:AWS_SHARED_CREDENTIALS_FILE = Join-Path $dir 'emulator_credentials'
$env:AWS_CONFIG_FILE = Join-Path $dir 'config'
$env:AWS_CA_BUNDLE = Join-Path $dir 'ca.pem'          # CLI v2, boto3, Go v2
$env:NODE_EXTRA_CA_CERTS = $env:AWS_CA_BUNDLE          # JavaScript SDK v3
# For Rust/.NET SDKs also set: $env:SSL_CERT_FILE = $env:AWS_CA_BUNDLE (replaces the default trust store)
$env:AWS_EC2_METADATA_DISABLED = 'true'
$env:AWS_DISABLE_HOST_PREFIX_INJECTION = 'true'
$env:AWS_REGION = 'us-east-1'
$env:AWS_DEFAULT_REGION = 'us-east-1'

Write-Host "AWS CLI/SDKs now target the emulator at $env:AWS_ENDPOINT_URL (account 000000000000)."
