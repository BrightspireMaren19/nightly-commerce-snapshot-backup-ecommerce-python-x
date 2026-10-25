import json

from nightly_snapshot.models import SnapshotRequest
from nightly_snapshot.snapshot_builder import build_snapshot


def test_snapshot_marks_only_complete_receipt_story_as_ready() -> None:
    request = SnapshotRequest.model_validate(
        {
            "snapshot_date": "2026-09-05",
            "orders": [
                {
                    "order_id": "ord_paid",
                    "customer_id": "cus_1",
                    "checkout": {
                        "checkout_id": "chk_1",
                        "paid_at": "2026-09-05T10:00:00Z",
                        "total": "24.00",
                        "currency": "USD",
                    },
                    "fulfillment": {"status": "shipped"},
                    "receipt": {
                        "receipt_id": "rcpt_1",
                        "issued_at": "2026-09-05T10:01:00Z",
                    },
                    "customer_updates": [
                        {
                            "occurred_at": "2026-09-05T12:00:00Z",
                            "message": "Shipped",
                        }
                    ],
                },
                {
                    "order_id": "ord_waiting",
                    "customer_id": "cus_2",
                    "checkout": {
                        "checkout_id": "chk_2",
                        "paid_at": "2026-09-05T11:00:00Z",
                        "total": "12.50",
                        "currency": "USD",
                    },
                    "fulfillment": {"status": "pending"},
                    "receipt": None,
                    "customer_updates": [],
                },
            ],
        }
    )

    snapshot = build_snapshot(request)
    document = json.loads(snapshot.content)

    readiness = {order["order_id"]: order["receipt_ready"] for order in document["orders"]}
    assert readiness == {"ord_paid": True, "ord_waiting": False}
    assert snapshot.receipt_ready_count == 1
    assert snapshot.key == "commerce/2026-09-05/orders.json"
