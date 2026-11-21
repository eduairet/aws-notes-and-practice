"""Save one contact-form message to DynamoDB.

Input:  {"email": "ada@example.com", "message": "Hi there"}
Output: 201 with the new item's id, or 400 when a field is missing.
"""
import functools
import json
import os
import uuid
from datetime import datetime, timezone

import boto3

TTL_DAYS = 90


@functools.cache
def dynamodb():
    return boto3.client("dynamodb")


def build_item(email, message, now=None):
    """One item per message: a random UUID key, so two writes never collide."""
    now = now or datetime.now(timezone.utc)
    return {
        "id": {"S": str(uuid.uuid4())},
        "createdAt": {"S": now.isoformat(timespec="milliseconds").replace("+00:00", "Z")},
        # TTL needs a Number holding Unix epoch *seconds*. Any other type never expires.
        "expiresAt": {"N": str(int(now.timestamp()) + TTL_DAYS * 24 * 60 * 60)},
        "email": {"S": email},
        "message": {"S": message},
    }


def lambda_handler(event, context):
    email = (event.get("email") or "").strip()
    message = (event.get("message") or "").strip()
    if "@" not in email or not message:
        return {"statusCode": 400, "body": json.dumps({"error": "email and message are required"})}

    item = build_item(email, message)
    # ReturnValues is left at its default (NONE): the write never reads anything back.
    dynamodb().put_item(TableName=os.environ["TABLE_NAME"], Item=item)
    return {"statusCode": 201, "body": json.dumps({"id": item["id"]["S"]})}
