# Amazon DynamoDB

- Amazon DynamoDB is a serverless key-value database. You store items in tables and read or write them through an HTTPS API, with no server or connection pool to manage.
- In on-demand mode you pay per request and per GB stored, so a small table that is rarely written costs close to nothing.
- Typical uses:
  - A backup copy of contact form messages, deleted automatically after a set time.
  - Sessions, carts, settings and other data you look up by a key.
  - Apps that need the same fast reads and writes at any traffic level.
- When it's not a good fit: queries that join tables or filter on many fields. DynamoDB is fast when you know the key. Anything else means reading the whole table (a Scan).

## Content

- [Tables, keys, Time to Live and pricing](notes/amazon-dynamodb/basics.md)
- [Writing one item with temporary credentials from an OIDC role](notes/amazon-dynamodb/put-item-oidc-role.md)

## Reference

- [Amazon DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
- [DynamoDB on-demand pricing](https://aws.amazon.com/dynamodb/pricing/on-demand/)
- [PutItem API reference](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_PutItem.html)
- [Using Time to Live](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)
