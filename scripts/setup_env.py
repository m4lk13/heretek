#!/usr/bin/env python3
"""Populate .env's two secret fields without echoing the token."""
from __future__ import annotations

import getpass
import pathlib
import re
import sys


def main() -> int:
    env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        print(f"no {env_path} — create it from .env.example first", file=sys.stderr)
        return 1

    tok = getpass.getpass("Bot token: ").strip()
    oid = input("Owner user_id: ").strip()

    if not tok:
        print("token empty — aborting", file=sys.stderr)
        return 1
    if not oid.isdigit():
        print(f"owner_id {oid!r} not a positive integer — aborting", file=sys.stderr)
        return 1

    text = env_path.read_text()
    text = re.sub(r"^TELEGRAM_BOT_TOKEN=.*", f"TELEGRAM_BOT_TOKEN={tok}", text, flags=re.M)
    text = re.sub(r"^HERETEK_OWNER_USER_ID=.*", f"HERETEK_OWNER_USER_ID={oid}", text, flags=re.M)
    env_path.write_text(text)

    print(f"patched. token_len={len(tok)} owner_id={oid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
