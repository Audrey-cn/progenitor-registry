"""Web-of-trust foundation — keyring, trust set, signature verification, reputation (Iteration 2)."""
import sys
from pathlib import Path

import pytest

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR / "tools"))
import trust  # noqa: E402


def _ident_mod():
    mod = trust._load_identity_module()
    if mod is None:  # pragma: no cover
        pytest.skip("sibling protocol stargate_identity not available")
    return mod


def _make_identity(name):
    return _ident_mod().generate_identity(name, bits=512)


def _keyring_from(identity, owner="Tester", role="creator"):
    return [{
        "owner": owner,
        "role": role,
        "key_id": identity["public_key_id"],
        "public_key": identity["public_key"],
    }]


# --- keyring + trust set -------------------------------------------------------------------

def test_load_keyring_has_founder():
    ring = trust.load_keyring()
    assert "Audrey" in {k["owner"] for k in ring}
    assert any(k.get("role") == "founder" for k in ring)


def test_trusted_set_default_is_all(monkeypatch):
    monkeypatch.delenv("PROGENITOR_TRUST_SET", raising=False)
    ring = [{"owner": "A", "key_id": "k1"}, {"owner": "B", "key_id": "k2"}]
    assert len(trust.trusted_set(ring)) == 2


def test_trusted_set_narrows_to_subset(monkeypatch):
    monkeypatch.setenv("PROGENITOR_TRUST_SET", "B")
    ring = [{"owner": "A", "key_id": "k1"}, {"owner": "B", "key_id": "k2"}]
    sel = trust.trusted_set(ring)
    assert len(sel) == 1 and sel[0]["owner"] == "B"


# --- signature verification ----------------------------------------------------------------

def test_verify_accepts_trusted_signer():
    mod = _ident_mod()
    identity = _make_identity("tester-node")
    envelope = mod.sign_document({"hello": "world"}, identity)
    ok, info = trust.verify_signed_document(envelope, _keyring_from(identity))
    assert ok is True and info["owner"] == "Tester"


def test_verify_rejects_untrusted_signer():
    mod = _ident_mod()
    signer = _make_identity("attacker")
    trusted = _make_identity("trusted")
    envelope = mod.sign_document({"hello": "world"}, signer)  # signed by attacker
    ok, _ = trust.verify_signed_document(envelope, _keyring_from(trusted))  # ring trusts 'trusted' only
    assert ok is False


def test_verify_rejects_signer_outside_trust_set(monkeypatch):
    mod = _ident_mod()
    identity = _make_identity("bob-node")
    envelope = mod.sign_document({"x": 1}, identity)
    monkeypatch.setenv("PROGENITOR_TRUST_SET", "Alice")  # excludes Bob
    ok, _ = trust.verify_signed_document(envelope, _keyring_from(identity, owner="Bob"))
    assert ok is False


def test_verify_rejects_unsigned_document():
    ok, info = trust.verify_signed_document({"no": "sig"}, [{"owner": "X", "public_key": {}}])
    assert ok is False and "not signed" in info["reason"]


# --- reputation ----------------------------------------------------------------------------

def test_reputation_unrated_for_unknown():
    rep = trust.reputation_for("does-not-exist", score_log={})
    assert rep["known"] is False and rep["tier"] == "unrated"


def test_reputation_new_for_seeded_zero():
    rep = trust.reputation_for("g", score_log={"g": {"score": 0, "downloads": 0, "reports": 0}})
    assert rep["tier"] == "new"


def test_reputation_flagged_when_reported():
    rep = trust.reputation_for("g", score_log={"g": {"score": 5, "downloads": 3, "reports": 2}})
    assert rep["tier"] == "flagged"


def test_reputation_established_with_activity():
    rep = trust.reputation_for("g", score_log={"g": {"score": 5, "downloads": 3, "reports": 0}})
    assert rep["tier"] == "established"
