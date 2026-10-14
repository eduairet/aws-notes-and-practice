# Tables, Keys, Time to Live and Pricing

## Tables and Items

- A **table** holds **items**. An item is a set of attributes, each with a name and a typed value. Think of a row whose columns can differ from item to item.
- Only the primary key is fixed when you create the table. Every other attribute is free-form.
- In the API, every value carries its type:

  ```json
  { "name": { "S": "Jane Doe" }, "visits": { "N": "3" }, "active": { "BOOL": true } }
  ```

  - Numbers are sent as strings (`"N": "3"`), so no precision is lost between languages.

## Partition Key

- The **partition key** is the attribute DynamoDB uses to find an item. It hashes the value to decide where the item is stored.
- With only a partition key (no sort key), each key value is one item. Writing an item with a key that already exists **replaces** the old item.
- A random UUID is a good key when you just need one item per event, like one per message: two writes never collide, and writes spread evenly.
- A **sort key** adds a second part, so many items can share a partition key and come back in order (for example a user ID plus a timestamp). Add one only if you'll query that way.

## Time to Live (TTL)

- TTL deletes old items for you. You name one attribute, and each item stores its expiry time there.
- The value must be a **Number** holding Unix epoch time in **seconds**. Any other type is ignored, and that item never expires.

  ```js
  const now = new Date();
  const expiresAt = Math.floor(now.getTime() / 1000) + 90 * 24 * 60 * 60; // 90 days
  ```

- Deletion is not instant. Expired items are usually removed within a few days, and until then they still show up in reads. Filter them out if exact timing matters.
- TTL deletes are free. They don't use write capacity.
- Turn it on in **DynamoDB > Tables > (table) > Settings > Time to Live (TTL) > Turn on**, and enter the attribute name (it's case-sensitive). It can take up to an hour to apply, but you can write items right away.

## On-Demand Pricing

Prices for us-east-1, checked 2026-10-13:

- **Writes**: $0.625 per million write request units. A standard write of up to 1 KB is 1 unit.
- **Reads**: $0.125 per million read request units.
- **Storage**: $0.25 per GB-month, with the first 25 GB free on the Standard table class.
- The free tier's capacity units apply to provisioned mode. On-demand pays per request from the first one, but a thousand small writes cost less than a tenth of a cent.
- **Encryption at rest** is always on. The default AWS owned key is free. An AWS managed key or a customer managed key adds AWS KMS charges.

## Creating a Small Table in the Console

**DynamoDB > Tables > Create table**, then **Customize settings** to see every option:

- **Table class**: DynamoDB Standard. Standard-IA only pays off when storage is most of the bill.
- **Capacity mode**: On-demand. Leave **Maximum table throughput** unchecked.
- **Warm throughput**: keep the defaults. They're free. Raising them pre-warms the table for a planned spike, and that costs extra.
- **Secondary indexes** and **vector indexes**: none. Indexes add storage and write cost. Vector indexes are for similarity search over embeddings.
- **Encryption at rest**: AWS owned key.
- **Deletion protection**: on. Nobody can delete the table until this is turned off first. It's free.
- **Resource-based policy**: empty. If an IAM role already grants access, a table policy is a second place to keep in sync.
- The **Settings** tab of the new table shows the partition key, capacity mode, status and the table ARN, which the IAM policy will need.
- Leave **point-in-time recovery** off unless you need backups. It adds cost.
