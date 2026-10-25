import hashlib
import json
from dataclasses import dataclass

from .models import OrderRecord, SnapshotRequest


@dataclass(frozen=True)
class BuiltSnapshot:
    key: str
    content: bytes
    order_count: int
    receipt_ready_count: int
    idempotency_key: str


def receipt_is_ready(order: OrderRecord) -> bool:
    return (
        order.checkout.paid_at is not None
        and order.fulfillment.status in {"shipped", "delivered"}
        and order.receipt is not None
        and order.receipt.issued_at is not None
        and bool(order.customer_updates)
    )


def build_snapshot(request: SnapshotRequest) -> BuiltSnapshot:
    records = []
    for order in sorted(request.orders, key=lambda item: item.order_id):
        record = order.model_dump(mode="json")
        record["receipt_ready"] = receipt_is_ready(order)
        records.append(record)

    document = {
        "snapshot_date": request.snapshot_date.isoformat(),
        "orders": records,
    }
    content = (json.dumps(document, separators=(",", ":"), sort_keys=True) + "\n").encode()
    digest = hashlib.sha256(content).hexdigest()
    key = f"commerce/{request.snapshot_date.isoformat()}/orders.json"
    return BuiltSnapshot(
        key=key,
        content=content,
        order_count=len(records),
        receipt_ready_count=sum(record["receipt_ready"] for record in records),
        idempotency_key=f"nightly-{request.snapshot_date.isoformat()}-{digest[:16]}",
    )
