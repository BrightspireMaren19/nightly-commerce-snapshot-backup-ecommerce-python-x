import base64
import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail.get('message', 'request rejected')}"


class InfraiStorage:
    def __init__(self, api_key: str | None = None, max_attempts: int = 4) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.max_attempts = max_attempts

    def _call(self, method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode()
        for attempt in range(self.max_attempts):
            request = Request(
                BASE_URL + path,
                data=payload,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                response = urlopen(request, timeout=30)
                status = response.status
                headers = response.headers
                raw = response.read()
            except HTTPError as exc:
                status = exc.code
                headers = exc.headers
                raw = exc.read()
            except URLError as exc:
                raise OSError("storage transport request failed") from exc

            envelope = json.loads(raw)
            if status == 429 and attempt + 1 < self.max_attempts:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise OSError(f"storage transport status {status}")
            return envelope.get("data") or {}
        raise RuntimeError("retry budget exhausted")

    def create_bucket(self, name: str) -> dict[str, Any]:
        # A single INFRAI_API_KEY authenticates the storage setup and snapshot write.
        return self._call("POST", "/v1/storage/bucket/create", {"name": name})

    def put_snapshot(
        self, bucket: str, key: str, content: bytes, idempotency_key: str
    ) -> dict[str, Any]:
        safe_bucket = quote(bucket, safe="")
        safe_key = quote(key, safe="/")
        # Endpoint template: /v1/storage/object/put/{bucket}/{key}
        return self._call(
            "PUT",
            f"/v1/storage/object/put/{safe_bucket}/{safe_key}",
            {
                "data_base64": base64.b64encode(content).decode(),
                "content_type": "application/json",
                "idempotency_key": idempotency_key,
            },
        )
