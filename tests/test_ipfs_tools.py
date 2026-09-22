"""IPFS tooling pure-logic tests (no daemon required)."""
import json
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR / "tools"))
import ipfs_upload  # noqa: E402
import ipfs_pull  # noqa: E402

CID = "bafkreic2oavsjmmzwionmexgeiobwwcfby52kbgifwzpqzxqk4uyygalkq"
SHA = "5a702b24b199b21cd612e6221c1b58450e3ba504c82db2f866f057298c180b54"


def test_verify_upload_cid_sha_cross_check(tmp_path):
    real_gene = REPO_DIR / "genes" / SHA
    assert ipfs_upload.verify_upload(CID, real_gene) is True
    tampered = tmp_path / "tampered"
    tampered.write_bytes(b"tampered bytes")
    assert ipfs_upload.verify_upload(CID, tampered) is False


def test_gateway_url_shapes():
    urls = ipfs_upload.get_gateway_url(CID)
    assert urls[0] == f"https://ipfs.io/ipfs/{CID}"
    assert all(u.endswith(CID) for u in urls)
    single = ipfs_upload.get_gateway_url(CID, gateway="https://example.com")
    assert single == f"https://example.com/ipfs/{CID}"


def test_index_update_attaches_hint_without_overwriting(tmp_path):
    idx = tmp_path / ".akashic_index.json"
    entry = {
        "life_id": "PGN@L1-G1-X",
        "creator": "Audrey",
        "content_sha256": SHA,
        "cid": SHA,
        "transport_hints": [{"type": "github_raw", "url": "https://x", "priority": 70}],
        "trust_state": "registry_verified",
    }
    idx.write_text(json.dumps({"whatever": entry, "__anchor": {"keep": 1}}), encoding="utf-8", newline="")
    ok = ipfs_upload.update_akashic_index("whatever", CID, SHA, 455, index_file=idx)
    assert ok is True
    data = json.loads(idx.read_text(encoding="utf-8"))
    merged = data["whatever"]
    assert merged["life_id"] == "PGN@L1-G1-X"  # entry not overwritten
    assert merged["trust_state"] == "registry_verified"  # entry not overwritten
    assert data["__anchor"]["keep"] == 1  # sibling entries untouched
    assert merged["cid"] == CID
    types = [h["type"] for h in merged["transport_hints"]]
    assert "ipfs" in types and "github_raw" in types  # hint attached, not replaced


def test_index_update_refuses_unknown_gene(tmp_path):
    idx = tmp_path / ".akashic_index.json"
    idx.write_text(json.dumps({"known": {"content_sha256": "f" * 64}}), encoding="utf-8", newline="")
    assert ipfs_upload.update_akashic_index("unknown-gene", CID, SHA, 455, index_file=idx) is False


def test_pull_gateway_list_has_no_dead_entries():
    joined = " ".join(ipfs_pull.IPFS_GATEWAYS)
    assert "cloudflare-ipfs" not in joined and "ghproxy" not in joined
