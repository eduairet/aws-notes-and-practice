"""Integration tests against the deployed stack. Needs AWS_SAM_STACK_NAME."""
import json
import os
import time

import boto3
import pytest
from botocore.exceptions import ClientError

dynamodb = boto3.client("dynamodb")


@pytest.fixture(scope="module")
def outputs():
    stack_name = os.environ.get("AWS_SAM_STACK_NAME")
    if stack_name is None:
        raise ValueError("Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack")
    stack = boto3.client("cloudformation").describe_stacks(StackName=stack_name)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in stack["Outputs"]}


def invoke(function_name, event):
    response = boto3.client("lambda").invoke(FunctionName=function_name, Payload=json.dumps(event))
    payload = json.loads(response["Payload"].read())
    assert "FunctionError" not in response, payload
    return payload


def test_function_saves_the_message(outputs):
    ret = invoke(outputs["SaveMessageFunction"], {"email": "ada@example.com", "message": "Hi there"})
    assert ret["statusCode"] == 201

    key = {"id": {"S": json.loads(ret["body"])["id"]}}
    item = dynamodb.get_item(TableName=outputs["ContactMessagesTable"], Key=key)["Item"]
    assert item["email"] == {"S": "ada@example.com"}
    assert item["message"] == {"S": "Hi there"}
    expires_in_days = (int(item["expiresAt"]["N"]) - time.time()) / 86400
    assert 89.9 < expires_in_days <= 90


def test_ttl_is_on_expires_at(outputs):
    ttl = dynamodb.describe_time_to_live(TableName=outputs["ContactMessagesTable"])["TimeToLiveDescription"]

    assert ttl["AttributeName"] == "expiresAt"
    assert ttl["TimeToLiveStatus"] in ("ENABLING", "ENABLED")


def test_writing_an_existing_key_replaces_the_item(outputs):
    table = outputs["ContactMessagesTable"]
    dynamodb.put_item(TableName=table, Item={"id": {"S": "same-key"}, "message": {"S": "first"}, "extra": {"S": "x"}})
    dynamodb.put_item(TableName=table, Item={"id": {"S": "same-key"}, "message": {"S": "second"}})

    item = dynamodb.get_item(TableName=table, Key={"id": {"S": "same-key"}})["Item"]
    assert item == {"id": {"S": "same-key"}, "message": {"S": "second"}}  # replaced, not merged


@pytest.fixture(scope="module")
def writer_credentials(outputs):
    """Temporary credentials from the write-only role (the notes get these through OIDC)."""
    return boto3.client("sts").assume_role(
        RoleArn=outputs["ContactWriterRoleArn"], RoleSessionName="website-contact", DurationSeconds=900
    )["Credentials"]


def writer_client(credentials, with_session_token=True):
    return boto3.client(
        "dynamodb",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"] if with_session_token else None,
    )


def error_code(call):
    with pytest.raises(ClientError) as excinfo:
        call()
    return excinfo.value.response["Error"]["Code"]


def test_writer_role_can_put(outputs, writer_credentials):
    item = {"id": {"S": "from-writer"}, "message": {"S": "hi"}}
    writer_client(writer_credentials).put_item(TableName=outputs["ContactMessagesTable"], Item=item)


def test_writer_role_cannot_read(outputs, writer_credentials):
    client = writer_client(writer_credentials)
    get = lambda: client.get_item(TableName=outputs["ContactMessagesTable"], Key={"id": {"S": "from-writer"}})

    assert error_code(get) == "AccessDeniedException"


@pytest.mark.real_aws_only  # the emulator mis-evaluates the ReturnValues condition, so its run turns it off
def test_writer_role_cannot_read_back_the_replaced_item(outputs, writer_credentials):
    client = writer_client(writer_credentials)
    item = {"id": {"S": "from-writer"}, "message": {"S": "again"}}
    put = lambda: client.put_item(TableName=outputs["ContactMessagesTable"], Item=item, ReturnValues="ALL_OLD")

    assert error_code(put) == "AccessDeniedException"


def test_temporary_credentials_need_the_session_token(outputs, writer_credentials):
    client = writer_client(writer_credentials, with_session_token=False)
    put = lambda: client.put_item(TableName=outputs["ContactMessagesTable"], Item={"id": {"S": "x"}})

    assert error_code(put) in ("InvalidClientTokenId", "UnrecognizedClientException")


def test_deletion_protection_blocks_delete(outputs):
    table = outputs["ContactMessagesTable"]
    assert dynamodb.describe_table(TableName=table)["Table"]["DeletionProtectionEnabled"] is True

    assert error_code(lambda: dynamodb.delete_table(TableName=table)) in ("ValidationException", "ResourceInUseException")
