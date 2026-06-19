import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from repo_paths import GIT_DIR, REGISTRY_DIR, REPORT_DIR


DEFAULT_AUDIT_DIR = REPORT_DIR / "gatekeeper_audit"
DEFAULT_OUTPUT_JSON = REPORT_DIR / "registry_audit_report.json"
DEFAULT_OUTPUT_MD = REPORT_DIR / "registry_audit_report.md"


def iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {
                    "event_type": "invalid_jsonl",
                    "file": str(path),
                    "line": line_no,
                    "message": line[:200],
                }


def load_records(audit_dir: Path):
    audit_records = list(iter_jsonl(audit_dir / ".gatekeeper_audit.jsonl") or [])
    rejection_records = list(iter_jsonl(audit_dir / ".gatekeeper_rejections.jsonl") or [])
    return audit_records, rejection_records


def summarize(audit_records, rejection_records):
    layer_counts = Counter(record.get("layer", "unknown") for record in audit_records)
    status_counts = Counter(record.get("status", "unknown") for record in audit_records)
    rejection_layers = Counter(record.get("layer", "unknown") for record in rejection_records)
    rejection_files = Counter(record.get("file", "unknown") for record in rejection_records)
    reformable = sum(1 for record in rejection_records if record.get("reformable"))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_events": len(audit_records),
        "rejections": len(rejection_records),
        "reformable_rejections": reformable,
        "status_counts": dict(status_counts),
        "layer_counts": dict(layer_counts),
        "rejection_layers": dict(rejection_layers),
        "top_rejected_files": dict(rejection_files.most_common(10)),
        "recent_rejections": rejection_records[-10:],
    }


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, summary: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Registry Audit Report",
        "",
        f"- Generated: `{summary['generated_at']}`",
        f"- Audit events: `{summary['audit_events']}`",
        f"- Rejections: `{summary['rejections']}`",
        f"- Reformable rejections: `{summary['reformable_rejections']}`",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(summary["status_counts"].items()):
        lines.append(f"- `{status}`: {count}")

    lines.extend(["", "## Layer Counts", ""])
    for layer, count in sorted(summary["layer_counts"].items()):
        lines.append(f"- `{layer}`: {count}")

    lines.extend(["", "## Rejection Layers", ""])
    if summary["rejection_layers"]:
        for layer, count in sorted(summary["rejection_layers"].items()):
            lines.append(f"- `{layer}`: {count}")
    else:
        lines.append("- No rejections recorded.")

    lines.extend(["", "## Recent Rejections", ""])
    if summary["recent_rejections"]:
        for record in summary["recent_rejections"]:
            lines.append(
                f"- `{record.get('layer', 'unknown')}` `{record.get('status', 'unknown')}` "
                f"`{record.get('file', 'unknown')}` - {record.get('message', '')}"
            )
    else:
        lines.append("- No recent rejection records.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Summarize Gatekeeper audit and rejection JSONL logs.")
    parser.add_argument("--audit-dir", default=str(DEFAULT_AUDIT_DIR), help="Directory containing Gatekeeper JSONL logs.")
    parser.add_argument("--json", default=str(DEFAULT_OUTPUT_JSON), help="Output JSON report path.")
    parser.add_argument("--markdown", default=str(DEFAULT_OUTPUT_MD), help="Output Markdown report path.")
    args = parser.parse_args()

    audit_dir = Path(args.audit_dir).resolve()
    audit_records, rejection_records = load_records(audit_dir)
    summary = summarize(audit_records, rejection_records)

    write_json(Path(args.json), summary)
    write_markdown(Path(args.markdown), summary)

    print("=" * 60)
    print("  Registry Audit Report")
    print("=" * 60)
    print(f"  registry: {REGISTRY_DIR}")
    print(f"  audit dir: {audit_dir}")
    print(f"  audit events: {summary['audit_events']}")
    print(f"  rejections: {summary['rejections']}")
    print(f"  json: {Path(args.json).resolve()}")
    print(f"  markdown: {Path(args.markdown).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
