#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import hashlib
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

GENE_DIR = Path("genes")
SIGNATURES_DIR = Path("signatures")  # optional per-gene creator signatures: signatures/<sha>.sig
INDEX_FILE = Path(".akashic_index.json")
README_FILE = Path("README.md")
SCORE_FILE = Path(".gene_score_log.json")
AUDIT_DIR = Path(os.environ.get("GATEKEEPER_AUDIT_DIR", "."))
REJECTION_LOG_FILE = AUDIT_DIR / ".gatekeeper_rejections.jsonl"
AUDIT_LOG_FILE = AUDIT_DIR / ".gatekeeper_audit.jsonl"
SECURITY_RULES_FILE = Path("policy") / "security_rules.json"

ALLOWED_LINEAGES = ["PGN@"]
ALLOWED_CREATORS = []
RATE_LIMIT_PER_PR = 5
RATE_LIMIT_PER_DAY = 20
QUALITY_GATE_STRICT = os.environ.get("GATEKEEPER_STRICT_L4", "1") == "1"
CONTENT_ADDRESS_STRICT = os.environ.get("GATEKEEPER_STRICT_L2", "1") == "1"


@dataclass
class AuditResult:
    event_type: str
    gene_file: str
    layer: str
    status: str
    reason: str
    strict: bool
    reformable: bool
    life_id: str = ""
    creator: str = "Anonymous"
    source: str = "registry_gatekeeper"
    timestamp: str = ""

    def to_record(self) -> dict:
        record = asdict(self)
        if not record["timestamp"]:
            record["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return record


def make_result(gene_file: Path, layer: str, status: str, reason: str, meta: dict, *, strict: bool, reformable: bool) -> AuditResult:
    return AuditResult(
        event_type="registry_audit",
        gene_file=gene_file.name,
        layer=layer,
        status=status,
        reason=reason,
        strict=strict,
        reformable=reformable,
        life_id=meta.get("life_id", ""),
        creator=meta.get("creator", "Anonymous"),
    )


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except PermissionError:
        fallback = Path(os.environ.get("TEMP", "/tmp")) / path.name
        with fallback.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def record_audit(result: AuditResult) -> None:
    record = result.to_record()
    append_jsonl(AUDIT_LOG_FILE, record)
    if result.status == "fail":
        append_jsonl(REJECTION_LOG_FILE, record)


def extract_yaml_header(filepath: Path) -> tuple[dict, int]:
    content = filepath.read_text(encoding="utf-8-sig", errors="ignore")
    raw_lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            raw_lines.append(stripped.lstrip("#").strip())
        elif re.match(r"^[A-Za-z_][A-Za-z0-9_]*:\s*", stripped):
            raw_lines.append(stripped)
        else:
            break

    yaml_text = "\n".join(raw_lines)
    meta = {}
    for key in ("life_id", "creator", "description"):
        m = re.search(rf'{key}:\s*"?([^"\n]+)"?', yaml_text)
        if m:
            meta[key] = m.group(1).strip()

    if "creator" not in meta:
        m = re.search(r'creator:\s*\n\s+name:\s*"([^"]+)"', content)
        if m:
            meta["creator"] = m.group(1).strip()

    return meta, len(raw_lines)


def validate_l1_lineage(meta: dict) -> tuple[bool, str]:
    life_id = meta.get("life_id", "")
    if any(life_id.startswith(prefix) for prefix in ALLOWED_LINEAGES):
        return True, life_id
    return False, f"life_id '{life_id}' must start with one of {ALLOWED_LINEAGES}"


def validate_l3_creator(meta: dict) -> tuple[bool, str]:
    creator = meta.get("creator", "").strip() or "Anonymous"
    meta["creator"] = creator
    return True, creator


def validate_l4_quality(meta: dict, filepath: Path) -> tuple[bool, str]:
    errors = []
    if len(meta.get("life_id", "")) < 5:
        errors.append("life_id too short")
    if len(meta.get("creator", "")) < 2:
        errors.append("creator too short")
    if len(meta.get("description", "")) < 10:
        errors.append("description too short")
    size = filepath.stat().st_size
    if size == 0:
        errors.append("empty file")
    if size > 1024 * 1024:
        errors.append("file exceeds 1MB")
    if errors:
        return False, "; ".join(errors)
    return True, "quality gate passed"


def load_security_rules() -> list[dict]:
    if not SECURITY_RULES_FILE.exists():
        return []
    payload = json.loads(SECURITY_RULES_FILE.read_text(encoding="utf-8-sig"))
    return payload.get("dangerous_patterns", [])


def validate_l5_security(filepath: Path) -> tuple[bool, str]:
    content = filepath.read_text(encoding="utf-8-sig", errors="ignore")
    rules = load_security_rules()
    if not rules:
        return False, "missing policy/security_rules.json"
    warnings = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for rule in rules:
            pattern = rule["pattern"]
            matched = re.search(pattern, line) is not None if rule.get("regex", False) else pattern in line
            if matched:
                warnings.append(rule["reason"])
    if warnings:
        return False, "; ".join(sorted(set(warnings)))
    return True, "security scan passed"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_l2_content_address(filepath: Path, actual_sha256: str) -> tuple[bool, str]:
    if filepath.name != actual_sha256:
        return False, f"filename {filepath.name[:16]}... != sha {actual_sha256[:16]}..."
    return True, "content-address check passed"


def load_index() -> dict:
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text(encoding="utf-8-sig"))
    return {}


