#!/usr/bin/env python3
"""Patch an isolated TBX Hybrid preview identity into Starling packaging."""
import argparse
from pathlib import Path

def replace_one(text, original, updated):
    if text.count(original) == 1:
        return text.replace(original, updated, 1)
    if text.count(updated) == 1 and original not in text:
        return text
    raise ValueError("Starling build identity changed; refusing unsafe patch")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    path = args.source / "packaging/android/build_apk.py"
    old = path.read_text(encoding="utf-8")
    new = replace_one(old, 'APPLICATION_ID = "io.github.juanluci.starling"',
                           'APPLICATION_ID = "dev.tbx.hybrid"')
    new = replace_one(new, 'LABEL = "Starling"', 'LABEL = "TBX Hybrid"')
    if not args.check:
        path.write_text(new, encoding="utf-8")
    print("PASS: isolated preview app: dev.tbx.hybrid.preview / TBX Hybrid Preview")

if __name__ == "__main__":
    main()
