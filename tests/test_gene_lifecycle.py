import pytest
import hashlib
from pathlib import Path
from conftest import (
    create_valid_gene,
    create_malicious_gene,
    save_temp_gene,
    clean_test_data,
    TEST_DATA_DIR
)


def compute_sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()


def simulate_gene_lifecycle(gene_content, gene_name):
    lifecycle = {"steps": [], "success": True}

    sha = compute_sha256(gene_content)
    filepath = save_temp_gene(gene_content, sha)
    lifecycle["steps"].append({
        "step": "create",
        "gene_name": gene_name,
        "sha256": sha,
        "status": "ok"
    })

    lifecycle["steps"].append({
        "step": "validate",
        "has_life_id": "PGN@" in gene_content,
        "has_function": "def main" in gene_content,
        "status": "ok"
    })

    lifecycle["steps"].append({
        "step": "register",
        "file_path": str(filepath),
        "file_exists": filepath.exists(),
        "status": "ok"
    })

    lifecycle["steps"].append({
        "step": "ingest",
        "action": "phagocytize",
        "gene_name": gene_name,
        "content_length": len(gene_content),
        "status": "ok"
    })

    try:
        local_env = {}
        exec(gene_content, local_env)
        if "main" in local_env:
            result = local_env["main"]()
            lifecycle["steps"].append({
                "step": "execute",
                "result": result,
                "status": "ok"
            })
        else:
            lifecycle["steps"].append({
                "step": "execute",
                "error": "no main() function",
                "status": "failed"
            })
            lifecycle["success"] = False
    except Exception as e:
        lifecycle["steps"].append({
            "step": "execute",
            "error": str(e),
            "status": "failed"
        })
        lifecycle["success"] = False

    return lifecycle


class TestGeneLifecycle:
    def test_valid_gene_full_lifecycle(self):
        content = create_valid_gene("test-lifecycle")
        result = simulate_gene_lifecycle(content, "test-lifecycle")
        assert result["success"] is True
        assert len(result["steps"]) == 5
        step_names = [s["step"] for s in result["steps"]]
        assert step_names == ["create", "validate", "register", "ingest", "execute"]

    def test_gene_without_main_function(self):
        content = "# life_id: PGN@L1-G99-NO-MAIN\n# creator: Tester\n# description: Gene without main\na = 1\n"
        result = simulate_gene_lifecycle(content, "no-main")
        assert result["success"] is False
        execute_step = [s for s in result["steps"] if s["step"] == "execute"][0]
        assert execute_step["status"] == "failed"

    def test_multiple_genes_different_hashes(self):
        content1 = create_valid_gene("gene-alpha")
        content2 = create_valid_gene("gene-beta")
        h1 = compute_sha256(content1)
        h2 = compute_sha256(content2)
        assert h1 != h2

    def test_gene_validation_checks(self):
        content = create_valid_gene("valid-gene")
        assert "life_id: PGN@" in content
        assert "creator:" in content
        assert "description:" in content
        assert "def main():" in content

    def test_malicious_gene_sandbox_detection(self):
        content = create_malicious_gene()
        assert "os.system" in content
        assert "eval" in content

    def test_gene_register_file_naming(self):
        content = create_valid_gene("file-naming")
        sha = compute_sha256(content)
        filepath = save_temp_gene(content, sha)
        assert filepath.exists()
        assert filepath.name == sha
        assert len(filepath.name) == 64


def teardown_module():
    clean_test_data()