def save_index(index: dict) -> None:
    tmp = INDEX_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(INDEX_FILE)


def load_score_log() -> dict:
    if SCORE_FILE.exists():
        return json.loads(SCORE_FILE.read_text(encoding="utf-8-sig"))
    return {}


def save_score_log(score_log: dict) -> None:
    SCORE_FILE.write_text(json.dumps(score_log, ensure_ascii=False, indent=2), encoding="utf-8")


def infer_capability_name(life_id: str) -> str:
    parts = life_id.split("-", 2)
    if len(parts) >= 3:
        return parts[-1].lower().replace("_", "-")
    return parts[-1].lower() if parts else "unknown"


def build_readme_table(entries: list[dict]) -> str:
    header = "| Capability | Lineage | Creator | SHA-256 | CID | Status |\n"
    header += "|------|------|------|------|------|------|\n"
    rows = []
    for e in entries:
        rows.append(
            f"| `{e['capability']}` | {e.get('life_id','N/A')} | {e.get('creator','N/A')} | "
            f"`{e.get('sha256','N/A')[:16]}...` | `{e.get('cid','N/A')[:16]}...` | Registered |"
        )
    return header + "\n".join(rows) + "\n"


def update_readme(index: dict) -> bool:
    if not README_FILE.exists():
        return False
    content = README_FILE.read_text(encoding="utf-8-sig", errors="ignore")
    entries = []
    for cap, item in index.items():
        if isinstance(item, dict):
            entries.append({"capability": cap, "life_id": item.get("life_id", ""), "creator": item.get("creator", ""), "cid": item.get("cid", ""), "sha256": item.get("expected_sha256", "")})
    entries.sort(key=lambda x: x["capability"])
    marker_start = "<!-- REGISTRY TABLE START -->"
    marker_end = "<!-- REGISTRY TABLE END -->"
    if marker_start not in content or marker_end not in content:
        return False
    new_content = content[: content.index(marker_start) + len(marker_start)] + "\n" + build_readme_table(entries) + content[content.index(marker_end) :]
    README_FILE.write_text(new_content, encoding="utf-8")
    return True


