import json
import hashlib
import re
import sys
from pathlib import Path

from repo_paths import REGISTRY_DIR


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


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


def load_security_rules():
    rules_file = REGISTRY_DIR / "policy" / "security_rules.json"
    payload = json.loads(rules_file.read_text(encoding="utf-8-sig"))
    return payload.get("dangerous_patterns", [])


def has_non_comment_match(content, rule):
    pattern = rule["pattern"]
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if rule.get("regex", False):
            if re.search(pattern, line):
                return line.strip()[:80], rule["reason"]
        elif pattern in line:
            return line.strip()[:80], rule["reason"]
    return None, None


def crucible_check(gene_dir=None):
    if gene_dir is None:
        gene_dir = REGISTRY_DIR / "genes"

    if not gene_dir or not Path(gene_dir).exists():
        print(f"gene directory not found: {gene_dir}")
        return 1

    gene_dir = Path(gene_dir)
    rules = load_security_rules()
    results = {"passed": [], "failed": [], "warnings": [], "total": 0}

    for f in sorted(gene_dir.iterdir()):
        if not f.is_file() or len(f.name) != 64:
            continue

        results["total"] += 1
        gene_ok = True

        try:
            content = f.read_text(encoding="utf-8-sig")
        except Exception as e:
            results["failed"].append((f.name, f"read failed: {e}"))
            continue

        meta = extract_yaml_header(content)

        if not meta.get("life_id", "").startswith("PGN@"):
            results["failed"].append((f.name, "invalid life_id: must start with PGN@"))
            gene_ok = False

        if len(meta.get("description", "")) < 10:
            results["warnings"].append((f.name, f"description too short: {len(meta.get('description', ''))}"))

        actual_sha = compute_sha256(f)
        if actual_sha != f.name:
            results["failed"].append((f.name, f"SHA-256 mismatch: name={f.name[:12]} actual={actual_sha[:12]}"))
            gene_ok = False

        if len(content.encode()) > 1024 * 1024:
            results["failed"].append((f.name, "file exceeds 1MB"))
            gene_ok = False

        for rule in rules:
            hit_line, reason = has_non_comment_match(content, rule)
            if hit_line:
                results["failed"].append((f.name, f"security violation: {reason} -> {hit_line}"))
                gene_ok = False
                break

        if gene_ok:
            results["passed"].append(f.name)

    print("=" * 60)
    print("  Crucible precheck")
    print("=" * 60)
    print(f"  scan dir: {gene_dir}")
    print(f"  total: {results['total']}")
    print(f"  passed: {len(results['passed'])}")
    print(f"  failed: {len(results['failed'])}")
    print(f"  warnings: {len(results['warnings'])}")

    if results["failed"]:
        print("\n-- failed --")
        for name, reason in results["failed"]:
            print(f"  X {name[:12]}... : {reason}")

    if results["warnings"]:
        print("\n-- warnings --")
        for name, reason in results["warnings"]:
            print(f"  ! {name[:12]}... : {reason}")

    if results["passed"]:
        print("\n-- passed --")
        for name in results["passed"]:
            print(f"  OK {name[:12]}...")

    return 1 if results["failed"] else 0


def main():
    gene_dir = None
    for arg in sys.argv[1:]:
        if arg.startswith("--gene-dir="):
            gene_dir = arg.split("=", 1)[1]

    sys.exit(crucible_check(gene_dir))


if __name__ == "__main__":
    main()

