"""trust_report surfaces the web-of-trust over the real registry index (Iteration 2)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import trust_report  # noqa: E402


def test_real_index_is_trusted_and_intact():
    report = trust_report.build_report()
    assert report["signature"]["trusted"] is True
    assert report["signature"]["signed_by"]["owner"] == "Audrey"
    assert report["signature"]["hash_intact"] is True
    assert len(report["genes"]) >= 1
    g = report["genes"][0]
    for field in ("capability", "creator", "content_sha256", "trust_state", "reputation"):
        assert field in g


def test_untrusted_when_keyring_excludes_signer():
    # an empty keyring trusts no one → the index signature cannot be trusted
    report = trust_report.build_report(keyring=[])
    assert report["signature"]["trusted"] is False
    assert report["signature"]["reason"]


def test_missing_index_is_handled(tmp_path):
    report = trust_report.build_report(index_file=tmp_path / "absent.json", sig_file=tmp_path / "absent.sig")
    assert report["index_present"] is False
    assert report["signature"]["trusted"] is False
