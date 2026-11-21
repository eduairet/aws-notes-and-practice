"""Invoke the deployed function. Needs AWS_SAM_STACK_NAME (the stack to test)."""
import json
import os

import boto3
import pytest


@pytest.fixture(scope="module")
def outputs():
    stack_name = os.environ.get("AWS_SAM_STACK_NAME")
    if stack_name is None:
        raise ValueError("Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack")
    stack = boto3.client("cloudformation").describe_stacks(StackName=stack_name)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in stack["Outputs"]}


def test_function_has_the_layer(outputs):
    config = boto3.client("lambda").get_function_configuration(FunctionName=outputs["GreetingFunction"])

    assert [layer["Arn"] for layer in config["Layers"]] == [outputs["GreetingLayerArn"]]


def test_invoke_runs_layer_code(outputs):
    response = boto3.client("lambda").invoke(
        FunctionName=outputs["GreetingFunction"],
        Payload=json.dumps({"name": "Ada", "count": 1234}),
    )
    payload = json.loads(response["Payload"].read())

    assert "FunctionError" not in response, payload
    assert json.loads(payload["body"]) == {"message": "Hello, Ada! You have 1,234 new messages."}
