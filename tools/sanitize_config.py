#!/usr/bin/env python3
import re
import sys
from pathlib import Path

SECRET_KEYS = {
    "api_key": "YOUR_API_KEY",
    "access_token": "YOUR_ACCESS_TOKEN",
    "pexels_api_key": "YOUR_PEXELS_API_KEY",
    "uid": "YOUR_UID",
    "appid": "YOUR_APPID",
}


def sanitize_line(line: str) -> str:
    m = re.match(r'^(\s*)([A-Za-z0-9_]+)(\s*=\s*)"([^"]*)"(\s*(?:#.*)?)$', line)
    if not m:
        return line

    indent, key, sep, _value, suffix = m.groups()
    if key not in SECRET_KEYS:
        return line

    replacement = SECRET_KEYS[key]
    return f'{indent}{key}{sep}"{replacement}"{suffix}'


def main() -> int:
    if len(sys.argv) != 3:
      print("Usage: sanitize_config.py <input-config.toml> <output-config.toml>", file=sys.stderr)
      return 1

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    if not src.exists():
      print(f"Input file not found: {src}", file=sys.stderr)
      return 1

    lines = src.read_text(encoding="utf-8").splitlines()
    out = [sanitize_line(line) for line in lines]
    dst.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote sanitized config: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
