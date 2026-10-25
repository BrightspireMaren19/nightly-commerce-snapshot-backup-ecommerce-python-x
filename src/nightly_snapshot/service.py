import json
import os

from fastapi import FastAPI, HTTPException

from .infrai_storage import InfraiError, InfraiStorage
from .models import SnapshotRequest, SnapshotResult
from .snapshot_builder import build_snapshot


app = FastAPI(title="Nightly commerce snapshot")


@app.post("/snapshots/nightly", response_model=SnapshotResult)
def create_nightly_snapshot(request: SnapshotRequest) -> SnapshotResult:
    bucket = os.environ.get("SNAPSHOT_BUCKET", "commerce-nightly-snapshots")
    snapshot = build_snapshot(request)
    storage = InfraiStorage()
    try:
        storage.create_bucket(bucket)
        storage.put_snapshot(
            bucket=bucket,
            key=snapshot.key,
            content=snapshot.content,
            idempotency_key=snapshot.idempotency_key,
        )
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=exc.detail) from exc
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail="Storage transport failed") from exc

    return SnapshotResult(
        bucket=bucket,
        key=snapshot.key,
        order_count=snapshot.order_count,
        receipt_ready_count=snapshot.receipt_ready_count,
    )
