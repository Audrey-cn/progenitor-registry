#!/usr/bin/env python3
"""Rejection analytics for the Gatekeeper daily scan.

Reads `.gatekeeper_rejections.jsonl` (every record) and `.gatekeeper_audit.jsonl`
(pass/fail mix) and prints a markdown summary: totals, per-layer failure counts,
top failure reasons, and the most recent rejections. Stdlib only; informational —
always exits 0 so a report hiccup never fails the scan.

Exit criteria owner: NEXT_PHASE_PLAN to-do #4 (summary shows top rejection reasons by layer).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

LAYER_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # a torn last line must not kill the report
    return records


def _short(value: str | None, width: int = 12) -> str:
    value = value or "—"
    return value if len(value) <= width else value[: width - 1] + "…"


def build_report(rejections: list[dict], audit: list[dict], *, top: int, recent: int) -> str:
    lines: list[str] = []
    fails = [r for r in rejections if r.get("status") == "fail"]
    lines.append("## Gatekeeper rejection analytics")
    lines.append("")
    if audit:
        passes = sum(1 for r in audit if r.get("status") == "pass")
        warns = sum(1 for r in audit if r.get("status") == "warn")
        lines.append(
            f"- Audit events: **{len(audit)}** (pass {passes} · fail {len(fails)} · warn {warns})"
        )
    else:
        lines.append(f"- Rejections on record: **{len(fails)}**")
    if not fails:
        lines.append("")
        lines.append("No rejections recorded — all layers clean. 🟢")
        return "\n".join(lines)

    # Per-layer failure counts.
    by_layer = Counter(r.get("layer", "?") for r in fails)
    lines.append("")
    lines.append("| Layer | Failures |")
    lines.append("|---|---|")
    for layer in sorted(by_layer, key=lambda l: (LAYER_ORDER.index(l) if l in LAYER_ORDER else 99, l)):
        lines.append(f"| {layer} | {by_layer[layer]} |")

    # Top failure reasons (normalized: strip the variable tail after ':' / '(' to group).
    def normalize(reason: str) -> str:
        for sep in (":", "("):
            if sep in reason:
                reason = reason.split(sep, 1)[0]
        return reason.strip() or "(no reason)"

    by_reason = Counter(normalize(str(r.get("reason", ""))) for r in fails)
    lines.append("")
    lines.append(f"Top rejection reasons (top {min(top, len(by_reason))}):")
    lines.append("")
    lines.append("| Reason (normalized) | Count |")
    lines.append("|---|---|")
    for reason, count in by_reason.most_common(top):
        lines.append(f"| {_short(reason, 60)} | {count} |")

    # Recent rejections.
    def sort_key(r: dict) -> str:
        return str(r.get("timestamp") or "")

    lines.append("")
    lines.append(f"Most recent rejections (last {min(recent, len(fails))}):")
    lines.append("")
    lines.append("| Timestamp | Gene | Layer | Reason | Creator |")
    lines.append("|---|---|---|---|---|")
    for r in sorted(fails, key=sort_key)[-recent:][::-1]:
        lines.append(
            "| {ts} | `{gene}` | {layer} | {reason} | {creator} |".format(
                ts=_short(r.get("timestamp"), 19),
                gene=_short(r.get("gene_file"), 14),
                layer=r.get("layer", "?"),
                reason=_short(str(r.get("reason", "")), 40),
                creator=_short(r.get("creator"), 16),
            )
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rejections", default=".gatekeeper_rejections.jsonl")
    parser.add_argument("--audit", default=".gatekeeper_audit.jsonl")
    parser.add_argument("--top", type=int, default=5, help="how many top reasons to show")
    parser.add_argument("--recent", type=int, default=10, help="how many recent rejections to show")
    args = parser.parse_args()

    rejections = load_jsonl(Path(args.rejections))
    audit = load_jsonl(Path(args.audit))
    print(build_report(rejections, audit, top=args.top, recent=args.recent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
