import json
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError

from contact_form import app

FORM = {"name": "Ada", "email": "ada@example.com", "message": "Hi there"}


def client_error(code, status=400):
    return ClientError({"Error": {"Code": code, "Message": "..."}, "ResponseMetadata": {"HTTPStatusCode": status}}, "op")


@pytest.fixture
def ses(monkeypatch):
    client = Mock()
    client.send_email.return_value = {"MessageId": "msg-1"}
    monkeypatch.setattr(app, "ses", lambda: client)
    monkeypatch.setenv("FROM_ADDRESS", "hello@example.com")
    monkeypatch.setenv("CONTACT_EMAIL", "owner@example.com")
    return client


@pytest.fixture
def dynamodb(monkeypatch):
    client = Mock()
    monkeypatch.setattr(app, "dynamodb", lambda: client)
    monkeypatch.setenv("TABLE_NAME", "copies")
    return client


def test_copy_item_expires_in_90_days():
    now = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
    item = app.build_item("Ada", "ada@example.com", "Hi there", now=now)

    assert item["createdAt"] == {"S": "2026-10-13T12:00:00.000Z"}
    assert item["expiresAt"] == {"N": str(int(now.timestamp()) + 90 * 24 * 60 * 60)}


def test_sends_then_saves_a_copy(ses, dynamodb):
    ret = app.lambda_handler(FORM, None)

    assert ret["statusCode"] == 200
    body = json.loads(ret["body"])
    assert body["messageId"] == "msg-1" and body["copyId"]
    send = ses.send_email.call_args.kwargs
    assert send["FromEmailAddress"] == "hello@example.com"
    assert send["Destination"] == {"ToAddresses": ["owner@example.com"]}
    assert send["ReplyToAddresses"] == ["ada@example.com"]
    assert dynamodb.put_item.call_args.kwargs["Item"]["email"] == {"S": "ada@example.com"}


@pytest.mark.parametrize("code", ["ResourceNotFoundException", "AccessDeniedException"])
def test_a_failed_copy_never_breaks_the_send(ses, dynamodb, capsys, code):
    dynamodb.put_item.side_effect = client_error(code)

    ret = app.lambda_handler(FORM, None)

    assert ret["statusCode"] == 200
    assert json.loads(ret["body"])["copyId"] is None
    log = capsys.readouterr().out
    assert log == f"backup copy not saved: {code}\n"
    assert "ada@example.com" not in log


def test_a_refused_send_is_a_502_and_saves_nothing(ses, dynamodb, capsys):
    ses.send_email.side_effect = client_error("AccessDeniedException", 403)

    ret = app.lambda_handler(FORM, None)

    assert ret["statusCode"] == 502
    dynamodb.put_item.assert_not_called()
    assert capsys.readouterr().out == "send failed: 403 AccessDeniedException\n"


@pytest.mark.parametrize("missing", ["name", "email", "message"])
def test_incomplete_forms_are_rejected(ses, dynamodb, missing):
    assert app.lambda_handler({**FORM, missing: ""}, None)["statusCode"] == 400
    ses.send_email.assert_not_called()
