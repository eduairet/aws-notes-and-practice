import json
from pathlib import Path

import pytest
import yaml

from validate_order import app


class CloudFormationLoader(yaml.SafeLoader):
    """SafeLoader that reads CloudFormation tags: !Sub "text" gives the text, other tags give None."""


CloudFormationLoader.add_multi_constructor(
    "!", lambda loader, tag, node: loader.construct_scalar(node) if isinstance(node, yaml.ScalarNode) else None
)

TEMPLATE = yaml.load((Path(__file__).resolve().parents[2] / "template.yaml").read_text(), Loader=CloudFormationLoader)
DEFINITION = json.loads(TEMPLATE["Resources"]["OrderStateMachine"]["Properties"]["DefinitionString"])


def test_total_is_quantity_times_price():
    order = {"orderId": "o-1", "items": [{"sku": "a", "quantity": 2, "price": 12.5}, {"sku": "b", "quantity": 1, "price": 5}]}

    assert app.lambda_handler(order, None) == {"orderId": "o-1", "total": 30.0}


@pytest.mark.parametrize(
    "order",
    [
        {"items": [{"sku": "a", "quantity": 1, "price": 1}]},
        {"orderId": "o-1", "items": []},
        {"orderId": "o-1", "items": [{"sku": "a", "quantity": 0, "price": 1}]},
        {"orderId": "o-1", "items": [{"sku": "a", "quantity": 1, "price": -1}]},
    ],
)
def test_invalid_orders_raise(order):
    with pytest.raises(app.InvalidOrderError):
        app.lambda_handler(order, None)


def test_every_transition_target_exists():
    states = DEFINITION["States"]
    targets = {DEFINITION["StartAt"]}
    for state in states.values():
        targets.update(filter(None, [state.get("Next"), state.get("Default")]))
        targets.update(choice["Next"] for choice in state.get("Choices", []))
        targets.update(catch["Next"] for catch in state.get("Catch", []))

    assert targets <= states.keys()


def test_business_errors_are_not_retried():
    retried = {error for rule in DEFINITION["States"]["ValidateOrder"]["Retry"] for error in rule["ErrorEquals"]}

    assert "InvalidOrderError" not in retried
    assert "States.ALL" not in retried
