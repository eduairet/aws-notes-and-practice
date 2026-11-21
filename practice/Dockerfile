# Test runner image for practice/run-tests.sh (the `practice-tests` compose service).
# Test dependencies come from each project's tests/requirements.txt.
FROM python:3.13-slim
ENV SAM_CLI_TELEMETRY=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore
RUN pip install --no-cache-dir aws-sam-cli==1.174.0 pytest
WORKDIR /repo
