"""Exercise the real rejection_report tool against synthetic jsonl logs."""
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR / "tools"))
import rejection_report as rr  # noqa: E402


def _write_jsonl(path: Path, rows: list[dict], torn_tail: bool = False) -> None:
    lines = [__import__("json").dumps(r) for r in rows]
    if torn_tail:
        lines.append('{"truncated": ')  # a torn last line must be skipped, not fatal
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")


def test_empty_logs_report_clean(tmp_path):
    report = rr.build_report([], [], top=5, recent=10)
    assert "No rejections recorded" in report


def test_layer_counts_and_reason_grouping(tmp_path):
    rej_path = tmp_path / "rej.jsonl"
    rows = [
        {"layer": "L2", "status": "fail", "reason": "filename does not match sha256: a vs b",
         "gene_file": "aaa", "creator": "Eve", "timestamp": "2026-09-20T03:00:00Z"},
        {"layer": "L2", "status": "fail", "reason": "filename does not match sha256: c vs d",
         "gene_file": "bbb", "creator": "Eve", "timestamp": "2026-09-21T03:00:00Z"},
        {"layer": "L5", "status": "fail", "reason": "dangerous call: os.system",
         "gene_file": "ccc", "creator": "Mal", "timestamp": "2026-09-22T03:00:00Z"},
    ]
    _write_jsonl(rej_path, rows)
    rejections = rr.load_jsonl(rej_path)
    report = rr.build_report(rejections, [], top=5, recent=10)
    assert "| L2 | 2 |" in report
    assert "| L5 | 1 |" in report
    assert "filename does not match sha256" in report  # grouped, variable tails stripped
    assert report.index("filename does not match") < report.index("dangerous call")  # top-1 first
    assert report.index("bbb") < report.index("aaa")  # recent table: newest first


def test_torn_last_line_is_skipped(tmp_path):
    rej_path = tmp_path / "rej.jsonl"
    _write_jsonl(rej_path, [{"layer": "L1", "status": "fail", "reason": "boom",
                             "gene_file": "x", "creator": "a", "timestamp": "t"}], torn_tail=True)
    records = rr.load_jsonl(rej_path)
    assert len(records) == 1  # the valid record survived; the torn line was dropped
