"""Gatekeeper tests against the REAL .github/workflows/gatekeeper.py.

Previously this file re-implemented its own validate_l* helpers and never imported
gatekeeper.py, so the CI validator itself was untested. It now imports the real module
and exercises its actual validators (L1 lineage, L3 creator, L4 quality, L5 security via
policy/security_rules.json, L2 content-address, sha256, capability inference).
"""
import hashlib
import sys
from pathlib import Path

import pytest

from conftest import (
    create_valid_gene,
    create_malicious_gene,
    create_invalid_lineage_gene,
    create_third_party_import_gene,
    save_temp_gene,
    clean_test_data,
)

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR / ".github" / "workflows"))

import gatekeeper  # the REAL registry gatekeeper


@pytest.fixture(autouse=True)
def _use_real_security_rules(monkeypatch):
    # validate_l5_security() reads policy/security_rules.json relative to cwd;
    # pin it to the real file so the test works from any working directory.
    monkeypatch.setattr(gatekeeper, "SECURITY_RULES_FILE", REPO_DIR / "policy" / "security_rules.json")


class TestGatekeeperL1Lineage:
    def test_valid_lineage(self):
        meta, _ = gatekeeper.extract_yaml_header(save_temp_gene(create_valid_gene("test-gene")))
        ok, _ = gatekeeper.validate_l1_lineage(meta)
        assert ok is True

    def test_invalid_lineage(self):
        meta, _ = gatekeeper.extract_yaml_header(save_temp_gene(create_invalid_lineage_gene()))
        ok, reason = gatekeeper.validate_l1_lineage(meta)
        assert ok is False
        assert "PGN@" in reason

    def test_missing_life_id(self):
        ok, _ = gatekeeper.validate_l1_lineage({})
        assert ok is False


class TestGatekeeperL3Creator:
    def test_creator_provided(self):
        meta, _ = gatekeeper.extract_yaml_header(save_temp_gene(create_valid_gene("g", creator="Audrey")))
        ok, creator = gatekeeper.validate_l3_creator(meta)
        assert ok is True and creator == "Audrey"

    def test_creator_missing_gets_anonymous(self):
        ok, creator = gatekeeper.validate_l3_creator({"life_id": "PGN@L1-G99-TEST"})
        assert ok is True and creator == "Anonymous"


class TestGatekeeperL4Quality:
    def test_valid_gene_quality(self):
        gf = save_temp_gene(create_valid_gene("g", description="A very good test gene description"))
        meta, _ = gatekeeper.extract_yaml_header(gf)
        ok, _ = gatekeeper.validate_l4_quality(meta, gf)
        assert ok is True

    def test_short_description(self):
        gf = save_temp_gene(create_valid_gene("g", description="short"))
        meta, _ = gatekeeper.extract_yaml_header(gf)
        ok, reason = gatekeeper.validate_l4_quality(meta, gf)
        assert ok is False and "description" in reason

    def test_short_creator(self):
        gf = save_temp_gene(create_valid_gene("g", creator="X"))
        meta, _ = gatekeeper.extract_yaml_header(gf)
        ok, reason = gatekeeper.validate_l4_quality(meta, gf)
        assert ok is False and "creator" in reason


class TestGatekeeperL5Security:
    def test_clean_gene_passes(self):
        ok, _ = gatekeeper.validate_l5_security(save_temp_gene(create_valid_gene("clean-gene")))
        assert ok is True

    def test_malicious_gene_blocked(self):
        ok, reason = gatekeeper.validate_l5_security(save_temp_gene(create_malicious_gene()))
        assert ok is False and reason

    def test_third_party_import_blocked(self):
        ok, _ = gatekeeper.validate_l5_security(save_temp_gene(create_third_party_import_gene()))
        assert ok is False

    def test_missing_rules_fails_closed(self, monkeypatch, tmp_path):
        monkeypatch.setattr(gatekeeper, "SECURITY_RULES_FILE", tmp_path / "absent.json")
        ok, reason = gatekeeper.validate_l5_security(save_temp_gene(create_valid_gene("x")))
        assert ok is False and "missing" in reason


class TestGatekeeperL2ContentAddress:
    def test_filename_matches_sha(self, tmp_path):
        content = create_valid_gene("hash-gene")
        sha = hashlib.sha256(content.encode()).hexdigest()
        gf = tmp_path / sha
        gf.write_text(content, encoding="utf-8")
        assert gatekeeper.compute_sha256(gf) == sha
        ok, _ = gatekeeper.validate_l2_content_address(gf, sha)
        assert ok is True

    def test_filename_mismatch_rejected(self, tmp_path):
        gf = tmp_path / "not-a-content-hash"
        gf.write_text("data", encoding="utf-8")
        ok, _ = gatekeeper.validate_l2_content_address(gf, gatekeeper.compute_sha256(gf))
        assert ok is False


class TestGatekeeperHelpers:
    def test_infer_capability_name(self):
        assert gatekeeper.infer_capability_name("PGN@L1-G3-CODE-REVIEWER") == "code-reviewer"

    def test_extract_yaml_header_parses_fields(self):
        gf = save_temp_gene(create_valid_gene("parsed", creator="Audrey", description="parses header fields ok"))
        meta, _ = gatekeeper.extract_yaml_header(gf)
        assert meta["life_id"].startswith("PGN@")
        assert meta["creator"] == "Audrey"
        assert len(meta["description"]) >= 10


class TestGatekeeperL6CapabilityScope:
    def test_no_purity_claim_is_unaffected(self):
        # backward compatible: genes that make no purity claim pass L6
        gf = save_temp_gene(create_valid_gene("plain-gene"), name="l6-plain")
        ok, _ = gatekeeper.validate_l6_capability_scope(gf)
        assert ok is True

    def test_honest_pure_gene_passes(self):
        if gatekeeper._load_capability_module() is None:
            pytest.skip("sibling protocol capability module not available")
        content = (
            "# life_id: PGN@L1-G99-PURE-DOUBLER\n"
            "# creator: TestCreator\n"
            "# description: an honest pure gene\n"
            "# purity: pure\n\n"
            "def main(x):\n    return {'doubled': x * 2}\n"
        )
        gf = save_temp_gene(content, name="l6-honest-pure")
        ok, reason = gatekeeper.validate_l6_capability_scope(gf)
        assert ok is True, reason

    def test_dishonest_pure_gene_rejected(self):
        if gatekeeper._load_capability_module() is None:
            pytest.skip("sibling protocol capability module not available")
        content = (
            "# life_id: PGN@L1-G99-FAKE-PURE\n"
            "# creator: Attacker\n"
            "# description: claims pure but reads the filesystem\n"
            "# purity: pure\n\n"
            "import os\n"
            "def main():\n    return os.getcwd()\n"
        )
        gf = save_temp_gene(content, name="l6-fake-pure")
        ok, reason = gatekeeper.validate_l6_capability_scope(gf)
        assert ok is False
        assert "allowlist" in reason


def teardown_module():
    clean_test_data()
