# Point the current bash/zsh session at the local AWS Emulator.
# Usage (source it so the variables stay in your shell):
#   source emulator/env.sh
# Open a new terminal to go back to your real AWS credentials.
EMULATOR_PORT="${1:-9297}"
EMULATOR_DIR="$HOME/.aws/emulator/$EMULATOR_PORT"
# Git Bash on Windows: hand the Windows AWS CLI a Windows-style path.
if command -v cygpath >/dev/null 2>&1; then EMULATOR_DIR="$(cygpath -m "$EMULATOR_DIR")"; fi

if [ ! -f "$EMULATOR_DIR/config" ]; then
  echo "No emulator files in $EMULATOR_DIR. Start it first: docker compose up -d" >&2
  return 1 2>/dev/null || exit 1
fi

# Real credentials/profiles take precedence and make the emulator reject requests.
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_PROFILE

export AWS_ENDPOINT_URL="https://127.0.0.1:$EMULATOR_PORT"   # 127.0.0.1, not localhost (S3 needs it)
export AWS_SHARED_CREDENTIALS_FILE="$EMULATOR_DIR/emulator_credentials"
export AWS_CONFIG_FILE="$EMULATOR_DIR/config"
export AWS_CA_BUNDLE="$EMULATOR_DIR/ca.pem"          # CLI v2, boto3, Go v2
export NODE_EXTRA_CA_CERTS="$AWS_CA_BUNDLE"           # JavaScript SDK v3
# For Rust/.NET SDKs also set: export SSL_CERT_FILE="$AWS_CA_BUNDLE" (replaces the default trust store)
export AWS_EC2_METADATA_DISABLED=true
export AWS_DISABLE_HOST_PREFIX_INJECTION=true
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1

echo "AWS CLI/SDKs now target the emulator at $AWS_ENDPOINT_URL (account 000000000000)."
