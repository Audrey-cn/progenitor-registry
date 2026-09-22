"""Per-creator gene signing → gatekeeper trust_state upgrade (Iteration 2, increment B)."""
import json
import sys
from pathlib import Path

import pytest

from conftest import create_valid_gene, save_temp_gene, clean_test_data

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR / ".github" / "workflows"))
sys.path.insert(0, str(REPO_DIR / "tools"))
import gatekeeper  # noqa: E402
import sign_gene  # noqa: E402


def _trust_or_skip():
    trust = gatekeeper._load_trust_module()
    if trust is None:
        pytest.skip("sibling protocol / trust module not available")
    return trust


def _creator_identity(name="CreatorX"):
    trust = _trust_or_skip()
    return trust._load_identity_module().generate_identity(name.lower(), bits=512)


def _pin_keyring(tmp_path, monkeypatch, owner, identity):
    keyring = tmp_path / "trusted_keys.json"
    keyring.write_text(json.dumps({
        "trusted_keys": [{"owner": owner, "public_key": identity["public_key"]}]
    }), encoding="utf-8")
    monkeypatch.setenv("PROGENITOR_TRUST_KEYRING_FILE", str(keyring))


def test_unsigned_gene_stays_registry_verified(tmp_path, monkeypatch):
    monkeypatch.setattr(gatekeeper, "SIGNATURES_DIR", tmp_path / "signatures")
    gf = save_temp_gene(create_valid_gene("plain"), name="unsigned-sha")
    assert gatekeeper.gene_trust_state(gf, {"creator": "Audrey"}, "unsigned-sha") == "registry_verified"


def test_valid_creator_signature_upgrades_trust_state(tmp_path, monkeypatch):
    _trust_or_skip()
    identity = _creator_identity("CreatorX")
    _pin_keyring(tmp_path, monkeypatch, "CreatorX", identity)
    sigs = tmp_path / "signatures"
    sigs.mkdir()
    monkeypatch.setattr(gatekeeper, "SIGNATURES_DIR", sigs)

    gf = save_temp_gene(create_valid_gene("signed", creator="CreatorX"), name="creatorx-gene")
    sha = gatekeeper.compute_sha256(gf)
    signed = sign_gene.build_gene_signature(gf, identity)
    (sigs / f"{sha}.sig").write_text(json.dumps(signed), encoding="utf-8")

    assert gatekeeper.gene_trust_state(gf, {"creator": "CreatorX"}, sha) == "creator-signed:CreatorX"


def test_creator_mismatch_is_invalid(tmp_path, monkeypatch):
    _trust_or_skip()
    identity = _creator_identity("CreatorX")
    _pin_keyring(tmp_path, monkeypatch, "CreatorX", identity)
    sigs = tmp_path / "signatures"
    sigs.mkdir()
    monkeypatch.setattr(gatekeeper, "SIGNATURES_DIR", sigs)

    gf = save_temp_gene(create_valid_gene("mismatch", creator="Bob"), name="mismatch-gene")
    sha = gatekeeper.compute_sha256(gf)
    signed = sign_gene.build_gene_signature(gf, identity)  # signed by CreatorX, but meta says Bob
    (sigs / f"{sha}.sig").write_text(json.dumps(signed), encoding="utf-8")

    assert gatekeeper.gene_trust_state(gf, {"creator": "Bob"}, sha) == "creator-signature-invalid"


def test_unknown_signer_is_pending_review(tmp_path, monkeypatch):
    """A first-time contributor: well-formed signature, signer not yet in the keyring.
    Must be *pending review*, not invalid — the maintainer adds the key in review."""
    _trust_or_skip()
    signer = _creator_identity("NewContributor")
    sigs = tmp_path / "signatures"
    sigs.mkdir()
    monkeypatch.setattr(gatekeeper, "SIGNATURES_DIR", sigs)

    gf = save_temp_gene(create_valid_gene("firstpr", creator="NewContributor"), name="firstpr-gene")
    sha = gatekeeper.compute_sha256(gf)
    signed = sign_gene.build_gene_signature(gf, signer)
    assert signed.get("public_key"), "envelope must embed the creator public identity"
    (sigs / f"{sha}.sig").write_text(json.dumps(signed), encoding="utf-8")

    assert gatekeeper.gene_trust_state(gf, {"creator": "NewContributor"}, sha) == "creator-signature-pending-review"


def test_tampered_signature_is_invalid(tmp_path, monkeypatch):
    _trust_or_skip()
    signer = _creator_identity("Honest")
    sigs = tmp_path / "signatures"
    sigs.mkdir()
    monkeypatch.setattr(gatekeeper, "SIGNATURES_DIR", sigs)

    gf = save_temp_gene(create_valid_gene("honest"), name="honest-gene")
    sha = gatekeeper.compute_sha256(gf)
    signed = sign_gene.build_gene_signature(gf, signer)
    signed["content_sha256"] = "0" * 64  # tamper the covered content hash
    (sigs / f"{sha}.sig").write_text(json.dumps(signed), encoding="utf-8")

    assert gatekeeper.gene_trust_state(gf, {"creator": "Honest"}, sha) == "creator-signature-invalid"


def teardown_module():
    clean_test_data()
