"""Contact-form backend: email the message, then save a backup copy.

Input:  {"name": "Ada", "email": "ada@example.com", "message": "Hi there"}
Output: 200 with the SES message ID and the copy's ID, 400 for a bad form,
        502 if SES refuses the send.
"""
import functools
import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

TTL_DAYS = 90


@functools.cache
def ses():
    return boto3.client("sesv2")


@functools.cache
def dynamodb():
    return boto3.client("dynamodb")


def response(status, body):
    return {"statusCode": status, "body": json.dumps(body)}


def send_email(name, email, message):
    """Send to the site owner. Reply-To is the visitor, so replying just works."""
    result = ses().send_email(
        FromEmailAddress=os.environ["FROM_ADDRESS"],
        Destination={"ToAddresses": [os.environ["CONTACT_EMAIL"]]},
        ReplyToAddresses=[email],
        Content={
            "Simple": {
                "Subject": {"Data": f"Contact form: {name}"},
                "Body": {"Text": {"Data": f"From: {name} <{email}>\n\n{message}"}},
            }
        },
    )
    return result["MessageId"]


def build_item(name, email, message, now=None):
    """The copy: random UUID key, and expiresAt as a Number in epoch seconds (for TTL)."""
    now = now or datetime.now(timezone.utc)
    return {
        "id": {"S": str(uuid.uuid4())},
        "createdAt": {"S": now.isoformat(timespec="milliseconds").replace("+00:00", "Z")},
        "expiresAt": {"N": str(int(now.timestamp()) + TTL_DAYS * 24 * 60 * 60)},
        "name": {"S": name},
        "email": {"S": email},
        "message": {"S": message},
    }


def save_copy(name, email, message):
    """Best effort: a missing table or a refused permission never changes the response."""
    item = build_item(name, email, message)
    try:
        dynamodb().put_item(TableName=os.environ["TABLE_NAME"], Item=item)
        return item["id"]["S"]
    except Exception as error:  # noqa: BLE001 - the copy must never break the send
        code = getattr(error, "response", {}).get("Error", {}).get("Code", type(error).__name__)
        print(f"backup copy not saved: {code}")  # one line, no form data
        return None


def lambda_handler(event, context):
    name = (event.get("name") or "").strip()
    email = (event.get("email") or "").strip()
    message = (event.get("message") or "").strip()
    if not name or "@" not in email or not message:
        return response(400, {"error": "name, email and message are required"})

    try:
        message_id = send_email(name, email, message)
    except ClientError as error:
        # Log the status and error type only: SES messages can include addresses.
        print(f"send failed: {error.response['ResponseMetadata']['HTTPStatusCode']} {error.response['Error']['Code']}")
        return response(502, {"error": "the message could not be sent"})

    return response(200, {"messageId": message_id, "copyId": save_copy(name, email, message)})
