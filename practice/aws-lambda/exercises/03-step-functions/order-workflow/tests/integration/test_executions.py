"""Run real executions of the deployed state machine. Needs AWS_SAM_STACK_NAME."""
import json
import os
import time

import boto3
import pytest

sfn = boto3.client("stepfunctions")


@pytest.fixture(scope="module")
def outputs():
    stack_name = os.environ.get("AWS_SAM_STACK_NAME")
    if stack_name is None:
        raise ValueError("Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack")
    stack = boto3.client("cloudformation").describe_stacks(StackName=stack_name)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in stack["Outputs"]}


@pytest.fixture(scope="module")
def state_machine_arn(outputs):
    return outputs["OrderStateMachine"]


def run(state_machine_arn, order, timeout=60):
    """Start an execution and wait until it stops running."""
    arn = sfn.start_execution(stateMachineArn=state_machine_arn, input=json.dumps(order))["executionArn"]
    deadline = time.time() + timeout
    while True:
        execution = sfn.describe_execution(executionArn=arn)
        if execution["status"] != "RUNNING" or time.time() > deadline:
            return execution
        time.sleep(0.5)


def test_small_order_is_auto_approved(state_machine_arn):
    order = {"orderId": "o-small", "items": [{"sku": "book", "quantity": 2, "price": 12.5}]}
    execution = run(state_machine_arn, order)

    assert execution["status"] == "SUCCEEDED"
    assert json.loads(execution["output"]) == {"orderId": "o-small", "total": 25.0, "decision": "approved"}


def test_big_order_needs_review(state_machine_arn):
    order = {"orderId": "o-big", "items": [{"sku": "laptop", "quantity": 1, "price": 999}]}
    execution = run(state_machine_arn, order)

    assert execution["status"] == "SUCCEEDED"
    assert json.loads(execution["output"])["decision"] == "manual-review"


def test_invalid_order_is_caught_without_retries(state_machine_arn):
    execution = run(state_machine_arn, {"orderId": "o-empty", "items": []})

    assert execution["status"] == "FAILED"
    assert execution["error"] == "TaskFailed"

    events = sfn.get_execution_history(executionArn=execution["executionArn"])["events"]
    lambda_failures = [e["lambdaFunctionFailedEventDetails"] for e in events if e["type"] == "LambdaFunctionFailed"]
    assert [f["error"] for f in lambda_failures] == ["InvalidOrderError"]  # one attempt, no retries
    assert any(e["type"] == "FailStateEntered" and e["stateEnteredEventDetails"]["name"] == "ErrorHandler" for e in events)
