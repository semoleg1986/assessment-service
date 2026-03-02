from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from src.interface.http.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    app = create_app()
    spec = app.openapi()
    output = Path(args.output)

    if args.check:
        if not output.exists():
            raise SystemExit(f"{output} does not exist")
        current = yaml.safe_load(output.read_text(encoding="utf-8"))
        if json.dumps(current, sort_keys=True) != json.dumps(spec, sort_keys=True):
            raise SystemExit("OpenAPI artifact is out of sync. Run make openapi-export")
        return

    output.write_text(
        yaml.safe_dump(spec, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
