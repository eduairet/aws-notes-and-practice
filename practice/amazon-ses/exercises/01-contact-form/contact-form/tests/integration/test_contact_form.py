"""Integration tests against the deployed stack. Needs AWS_SAM_STACK_NAME."""
import json
import os
import time

import boto3
import pytest

lambda_client = boto3.client("lambda")
FORM = {"name": "Ada", "email": "ada@example.com", "message": "Hi there"}


@pytest.fixture(scope="module")
def outputs():
    stack_name = os.environ.get("AWS_SAM_STACK_NAME")
    if stack_name is None:
        raise ValueError("Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack")
    stack = boto3.client("cloudformation").describe_stacks(StackName=stack_name)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in stack["Outputs"]}


@pytest.fixture(scope="module", autouse=True)
def verified_sender(outputs):
    """Sends fail until SES has verified the domain (on AWS: once the DKIM records resolve)."""
    ses = boto3.client("sesv2")
    deadline = time.time() + 120
    while not ses.get_email_identity(EmailIdentity=outputs["SenderDomain"])["VerifiedForSendingStatus"]:
        if time.time() > deadline:
            pytest.fail(f"{outputs['SenderDomain']} is not verified in SES")
        time.sleep(2)


def invoke(function_name, event):
    response = lambda_client.invoke(FunctionName=function_name, Payload=json.dumps(event))
    payload = json.loads(response["Payload"].read())
    assert "FunctionError" not in response, payload
    return payload


def test_sends_and_saves_a_copy(outputs):
    ret = invoke(outputs["ContactFormFunction"], FORM)

    assert ret["statusCode"] == 200, ret
    body = json.loads(ret["body"])
    assert body["messageId"]
    copy = boto3.client("dynamodb").get_item(TableName=outputs["MessageCopiesTable"], Key={"id": {"S": body["copyId"]}})["Item"]
    assert copy["message"] == {"S": "Hi there"}
