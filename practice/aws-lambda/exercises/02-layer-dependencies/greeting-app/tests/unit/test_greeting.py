import json

from greeting import greet
from greeting_function import app


def test_greet_formats_the_count():
    assert greet("Ada", 1234) == "Hello, Ada! You have 1,234 new messages."


def test_greet_singular():
    assert greet("Ada", 1) == "Hello, Ada! You have 1 new message."


def test_handler_uses_the_layer():
    ret = app.lambda_handler({"name": "Ada", "count": 1234}, None)

    assert ret["statusCode"] == 200
    assert json.loads(ret["body"]) == {"message": "Hello, Ada! You have 1,234 new messages."}


def test_handler_defaults():
    body = json.loads(app.lambda_handler({}, None)["body"])

    assert body["message"] == "Hello, world! You have 0 new messages."
