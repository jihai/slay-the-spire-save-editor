#!/usr/bin/env python3
"""Slay the Spire save file editor.

Decode .autosave files to JSON, edit, and re-encode.

Usage:
    python sts_save_editor.py decode <save_file> [output.json]
    python sts_save_editor.py encode <input.json> [save_file]
    python sts_save_editor.py edit <save_file>
"""

import base64
import json
import sys
import os
import tempfile
import subprocess

XOR_KEY = b"key"


def xor_crypt(data: bytes) -> bytes:
    return bytes(b ^ XOR_KEY[i % len(XOR_KEY)] for i, b in enumerate(data))


def decode_save(raw: str) -> dict:
    return json.loads(xor_crypt(base64.b64decode(raw.strip())))


def encode_save(obj: dict) -> str:
    return base64.b64encode(xor_crypt(json.dumps(obj, separators=(",", ":")).encode())).decode()


def cmd_decode(save_path: str, out_path: str | None = None):
    with open(save_path, "r") as f:
        obj = decode_save(f.read())
    text = json.dumps(obj, indent=2)
    if out_path:
        with open(out_path, "w") as f:
            f.write(text + "\n")
        print(f"Decoded to {out_path}")
    else:
        print(text)


def cmd_encode(json_path: str, out_path: str | None = None):
    with open(json_path, "r") as f:
        obj = json.load(f)
    encoded = encode_save(obj)
    if out_path:
        with open(out_path, "w") as f:
            f.write(encoded)
        print(f"Encoded to {out_path}")
    else:
        print(encoded)


def cmd_edit(save_path: str):
    with open(save_path, "r") as f:
        obj = decode_save(f.read())

    editor = os.environ.get("EDITOR", "vim")
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tmp:
        json.dump(obj, tmp, indent=2)
        tmp.write("\n")
        tmp_path = tmp.name

    try:
        subprocess.run([editor, tmp_path], check=True)
        with open(tmp_path, "r") as f:
            edited = json.load(f)
        with open(save_path, "w") as f:
            f.write(encode_save(edited))
        print(f"Saved back to {save_path}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON after edit: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        os.unlink(tmp_path)


COMMANDS = {"decode": cmd_decode, "encode": cmd_encode, "edit": cmd_edit}


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in COMMANDS:
        print(__doc__.strip())
        sys.exit(1)
    COMMANDS[sys.argv[1]](*sys.argv[2:])


if __name__ == "__main__":
    main()
