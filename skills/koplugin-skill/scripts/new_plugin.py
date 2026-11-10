#!/usr/bin/env python3
"""Scaffold a new KOReader plugin from the bundled template.

Usage: new_plugin.py <id> "<Full Name>" [--dir DIR] [--force]

<id> is lowercase letters/digits/underscore (e.g. readstreak); the plugin is
created as DIR/<id>.koplugin (default DIR = current directory).
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.koplugin"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("id")
    p.add_argument("fullname")
    p.add_argument("--dir", default=".")
    p.add_argument("--force", action="store_true", help="overwrite an existing plugin dir")
    a = p.parse_args()

    if not re.fullmatch(r"[a-z][a-z0-9_]*", a.id):
        print("error: <id> must match [a-z][a-z0-9_]*", file=sys.stderr)
        return 2
    if '"' in a.fullname or "]]" in a.fullname or "\\" in a.fullname:
        print('error: fullname may not contain ", \\ or ]]', file=sys.stderr)
        return 2

    dest = Path(a.dir).expanduser() / f"{a.id}.koplugin"
    if dest.exists():
        if not a.force:
            print(f"error: {dest} exists (use --force)", file=sys.stderr)
            return 1
        shutil.rmtree(dest)

    cls = "".join(w.capitalize() for w in a.id.split("_")) or "Plugin"
    shutil.copytree(TEMPLATE, dest)
    for f in dest.rglob("*"):
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            text = text.replace("__FULLNAME__", a.fullname).replace("__CLASS__", cls).replace("__ID__", a.id)
            f.write_text(text, encoding="utf-8")

    print(f"created {dest}")
    print(f"next: python3 {Path(__file__).with_name('validate_plugin.py')} {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
