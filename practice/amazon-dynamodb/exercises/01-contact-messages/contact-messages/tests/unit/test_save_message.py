import json
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from save_message import app

NOW = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)


def test_item_types_and_ttl():
    item = app.build_item("ada@example.com", "Hi there", now=NOW)

    uuid.UUID(item["id"]["S"])  # a valid UUID
    assert item["createdAt"] == {"S": "2026-10-13T12:00:00.000Z"}
    assert item["expiresAt"] == {"N": str(int(NOW.timestamp()) + 90 * 24 * 60 * 60)}  # seconds, as a Number
    assert item["email"] == {"S": "ada@example.com"}
    assert item["message"] == {"S": "Hi there"}


@pytest.fixture
def dynamodb(monkeypatch):
    client = Mock()
    monkeypatch.setattr(app, "dynamodb", lambda: client)
    monkeypatch.setenv("TABLE_NAME", "contact-messages")
    return client


def test_handler_writes_one_item(dynamodb):
    ret = app.lambda_handler({"email": "ada@example.com", "message": "Hi there"}, None)

    assert ret["statusCode"] == 201
    call = dynamodb.put_item.call_args.kwargs
    assert call["TableName"] == "contact-messages"
    assert call["Item"]["id"]["S"] == json.loads(ret["body"])["id"]
    assert "ReturnValues" not in call  # write-only: never ask for the old item


@pytest.mark.parametrize("event", [{}, {"email": "not-an-email", "message": "hi"}, {"email": "ada@example.com", "message": "  "}])
def test_handler_rejects_incomplete_messages(dynamodb, event):
    assert app.lambda_handler(event, None)["statusCode"] == 400
    dynamodb.put_item.assert_not_called()
