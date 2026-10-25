from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class Checkout(BaseModel):
    checkout_id: str
    paid_at: datetime | None = None
    total: Decimal = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)


class Fulfillment(BaseModel):
    status: Literal["pending", "shipped", "delivered", "returned"]
    carrier: str | None = None
    tracking_number: str | None = None


class Receipt(BaseModel):
    receipt_id: str
    issued_at: datetime | None = None


class CustomerOrderUpdate(BaseModel):
    occurred_at: datetime
    message: str = Field(min_length=1)


class OrderRecord(BaseModel):
    order_id: str
    customer_id: str
    checkout: Checkout
    fulfillment: Fulfillment
    receipt: Receipt | None = None
    customer_updates: list[CustomerOrderUpdate] = Field(default_factory=list)


class SnapshotRequest(BaseModel):
    snapshot_date: date
    orders: list[OrderRecord] = Field(min_length=1)


class SnapshotResult(BaseModel):
    bucket: str
    key: str
    order_count: int
    receipt_ready_count: int
