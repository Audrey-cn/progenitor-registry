"""Gene-lifecycle tests against the REAL gatekeeper.audit_gene pipeline.

Previously this file simulated a fake lifecycle and exec()'d gene strings locally. It now
runs the real L1→L5 audit_gene() from .github/workflows/gatekeeper.py on real gene files
(named by their content hash, as the registry requires).
"""
import hashlib
import sys
from pathlib import Path

import pytest

from conftest import (
    create_valid_gene,
    create_malicious_gene,
    create_invalid_lineage_gene,
    clean_test_data,
)

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR / ".github" / "workflows"))

import gatekeeper


@pytest.fixture(autouse=True)
def _isolate_gatekeeper(monkeypatch, tmp_path):
    monkeypatch.setattr(gatekeeper, "SECURITY_RULES_FILE", REPO_DIR / "policy" / "security_rules.json")
    monkeypatch.setattr(gatekeeper, "AUDIT_LOG_FILE", tmp_path / "audit.jsonl")
    monkeypatch.setattr(gatekeeper, "REJECTION_LOG_FILE", tmp_path / "rejections.jsonl")


def _gene_named_by_hash(tmp_path: Path, content: str) -> Path:
    sha = hashlib.sha256(content.encode()).hexdigest()
    gf = tmp_path / sha
    gf.write_text(content, encoding="utf-8")
    return gf


def test_valid_gene_passes_full_pipeline(tmp_path):
    content = create_valid_gene("lifecycle", description="A clearly long enough description")
    passed, meta, sha = gatekeeper.audit_gene(_gene_named_by_hash(tmp_path, content), {})
    assert passed is True
    assert meta["life_id"].startswith("PGN@")
    assert len(sha) == 64


def test_malicious_gene_rejected(tmp_path):
    passed, _, _ = gatekeeper.audit_gene(_gene_named_by_hash(tmp_path, create_malicious_gene()), {})
    assert passed is False  # L5 security


def test_invalid_lineage_rejected(tmp_path):
    passed, _, _ = gatekeeper.audit_gene(_gene_named_by_hash(tmp_path, create_invalid_lineage_gene()), {})
    assert passed is False  # L1 lineage


def test_content_address_mismatch_rejected(tmp_path):
    content = create_valid_gene("mismatch", description="A clearly long enough description")
    gf = tmp_path / "wrong-filename"  # NOT named by its sha
    gf.write_text(content, encoding="utf-8")
    passed, _, _ = gatekeeper.audit_gene(gf, {})
    assert passed is False  # L2 content-address (strict by default)


def test_short_description_rejected(tmp_path):
    content = create_valid_gene("shortdesc", description="short")
    passed, _, _ = gatekeeper.audit_gene(_gene_named_by_hash(tmp_path, content), {})
    assert passed is False  # L4 quality


def teardown_module():
    clean_test_data()
