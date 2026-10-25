import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a commerce snapshot to the local service")
    parser.add_argument("input", type=Path)
    parser.add_argument("--service-url", default="http://127.0.0.1:8000/snapshots/nightly")
    args = parser.parse_args()

    payload = args.input.read_bytes()
    request = Request(
        args.service_url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=30) as response:
        print(json.dumps(json.load(response), indent=2))


if __name__ == "__main__":
    main()
