"""pytest plugin for running integration tests against the AWS Emulator.

Loaded by run-tests.sh (`-p pytest_emulator`). With AWS_ENDPOINT_URL set:

- Every `requests` call to an `https://<id>.execute-api.<region>.amazonaws.com/...`
  URL (from stack outputs) goes to the emulator instead, with the original
  hostname in the Host header, which is how the emulator routes API Gateway.
- Tests marked `@pytest.mark.real_aws_only` are skipped: they check behaviour
  the emulator doesn't reproduce (see notes/aws-emulator). Against real AWS,
  without this plugin, they run like any other test.
"""
import os
from urllib.parse import urlsplit

import pytest

ENDPOINT = os.environ.get("AWS_ENDPOINT_URL")


def pytest_configure(config):
    config.addinivalue_line("markers", "real_aws_only: behaviour the AWS Emulator doesn't reproduce")
    if not ENDPOINT:
        return
    try:
        import requests
    except ImportError:
        return

    original = requests.Session.request

    def request(self, method, url, **kwargs):
        parts = urlsplit(url)
        if ".execute-api." in parts.netloc:
            kwargs["headers"] = {**(kwargs.get("headers") or {}), "Host": parts.netloc}
            kwargs.setdefault("verify", os.environ.get("AWS_CA_BUNDLE", True))
            url = ENDPOINT + parts.path + (f"?{parts.query}" if parts.query else "")
        return original(self, method, url, **kwargs)

    requests.Session.request = request


def pytest_collection_modifyitems(config, items):
    if not ENDPOINT:
        return
    skip = pytest.mark.skip(reason="the AWS Emulator doesn't reproduce this; runs against real AWS")
    for item in items:
        if "real_aws_only" in item.keywords:
            item.add_marker(skip)
