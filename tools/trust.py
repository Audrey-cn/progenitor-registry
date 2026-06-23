"""[trust] Registry web-of-trust — keyring, configurable trust set, verification, reputation.

Iteration 2 (docs/VISION.md, pillar A): trust the signer, not the platform. The keyring
(``policy/trusted_keys.json``) lists the creator identities this registry trusts; the founder
key is the trust root, not a sole authority. A host can narrow trust to a subset via the
``PROGENITOR_TRUST_SET`` env var (comma-separated owners or key_ids; ``all`` / unset = every
key in the ring). ``verify_signed_document`` checks a ``sign_document`` envelope against the
trusted set — verification uses the *trusted* public key, never the key embedded in the
envelope, so a stranger cannot self-attest. Reputation is surfaced honestly from the score log
(today the scores are seeded at 0 — a record, not yet earned reputation).

Reuses the protocol's ``stargate_identity`` as the single source of truth for crypto.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REGISTRY_DIR = Path(__file__).resolve().parent.parent
KEYRING_FILE = REGISTRY_DIR / "policy" / "trusted_keys.json"
SCORE_LOG_FILE = REGISTRY_DIR / ".gene_score_log.json"


def _load_identity_module():
    """Locate the sibling protocol's stargate_identity (single source of truth for crypto)."""
    protocol_dir = Path(os.environ.get("PROGENITOR_PROTOCOL_DIR", REGISTRY_DIR.parent / "progenitor-protocol"))
    hatchery = protocol_dir / "hatchery"
    if hatchery.is_dir() and str(hatchery) not in sys.path:
        sys.path.insert(0, str(hatchery))
    import stargate_identity
    return stargate_identity


def load_keyring(path=None):
    """Return the list of trusted-key records, or [] if the keyring is absent.

    Path resolution: explicit ``path`` arg > ``PROGENITOR_TRUST_KEYRING_FILE`` env > the bundled
    ``policy/trusted_keys.json``. The env override lets a host pin its own keyring."""
    if path is None:
        path = os.environ.get("PROGENITOR_TRUST_KEYRING_FILE") or KEYRING_FILE
    path = Path(path)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("trusted_keys", [])


def trusted_set(keyring=None):
    """The configured trust set. PROGENITOR_TRUST_SET narrows the keyring to listed owners /
    key_ids; 'all' or unset trusts every key in the ring."""
    keyring = keyring if keyring is not None else load_keyring()
    raw = os.environ.get("PROGENITOR_TRUST_SET", "").strip()
    if not raw or raw.lower() == "all":
        return list(keyring)
    wanted = {x.strip() for x in raw.split(",") if x.strip()}
    return [k for k in keyring if k.get("owner") in wanted or k.get("key_id") in wanted]


def verify_signed_document(envelope, keyring=None):
    """Verify a sign_document envelope against the trusted set.

    Returns (ok: bool, info: dict). On success info has owner/key_id/role of the verifying key;
    on failure info has a 'reason'. Verification is done with each trusted public key — never the
    key carried inside the envelope — so a stranger's self-signed document is rejected.
    """
    trusted = trusted_set(keyring)
    if not trusted:
        return False, {"reason": "no trusted keys configured"}
    if not isinstance(envelope, dict) or "signature" not in envelope:
        return False, {"reason": "document is not signed"}
    ident = _load_identity_module()
    for key in trusted:
        pub = key.get("public_key")
        if not pub:
            continue
        try:
            if ident.verify_document(envelope, pub):
                return True, {"owner": key.get("owner"), "key_id": key.get("key_id"), "role": key.get("role")}
        except Exception:
            continue
    return False, {"reason": "no trusted key verified the signature"}


def load_reputation(path=None):
    """Load the per-capability score log, or {} if absent."""
    path = Path(path) if path else SCORE_LOG_FILE
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def reputation_for(capability, score_log=None):
    """Surface a capability's reputation from the score log (honest: scores are seeded at 0).

    Tiers: 'flagged' (any reports), 'established' (positive score or downloads), 'new' (recorded
    but unproven), 'unrated' (not in the log).
    """
    log = score_log if score_log is not None else load_reputation()
    record = log.get(capability)
    if not record:
        return {"capability": capability, "known": False, "tier": "unrated"}
    score = record.get("score", 0)
    downloads = record.get("downloads", 0)
    reports = record.get("reports", 0)
    if reports > 0:
        tier = "flagged"
    elif score > 0 or downloads > 0:
        tier = "established"
    else:
        tier = "new"
    return {
        "capability": capability,
        "known": True,
        "score": score,
        "downloads": downloads,
        "reports": reports,
        "tier": tier,
    }
