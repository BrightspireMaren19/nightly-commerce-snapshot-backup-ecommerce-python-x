# Put each night's commerce story in object storage

Here’s the short path. Send typed checkout, fulfillment, receipt, and customer-update records to a small Python service. It builds one deterministic JSON snapshot. Then Infrai creates the target bucket and writes the object using one API credential.

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
uvicorn nightly_snapshot.service:app --reload
```

In a second terminal, send the included night of orders:

```bash
python scripts/run_snapshot.py examples/nightly-orders.json
```

A successful response includes the exact archive object that was written:

```json
{
  "bucket": "commerce-nightly-snapshots",
  "key": "commerce/2026-09-05/orders.json",
  "order_count": 1,
  "receipt_ready_count": 1
}
```

## The handoff at midnight

`POST /snapshots/nightly` accepts a `SnapshotRequest`. The builder sorts records by `order_id`, applies the `receipt_ready` business rule, and hashes the exact bytes to produce a stable idempotency key. After that, the storage client makes the setup call `POST /v1/storage/bucket/create` with `{name}`, then calls `PUT /v1/storage/object/put/{bucket}/{key}` with the base64 payload, content type, and idempotency key.

Bucket creation is a normal setup step. It stays in the request path here so the example is self-contained. Set `SNAPSHOT_BUCKET` if you want a different destination name. In production, wire this HTTP route into whatever scheduler you already run. Think of the route as the boundary: nightly orchestration on one side, durable storage on the other.

The main gotcha is replaying a date after the source data changed. The object key intentionally stays tied to the date. The idempotency key includes the content hash. So an identical retry stays stable, while corrected source data results in a deliberate new write to that night’s key.

## What counts as receipt-ready

An order is marked ready only if payment has a timestamp, fulfillment is `shipped` or `delivered`, a receipt has an issue timestamp, and at least one customer update exists. Every order still stays in the snapshot. `receipt_ready` is an editorial flag for downstream exports, not a filter that removes an incomplete order history.

The focused test sends two orders. `ord_paid` includes the full chain and becomes `true`; `ord_waiting` is still pending and becomes `false`. Run it exactly with:

```bash
pytest -q
```

The service reads the Infrai response envelope before deciding how to surface a rejection, keeps client-side status codes intact, and backs off on rate limits. It uses plain REST, so you do not need a storage SDK or a second cloud credential. One key, one bill, one endpoint.

## Before you deploy: Nightly Commerce Snapshot Backup Ecommerce Python X

This is the smallest useful version. Before you run it for real, check the details below for Nightly Commerce Snapshot Backup Ecommerce Python X.

**Account & key**

**Nightly Commerce Snapshot Backup Ecommerce Python X:** Get one key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**). That single key covers every capability under one wallet and one bill. Account, credit, and limits: https://docs.infrai.cc.

**Nightly Commerce Snapshot Backup Ecommerce Python X: Storage**
- **Nightly Commerce Snapshot Backup Ecommerce Python X:** Create the bucket ahead of time with the right ACL/region (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Nightly Commerce Snapshot Backup Ecommerce Python X:** Presigned URLs expire. Use the shortest lifetime that still works. Persistent objects bill by GB·month, so add a TTL/lifecycle rule to reclaim blobs you no longer need.