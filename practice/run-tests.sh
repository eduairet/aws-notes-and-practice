#!/usr/bin/env bash
# Builds, deploys and tests every SAM project under practice/ against the AWS Emulator.
#
#   docker compose run --rm practice-tests    # no local tools needed
#
# For each project (a folder with template.yaml) it runs, when present:
#   1. tests/unit          (pytest, no AWS calls)
#   2. sam build + sam deploy to the emulator
#   3. tests/integration   (pytest, with AWS_SAM_STACK_NAME set to the deployed stack;
#                           pytest_emulator.py routes API Gateway URLs to the emulator)
set -uo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$repo/emulator/env.sh" || exit 1

test_project() {
  local project="$1" stack="$2"
  # Work on a copy so builds never land in the repo (mounted read-only in Docker).
  cd "$(mktemp -d)"
  cp -r "$project/." .

  if [ -f tests/requirements.txt ]; then pip install -q -r tests/requirements.txt; fi
  if [ -d tests/unit ]; then python -m pytest -q tests/unit; fi

  # --profile default: the emulator's generated config only has [default],
  # whatever profile samconfig.toml names for real deployments.
  sam build --profile default
  # A project can tune its emulator deploy (for example, parameter_overrides that
  # switch off a policy condition the emulator mis-evaluates) in samconfig.toml
  # under [emulator.deploy.parameters]. Real deploys keep using [default.*].
  local config_env=()
  if grep -q '^\[emulator\.deploy\.parameters\]' samconfig.toml 2>/dev/null; then
    config_env=(--config-env emulator)
  fi
  sam deploy "${config_env[@]}" --profile default --stack-name "$stack" --resolve-s3 \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    --no-confirm-changeset --no-fail-on-empty-changeset

  if [ -d tests/integration ]; then
    AWS_SAM_STACK_NAME="$stack" PYTHONPATH="$repo/practice" \
      python -m pytest -q -p pytest_emulator tests/integration
  fi
}

failed=()
while IFS= read -r template; do
  project="$(dirname "$template")"
  rel="${project#"$repo/practice/"}"
  stack="practice-$(printf '%s' "$rel" | tr -c 'A-Za-z0-9-' '-')"
  echo "=== $rel (stack $stack) ==="
  # Subshell outside any condition, so `set -e` stops at the first failing step.
  (set -e; test_project "$project" "$stack")
  if [ $? -eq 0 ]; then
    echo "=== PASSED: $rel ==="
  else
    echo "=== FAILED: $rel ==="
    failed+=("$rel")
  fi
done < <(find "$repo/practice" -name template.yaml -not -path '*/.aws-sam/*' | sort)

if [ ${#failed[@]} -gt 0 ]; then
  printf 'Failed projects:\n'; printf '  %s\n' "${failed[@]}"
  exit 1
fi
echo "All practice projects passed."
