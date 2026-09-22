"""R2: end-to-end external-contributor flow — scaffold → sign → Gatekeeper → trust upgrade.

Simulates the exact journey of a first-time external creator, using the real tools
(gene_scaffold, sign_gene, gatekeeper) and a fresh identity per run.
"""
import json
import sys
from pathlib import Path

import pytest

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR / ".github" / "workflows"))
sys.path.insert(0, str(REPO_DIR / "tools"))
import gatekeeper  # noqa: E402
import gene_scaffold  # noqa: E402
import sign_gene  # noqa: E402


def _trust_or_skip():
    trust = gatekeeper._load_trust_module()
    if trust is None:
        pytest.skip("sibling protocol / trust module not available")
    return trust


def test_external_creator_full_flow(tmp_path, monkeypatch):
    trust = _trust_or_skip()
    si = trust._load_identity_module()

    # 1) contributor generates a creator identity (kept private)
    identity = sign_gene.generate_creator_identity("external-contributor")

    # 2) scaffold the gene (non-interactive, as documented in CONTRIBUTING.md)
    work = tmp_path / "work"
    out = gene_scaffold.scaffold(
        "contrib-flow-check", "ExternalContributor",
        "End-to-end contributor flow verification gene", "L1", out_dir=work)

    # 3) content-address: rename to sha, place into a fake genes/ dir
    sha = gene_scaffold.compute_sha256(out)
    genes = tmp_path / "genes"
    genes.mkdir()
    gf = genes / sha
    gf.write_bytes(out.read_bytes())

    # 4) sign it — sidecar lands in signatures/
    sigs = tmp_path / "signatures"
    monkeypatch.setattr(gatekeeper, "SIGNATURES_DIR", sigs)
    signed = sign_gene.build_gene_signature(gf, identity)
    sigs.mkdir()
    (sigs / f"{sha}.sig").write_text(json.dumps(signed), encoding="utf-8")

    # 5) first Gatekeeper pass: passes L0-L6, trust = pending review (signer unknown)
    monkeypatch.delenv("PROGENITOR_TRUST_KEYRING", raising=False)
    monkeypatch.delenv("PROGENITOR_TRUST_KEYRING_FILE", raising=False)
    passed, meta, got_sha = gatekeeper.audit_gene(gf, {})
    assert passed is True
    assert gatekeeper.gene_trust_state(gf, meta, got_sha) == "creator-signature-pending-review"

    # 6) maintainer review: keyring gains the contributor's public identity
    keyring = tmp_path / "trusted_keys.json"
    keyring.write_text(json.dumps({
        "trusted_keys": [{"owner": "ExternalContributor",
                          "public_key": identity["public_key"]}]
    }), encoding="utf-8")
    monkeypatch.setenv("PROGENITOR_TRUST_KEYRING_FILE", str(keyring))

    # 7) trust upgrade visible
    assert gatekeeper.gene_trust_state(gf, meta, got_sha) == "creator-signed:ExternalContributor"

    # 8) the upgrade path through the whole audit once more (idempotent, still passing)
    passed2, meta2, sha2 = gatekeeper.audit_gene(gf, {})
    assert passed2 is True and sha2 == sha
