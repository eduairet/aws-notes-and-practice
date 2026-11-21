import json

# Comes from the layer (/opt/python in Lambda), not from this function's package.
from greeting import greet


def lambda_handler(event, context):
    name = event.get("name", "world")
    count = int(event.get("count", 0))
    return {"statusCode": 200, "body": json.dumps({"message": greet(name, count)})}
