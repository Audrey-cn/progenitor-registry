#!/usr/bin/env python3
"""[trust_report] Surface the registry web-of-trust in one view (docs/VISION.md, pillar A):
who signed the index (verified against the trusted keyring, not the embedded key), whether the
signed hash still matches the index, and each gene's creator + trust_state + reputation tier.

Usage:
    python3 tools/trust_report.py        # exit 0 iff the index signature is trusted AND intact
Honors PROGENITOR_TRUST_SET to narrow the trusted creators.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trust  # noqa: E402

REGISTRY_DIR = Path(__file__).resolve().parent.parent
INDEX_FILE = REGISTRY_DIR / ".akashic_index.json"
SIG_FILE = REGISTRY_DIR / ".akashic_index.json.sig"


def build_report(index_file=INDEX_FILE, sig_file=SIG_FILE, keyring=None, score_log=None):
    """Compute the trust report as a dict (pure — no printing)."""
    index_file, sig_file = Path(index_file), Path(sig_file)
    report = {"index_present": index_file.exists(), "signature": {}, "genes": []}
    if not index_file.exists():
        report["signature"] = {"trusted": False, "reason": "index not found"}
        return report

    index = json.loads(index_file.read_text(encoding="utf-8"))
    index_sha = hashlib.sha256(index_file.read_bytes()).hexdigest()

    sig_ok, sig_info, hash_ok = False, {"reason": "signature file not found"}, False
    if sig_file.exists():
        envelope = json.loads(sig_file.read_text(encoding="utf-8"))
        sig_ok, sig_info = trust.verify_signed_document(envelope, keyring)
        hash_ok = envelope.get("index_sha256") == index_sha

    if sig_ok and hash_ok:
        reason = None
    elif not sig_ok:
        reason = sig_info.get("reason")
    else:
        reason = "index hash does not match the signed hash"
    report["signature"] = {
        "trusted": bool(sig_ok and hash_ok),
        "signed_by": sig_info if sig_ok else None,
        "hash_intact": hash_ok,
        "reason": reason,
    }

    log = score_log if score_log is not None else trust.load_reputation()
    entries = sorted((k, v) for k, v in index.items() if isinstance(v, dict) and not k.startswith("_"))
    for cap, entry in entries:
        report["genes"].append({
            "capability": cap,
            "creator": entry.get("creator", "Anonymous"),
            "content_sha256": (entry.get("content_sha256") or "")[:12],
            "trust_state": entry.get("trust_state", "unknown"),
            "reputation": trust.reputation_for(cap, score_log=log)["tier"],
        })
    return report


def main():
    report = build_report()
    sig = report["signature"]
    if sig["trusted"]:
        sb = sig["signed_by"]
        print(f"✅ index signature TRUSTED — signed by {sb.get('owner')} ({sb.get('role')}), hash intact")
    else:
        print(f"❌ index signature NOT trusted — {sig.get('reason')}")
    print(f"\n{'capability':<22} {'creator':<14} {'hash':<14} {'trust_state':<20} reputation")
    print("-" * 86)
    for g in report["genes"]:
        print(f"{g['capability']:<22} {g['creator']:<14} {g['content_sha256']:<14} {g['trust_state']:<20} {g['reputation']}")
    return 0 if sig["trusted"] else 1


if __name__ == "__main__":
    sys.exit(main())
