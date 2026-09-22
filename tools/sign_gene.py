#!/usr/bin/env python3
"""[sign_gene] A creator signs a gene → signatures/<sha>.sig, verifiable against the trust keyring.

Usage:
    CREATOR_PRIVATE_KEY_JSON='{...full identity incl private_key...}' \
        python3 tools/sign_gene.py genes/<sha>

Writes signatures/<sha>.sig — a sign_document envelope over the gene's content_sha256. The
gatekeeper upgrades such a gene's trust_state to 'creator-signed:<owner>' when the signer's
key is in the trust keyring and the declared creator matches (docs/VISION.md, pillar A).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
PROTOCOL_DIR = Path(os.environ.get("PROGENITOR_PROTOCOL_DIR", REPO_DIR.parent / "progenitor-protocol"))
sys.path.insert(0, str(PROTOCOL_DIR / "hatchery"))

from stargate_identity import public_identity, sign_document  # noqa: E402

SIGNATURES_DIR = REPO_DIR / "signatures"


def build_gene_signature(gene_path: Path, identity: dict) -> dict:
    """Build a self-certifying signed envelope over the gene's content hash.

    The creator's public identity is embedded BEFORE signing, so a reviewer can check
    signature well-formedness without the keyring (TOFU pattern, as in the R1.3 handshake):
    verify_document(envelope, envelope["public_key"]) -> well-formed but unknown signer ->
    gatekeeper marks `creator-signature-pending-review` (not `invalid`).
    """
    sha = hashlib.sha256(Path(gene_path).read_bytes()).hexdigest()
    envelope = {
        "schema_version": "akashic.gene-signature/v1",
        "content_sha256": sha,
        "capability_path": f"genes/{sha}",
        "public_key": public_identity(identity)["public_key"],
    }
    return sign_document(envelope, identity)


def generate_creator_identity(label: str = "creator") -> dict:
    """Generate a fresh creator identity (run once, keep the JSON private)."""
    from stargate_identity import generate_identity
    return generate_identity(label)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python3 tools/sign_gene.py <gene_file>", file=sys.stderr)
        return 2
    gene_path = Path(sys.argv[1])
    if not gene_path.exists():
        print(f"[sign_gene] ERROR: {gene_path} not found", file=sys.stderr)
        return 1
    if sys.argv[1] == "--gen-identity":
        label = sys.argv[2] if len(sys.argv) > 2 else "creator"
        ident = generate_creator_identity(label)
        out = Path(f"{label}-identity.json")
        out.write_text(json.dumps(ident, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8", newline="")
        print(f"[sign_gene] ✅ creator identity written: {out}")
        print("  保密此文件(含私钥); PR 时只需提交其中的 public_key / node_id。")
        return 0
    key_json = os.environ.get("CREATOR_PRIVATE_KEY_JSON")
    if not key_json:
        print("[sign_gene] ERROR: CREATOR_PRIVATE_KEY_JSON not set (full identity incl private_key)", file=sys.stderr)
        return 1
    try:
        identity = json.loads(key_json)
    except json.JSONDecodeError as exc:
        print(f"[sign_gene] ERROR: invalid CREATOR_PRIVATE_KEY_JSON: {exc}", file=sys.stderr)
        return 1
    if "private_key" not in identity or "d" not in identity.get("private_key", {}):
        print("[sign_gene] ERROR: identity missing private_key.d", file=sys.stderr)
        return 1

    signed = build_gene_signature(gene_path, identity)
    SIGNATURES_DIR.mkdir(exist_ok=True)
    out = SIGNATURES_DIR / f"{signed['content_sha256']}.sig"
    out.write_text(json.dumps(signed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")
    print(f"[sign_gene] ✅ signed {gene_path.name} -> {out}")
    print(f"  content_sha256: {signed['content_sha256']}")
    print(f"  signer key_id:  {signed.get('signature', {}).get('public_key_id', 'N/A')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