def _load_capability_module():
    """Locate the sibling protocol's capability module (single source of truth for the
    Gene Contract v2 AST allowlist). Returns the module, or None if the protocol repo is not
    checked out alongside this one (in which case L6 degrades to a skip)."""
    here = Path(__file__).resolve()
    registry_root = here.parents[2]  # .github/workflows/gatekeeper.py -> repo root
    protocol_dir = Path(os.environ.get("PROGENITOR_PROTOCOL_DIR", registry_root.parent / "progenitor-protocol"))
    hatchery = protocol_dir / "hatchery"
    if hatchery.is_dir() and str(hatchery) not in sys.path:
        sys.path.insert(0, str(hatchery))
    try:
        import capability
        return capability
    except Exception:
        return None


def validate_l6_capability_scope(gf: Path) -> tuple[bool, str]:
    """[L6] Capability honesty: a gene declaring ``purity: pure`` must actually pass the
    protocol's AST allowlist (no ambient authority). Genes that make no purity claim are
    unaffected (backward compatible). See docs/VISION.md (pillar B)."""
    cap = _load_capability_module()
    if cap is None:
        return True, "L6 skipped — sibling protocol capability module unavailable"
    content = gf.read_text(encoding="utf-8-sig", errors="ignore")
    manifest = cap.parse_capability_manifest(content)
    if manifest.get("purity") != "pure":
        return True, "no pure claim to verify (effectful default)"
    ok, reason = cap.check_pure_safe(content)
    if ok:
        return True, "declared purity: pure and passes the AST allowlist"
    return False, f"declares purity: pure but violates the allowlist — {reason}"


def _load_trust_module():
    """Load the registry's trust module (keyring verification). None if unavailable."""
    tools_dir = Path(__file__).resolve().parents[2] / "tools"
    if tools_dir.is_dir() and str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    try:
        import trust
        return trust
    except Exception:
        return None


def gene_trust_state(gf: Path, meta: dict, sha: str) -> str:
    """Determine a gene's trust_state (docs/VISION.md, pillar A).

    If a creator-signature sidecar ``signatures/<sha>.sig`` is present, verify it against the
    trust keyring and confirm it covers this exact content and matches the declared creator →
    ``creator-signed:<owner>``. A present-but-bad sidecar → ``creator-signature-invalid``.
    No sidecar → ``registry_verified`` (the gatekeeper still vouched for it)."""
    sig_path = SIGNATURES_DIR / f"{sha}.sig"
    if not sig_path.exists():
        return "registry_verified"
    trust = _load_trust_module()
    if trust is None:
        return "registry_verified"  # cannot verify here → no upgrade, no false alarm
    try:
        envelope = json.loads(sig_path.read_text(encoding="utf-8"))
        ok, info = trust.verify_signed_document(envelope)
    except Exception:
        return "creator-signature-invalid"
    if not ok:
        return "creator-signature-invalid"
    if envelope.get("content_sha256") != sha:
        return "creator-signature-invalid"
    declared = meta.get("creator")
    if declared and info.get("owner") and declared != info.get("owner"):
        return "creator-signature-invalid"
    return f"creator-signed:{info.get('owner')}"


