"""Validate an order and compute its total.

Input:  {"orderId": "o-1", "items": [{"sku": "book", "quantity": 2, "price": 12.5}]}
Output: {"orderId": "o-1", "total": 25.0}
"""


class InvalidOrderError(Exception):
    """A business error: retrying won't help, so the state machine catches it."""


def lambda_handler(event, context):
    order_id = event.get("orderId")
    items = event.get("items") or []
    if not order_id:
        raise InvalidOrderError("orderId is required")
    if not items:
        raise InvalidOrderError(f"order {order_id} has no items")

    total = 0.0
    for item in items:
        quantity, price = item.get("quantity", 0), item.get("price", 0)
        if quantity <= 0 or price < 0:
            raise InvalidOrderError(f"order {order_id} has an invalid item: {item.get('sku')}")
        total += quantity * price

    return {"orderId": order_id, "total": round(total, 2)}
