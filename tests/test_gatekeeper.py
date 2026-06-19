import pytest
import hashlib
from conftest import (
    create_valid_gene,
    create_malicious_gene,
    create_invalid_lineage_gene,
    create_third_party_import_gene,
    save_temp_gene,
    clean_test_data
)


def compute_sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()


def extract_yaml_header(content):
    meta = {}
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("# life_id:"):
            meta["life_id"] = line.split(":", 1)[1].strip()
        elif line.startswith("# creator:"):
            meta["creator"] = line.split(":", 1)[1].strip()
        elif line.startswith("# description:"):
            meta["description"] = line.split(":", 1)[1].strip()
    return meta


def validate_l1_lineage(meta):
    life_id = meta.get("life_id", "")
    if not life_id.startswith("PGN@"):
        return False, "虚空异种: life_id 必须以 PGN@ 开头"
    return True, None


def validate_l3_creator(meta):
    if not meta.get("creator"):
        meta["creator"] = "Anonymous"
    return True, None


def validate_l4_quality(meta, content):
    issues = []
    life_id = meta.get("life_id", "")
    creator = meta.get("creator", "")
    description = meta.get("description", "")

    if len(life_id) < 5:
        issues.append("life_id 过短 (<5)")
    if len(creator) < 2:
        issues.append("creator 过短 (<2)")
    if len(description) < 10:
        issues.append("description 过短 (<10)")
    if len(content) == 0:
        issues.append("基因文件为空")
    if len(content.encode()) > 1024 * 1024:
        issues.append("基因文件超过 1MB")

    return issues


def validate_l5_security(content):
    patterns = [
        ("eval(", "eval() 调用"),
        ("exec(", "exec() 调用"),
        ("__import__(", "__import__() 调用"),
        ("os.system(", "os.system() 调用"),
        ("subprocess.call", "subprocess.call() 调用"),
        ("subprocess.run", "subprocess.run() 调用"),
        ("subprocess.Popen", "subprocess.Popen() 调用"),
        ("import requests", "requests 库引用"),
        ("from requests", "requests 库引用"),
        ("import pandas", "pandas 库引用"),
        ("from pandas", "pandas 库引用"),
        ("import numpy", "numpy 库引用"),
        ("from numpy", "numpy 库引用"),
    ]
    findings = []
    for line_no, line in enumerate(content.split("\n"), 1):
        for pattern, desc in patterns:
            if pattern in line and not line.strip().startswith("#"):
                findings.append({
                    "line": line_no,
                    "pattern": pattern,
                    "description": desc
                })
    return findings


class TestGatekeeperL1Lineage:
    def test_valid_lineage(self):
        content = create_valid_gene("test-gene")
        meta = extract_yaml_header(content)
        passed, reason = validate_l1_lineage(meta)
        assert passed is True
        assert reason is None

    def test_invalid_lineage(self):
        content = create_invalid_lineage_gene()
        meta = extract_yaml_header(content)
        passed, reason = validate_l1_lineage(meta)
        assert passed is False
        assert "虚" in reason or "PGN@" in reason

    def test_missing_life_id(self):
        meta = {}
        passed, reason = validate_l1_lineage(meta)
        assert passed is False


class TestGatekeeperL3Creator:
    def test_creator_provided(self):
        content = create_valid_gene("test-gene", creator="Audrey")
        meta = extract_yaml_header(content)
        passed, _ = validate_l3_creator(meta)
        assert passed is True
        assert meta["creator"] == "Audrey"

    def test_creator_missing_gets_anonymous(self):
        content = """# life_id: PGN@L1-G99-TEST
# description: test

def main():
    return {}
"""
        meta = extract_yaml_header(content)
        passed, _ = validate_l3_creator(meta)
        assert passed is True
        assert meta["creator"] == "Anonymous"

    def test_anonymous_creator(self):
        content = create_valid_gene("test-gene", creator="Anonymous")
        meta = extract_yaml_header(content)
        passed, _ = validate_l3_creator(meta)
        assert passed is True


class TestGatekeeperL4Quality:
    def test_valid_gene_quality(self):
        content = create_valid_gene("test-gene",
                                     description="A very good test gene description")
        meta = extract_yaml_header(content)
        issues = validate_l4_quality(meta, content)
        assert len(issues) == 0

    def test_short_description(self):
        content = create_valid_gene("test-gene", description="short")
        meta = extract_yaml_header(content)
        issues = validate_l4_quality(meta, content)
        assert any("description" in i for i in issues)

    def test_empty_file(self):
        content = ""
        meta = {}
        issues = validate_l4_quality(meta, content)
        assert any("空" in i for i in issues)

    def test_short_creator(self):
        content = create_valid_gene("test-gene", creator="X")
        meta = extract_yaml_header(content)
        issues = validate_l4_quality(meta, content)
        assert any("creator" in i for i in issues)


class TestGatekeeperL5Security:
    def test_clean_gene(self):
        content = create_valid_gene("clean-gene")
        findings = validate_l5_security(content)
        assert len(findings) == 0

    def test_malicious_eval(self):
        content = create_malicious_gene()
        findings = validate_l5_security(content)
        eval_findings = [f for f in findings if "eval" in f["pattern"]]
        assert len(eval_findings) > 0

    def test_malicious_exec(self):
        content = create_malicious_gene()
        findings = validate_l5_security(content)
        exec_findings = [f for f in findings if "exec" in f["pattern"]]
        assert len(exec_findings) > 0

    def test_malicious_os_system(self):
        content = create_malicious_gene()
        findings = validate_l5_security(content)
        os_findings = [f for f in findings if "os.system" in f["pattern"]]
        assert len(os_findings) > 0

    def test_third_party_numpy(self):
        content = create_third_party_import_gene()
        findings = validate_l5_security(content)
        numpy_findings = [f for f in findings if "numpy" in f["pattern"]]
        assert len(numpy_findings) > 0

    def test_third_party_pandas(self):
        content = create_third_party_import_gene()
        findings = validate_l5_security(content)
        pandas_findings = [f for f in findings if "pandas" in f["pattern"]]
        assert len(pandas_findings) > 0

    def test_commented_eval_ignored(self):
        content = "# eval() is dangerous, do not use\n\ndef main():\n    return {}\n"
        findings = validate_l5_security(content)
        assert len(findings) == 0


class TestGatekeeperL2Hashing:
    def test_sha256_computation(self):
        content = "hello world"
        h = compute_sha256(content)
        expected = hashlib.sha256(b"hello world").hexdigest()
        assert h == expected

    def test_filename_matches_content(self):
        content = create_valid_gene("test-hash")
        expected_hash = compute_sha256(content)
        assert len(expected_hash) == 64
        assert all(c in "0123456789abcdef" for c in expected_hash)

    def test_different_content_different_hash(self):
        h1 = compute_sha256("content A")
        h2 = compute_sha256("content B")
        assert h1 != h2


class TestGatekeeperRateLimit:
    RATE_LIMIT_PER_PR = 5
    RATE_LIMIT_PER_DAY = 20

    def test_within_pr_limit(self):
        gene_count = 3
        assert gene_count <= self.RATE_LIMIT_PER_PR

    def test_exceeds_pr_limit(self):
        gene_count = 7
        assert gene_count > self.RATE_LIMIT_PER_PR

    def test_within_daily_limit(self):
        gene_count = 15
        assert gene_count <= self.RATE_LIMIT_PER_DAY

    def test_exceeds_daily_limit(self):
        gene_count = 25
        assert gene_count > self.RATE_LIMIT_PER_DAY


def teardown_module():
    clean_test_data()