def audit_gene(gf: Path, creator_counts: dict) -> tuple[bool, dict, str]:
    meta, _ = extract_yaml_header(gf)
    creator = meta.get("creator", "Anonymous")
    creator_counts[creator] = creator_counts.get(creator, 0) + 1

    passed_l1, msg_l1 = validate_l1_lineage(meta)
    result = make_result(gf, "L1", "pass" if passed_l1 else "fail", msg_l1, meta, strict=True, reformable=True)
    record_audit(result)
    if not passed_l1:
        return False, meta, ""

    sha = compute_sha256(gf)
    passed_l2, msg_l2 = validate_l2_content_address(gf, sha)
    status_l2 = "pass" if passed_l2 else ("fail" if CONTENT_ADDRESS_STRICT else "warn")
    result = make_result(gf, "L2", status_l2, msg_l2, meta, strict=CONTENT_ADDRESS_STRICT, reformable=False)
    record_audit(result)
    if status_l2 == "fail":
        return False, meta, sha

    passed_l3, msg_l3 = validate_l3_creator(meta)
    result = make_result(gf, "L3", "pass" if passed_l3 else "fail", msg_l3, meta, strict=True, reformable=True)
    record_audit(result)
    if not passed_l3:
        return False, meta, sha

    passed_l4, msg_l4 = validate_l4_quality(meta, gf)
    status_l4 = "pass" if passed_l4 else ("fail" if QUALITY_GATE_STRICT else "warn")
    result = make_result(gf, "L4", status_l4, msg_l4, meta, strict=QUALITY_GATE_STRICT, reformable=True)
    record_audit(result)
    if status_l4 == "fail":
        return False, meta, sha

    passed_l5, msg_l5 = validate_l5_security(gf)
    result = make_result(gf, "L5", "pass" if passed_l5 else "fail", msg_l5, meta, strict=True, reformable=False)
    record_audit(result)
    if not passed_l5:
        return False, meta, sha

    passed_l6, msg_l6 = validate_l6_capability_scope(gf)
    result = make_result(gf, "L6", "pass" if passed_l6 else "fail", msg_l6, meta, strict=True, reformable=True)
    record_audit(result)
    if not passed_l6:
        return False, meta, sha

    return True, meta, sha


def main() -> int:
    parser = argparse.ArgumentParser(description="Progenitor Registry Gatekeeper")
    parser.add_argument("--scan-only", action="store_true", help="Only scan and validate")
    args = parser.parse_args()

    if not GENE_DIR.exists():
        print("genes/ not found, skip")
        return 0
    gene_files = [p for p in GENE_DIR.iterdir() if p.is_file()]
    if not gene_files:
        print("genes/ empty, skip")
        return 0
    if len(gene_files) > RATE_LIMIT_PER_PR:
        print(f"L0 failed: PR has {len(gene_files)} genes > {RATE_LIMIT_PER_PR}")
        return 1

    index = load_index()
    score_log = load_score_log()
    new_entries = {}
    all_passed = True
    creator_counts = {}

    for gf in gene_files:
        passed, meta, sha = audit_gene(gf, creator_counts)
        if not passed:
            all_passed = False
            continue
        cap_name = infer_capability_name(meta.get("life_id", gf.name))
        creator = meta.get("creator", "Anonymous")
        if cap_name in index and isinstance(index[cap_name], dict) and index[cap_name].get("creator") != creator:
            cap_name = f"{cap_name}-{creator.lower().replace(' ', '-')[:10]}"
        new_entries[cap_name] = {
            "schema_version": "akashic.index/v2",
            "capability": cap_name,
            "cid": sha,
            "content_sha256": sha,
            "expected_sha256": sha,
            "registry_path": f"genes/{sha}",
            "transport_hints": [
                {"type": "registry_path", "url": f"genes/{sha}", "priority": 10},
                {"type": "github_raw", "url": f"https://raw.githubusercontent.com/Audrey-cn/progenitor-registry/main/genes/{sha}", "priority": 70},
            ],
            "trust_state": gene_trust_state(gf, meta, sha),
            "life_id": meta.get("life_id", ""),
            "creator": creator,
            "description": meta.get("description", ""),
            "registered_at": time.strftime("%Y-%m-%d"),
            "initial_score": 0,
        }

    for creator, count in creator_counts.items():
        if count > RATE_LIMIT_PER_DAY:
            print(f"L0 failed: creator {creator} submitted {count} > {RATE_LIMIT_PER_DAY}")
            return 1

    if args.scan_only:
        print("scan-only mode: validation complete, skip index/readme/score updates")
        return 0 if all_passed else 1
    if not new_entries:
        return 0 if all_passed else 1

    index.update(new_entries)
    save_index(index)
    update_readme(index)
    for cap_name in new_entries:
        if cap_name not in score_log:
            score_log[cap_name] = {"score": 0, "downloads": 0, "reports": 0, "created_at": time.strftime("%Y-%m-%d"), "last_updated": time.strftime("%Y-%m-%d")}
    save_score_log(score_log)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
