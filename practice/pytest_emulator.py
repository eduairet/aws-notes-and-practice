"""pytest plugin: send API Gateway calls in tests to the AWS Emulator.

Loaded by run-tests.sh (`-p pytest_emulator`) so tests can keep calling the
`https://<id>.execute-api.<region>.amazonaws.com/...` URLs from stack outputs.
With AWS_ENDPOINT_URL set, every `requests` call to such a URL goes to the
emulator instead, with the original hostname in the Host header, which is how
the emulator routes API Gateway requests. Without it, nothing changes.
"""
import os
from urllib.parse import urlsplit


def pytest_configure(config):
    endpoint = os.environ.get("AWS_ENDPOINT_URL")
    if not endpoint:
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
            url = endpoint + parts.path + (f"?{parts.query}" if parts.query else "")
        return original(self, method, url, **kwargs)

    requests.Session.request = request
