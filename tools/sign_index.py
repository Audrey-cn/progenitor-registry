#!/usr/bin/env python3
"""
[sign_index] 签名 registry index —— 使用 registry 私钥对 .akashic_index.json 签名。

用法:
    REGISTRY_PRIVATE_KEY_JSON='{"node_id":"progenitor-registry",...}' python3 tools/sign_index.py

输出:
    .akashic_index.json.sig  —— 签名信封（与索引文件放在同一目录）
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

# Ensure we can import from the protocol's hatchery
REPO_DIR = Path(__file__).resolve().parent.parent
PROTOCOL_DIR = REPO_DIR.parent / "progenitor-protocol"
HATCHERY_DIR = PROTOCOL_DIR / "hatchery"
sys.path.insert(0, str(HATCHERY_DIR))

from stargate_identity import sign_document, public_identity


INDEX_FILE = REPO_DIR / ".akashic_index.json"
SIG_FILE = REPO_DIR / ".akashic_index.json.sig"
SCHEMA_VERSION = "akashic.index-signature/v1"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_signature_envelope(index_bytes: bytes, identity: dict) -> dict:
    """Build and sign the signature envelope for the index."""
    index_sha256 = sha256_hex(index_bytes)

    envelope = {
        "schema_version": SCHEMA_VERSION,
        "index_sha256": index_sha256,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # sign_document embeds the public key and signature into the envelope
    signed = sign_document(envelope, identity)
    return signed


def main() -> None:
    if not INDEX_FILE.exists():
        print(f"[sign_index] ERROR: {INDEX_FILE} not found — run gatekeeper first", file=sys.stderr)
        sys.exit(1)

    private_key_json = os.environ.get("REGISTRY_PRIVATE_KEY_JSON")
    if not private_key_json:
        print("[sign_index] ERROR: REGISTRY_PRIVATE_KEY_JSON not set", file=sys.stderr)
        print("  Set this CI secret with the full registry identity JSON (including private_key).", file=sys.stderr)
        sys.exit(1)

    try:
        identity = json.loads(private_key_json)
    except json.JSONDecodeError as e:
        print(f"[sign_index] ERROR: invalid REGISTRY_PRIVATE_KEY_JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if "private_key" not in identity or "d" not in identity.get("private_key", {}):
        print("[sign_index] ERROR: REGISTRY_PRIVATE_KEY_JSON missing private_key.d", file=sys.stderr)
        sys.exit(1)

    index_bytes = INDEX_FILE.read_bytes()
    signed_envelope = build_signature_envelope(index_bytes, identity)

    SIG_FILE.write_text(json.dumps(signed_envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[sign_index] ✅ Signed {INDEX_FILE.name}")
    print(f"  index_sha256:  {signed_envelope['index_sha256']}")
    print(f"  public_key_id: {signed_envelope.get('signature', {}).get('public_key_id', 'N/A')}")
    print(f"  sig written:   {SIG_FILE}")


if __name__ == "__main__":
    main()
