#!/usr/bin/env python3
"""IPFS pull tool — stdlib-only (HTTP gateways + local Kubo RPC cat).

Gateway list refreshed 2026-09-22 (cloudflare-ipfs.com is shut down; ghproxy.com was
never an IPFS gateway). Verification is now honest: a pulled gene's SHA-256 is checked
against the index's registered `content_sha256` (matched by CID) when available — the
old "SHA-256 vs CID string" comparison was meaningless.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from urllib import request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import REGISTRY_DIR  # noqa: E402

INDEX_FILE = REGISTRY_DIR / ".akashic_index.json"
GENES_DIR = REGISTRY_DIR / "genes"

IPFS_GATEWAYS = [
    "https://ipfs.io/ipfs/",
    "https://dweb.link/ipfs/",
    "https://w3s.link/ipfs/",
    "https://4everland.io/ipfs/",
]

DEFAULT_API = "http://127.0.0.1:5001"
MAX_PULL_BYTES = 8 * 1024 * 1024


def compute_sha256(filepath) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _api_base(api_url):
    import os
    return (api_url or __import__("os").environ.get("PROGENITOR_IPFS_API") or DEFAULT_API).rstrip("/")


def pull_via_gateway(cid, output_path, timeout=30):
    for gateway in IPFS_GATEWAYS:
        url = f"{gateway.rstrip('/')}/ipfs/{cid}"
        try:
            print(f"   尝试: {gateway}")
            req = request.Request(url, headers={"User-Agent": "progenitor-pull/2.0"})
            with request.urlopen(req, timeout=timeout) as resp:
                content = resp.read(MAX_PULL_BYTES + 1)
            if len(content) > MAX_PULL_BYTES:
                print("   超过大小上限,拒绝")
                continue
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(content)
            return True, gateway
        except Exception as e:
            print(f"   失败: {e}")
            continue
    return False, None


def pull_via_api(cid, output_path, api_url=None):
    """Fetch raw bytes from the local Kubo RPC (`cat`), stdlib-only."""
    try:
        req = request.Request(f"{_api_base(api_url)}/api/v0/cat?arg={cid}", method="POST")
        with request.urlopen(req, timeout=60) as resp:
            content = resp.read(MAX_PULL_BYTES + 1)
        if len(content) > MAX_PULL_BYTES:
            return False
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(content)
        return True
    except Exception:
        return False


def pull_from_ipfs(cid, output_path=None, use_gateway=True, api_url=None):
    if output_path is None:
        output_path = GENES_DIR / cid
    output_path = Path(output_path)

    print(f"\n📥 从IPFS拉取:\n   CID: {cid}\n   输出: {output_path}\n")

    if use_gateway:
        print("🔄 通过HTTP网关拉取...")
        success, gateway = pull_via_gateway(cid, output_path)
        if success:
            print(f"✅ 拉取成功! (via {gateway})")
            return True, output_path, gateway
        print("❌ HTTP网关全部失败,尝试本地API...")
    print("🔄 尝试本地IPFS API...")
    if pull_via_api(cid, output_path, api_url):
        print("✅ 拉取成功! (via Local API)")
        return True, output_path, "Local API"
    return False, None, None


def _expected_sha_for(cid):
    """Look up the registered content_sha256 for a CID in the akashic index."""
    if not INDEX_FILE.exists():
        return None
    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    for entry in index.values():
        if entry.get("cid") == cid or entry.get("content_sha256") == cid:
            return entry.get("content_sha256")
    return None


def pull_gene(cid, gene_name=None, verify=True, api_url=None):
    if gene_name is None:
        gene_name = cid[:16] + "_pulled"
    output_path = GENES_DIR / gene_name

    success, path, method = pull_from_ipfs(cid, output_path, api_url=api_url)
    if not success:
        print(f"\n❌ 拉取失败: CID = {cid}")
        return None

    if verify:
        actual_sha = compute_sha256(path)
        expected = _expected_sha_for(cid)
        print(f"\n🔍 完整性验证:\n   文件SHA-256: {actual_sha}")
        if expected is None:
            print("   ⚠ 索引中无此CID的登记哈希,无法交叉验证")
        elif actual_sha == expected:
            print(f"   ✅ 与索引登记的 content_sha256 一致 ({expected[:16]}…)")
        else:
            print(f"   ❌ 与索引登记值不一致 ({expected[:16]}…) — 拒绝信任此内容")
            return None
    return path


def list_indexed_genes():
    if not INDEX_FILE.exists():
        print("未找到阿卡西索引")
        return []
    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    print(f"\n📚 阿卡西索引 ({len(index)} 条记录):")
    print("-" * 60)
    for name, entry in index.items():
        print(f"  {name}\n    CID: {entry.get('cid', 'N/A')}\n    SHA-256: {entry.get('content_sha256', 'N/A')}")
    return list(index.keys())


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    api_url = None
    if "--api" in argv:
        i = argv.index("--api")
        api_url = argv[i + 1]
        del argv[i:i + 2]
    if not argv:
        print(__doc__)
        print("""
用法:
  python ipfs_pull.py <cid>              # 拉取指定CID
  python ipfs_pull.py <cid> --name <n>   # 指定输出文件名
  python ipfs_pull.py <cid> --no-verify  # 跳过索引交叉验证
  python ipfs_pull.py --list             # 列出索引中的基因
  python ipfs_pull.py --gateways         # 显示可用网关
""")
        return 0
    arg = argv[0]
    if arg == "--list":
        list_indexed_genes()
    elif arg == "--gateways":
        print("可用IPFS网关:")
        for gw in IPFS_GATEWAYS:
            print(f"  {gw}")
    else:
        gene_name = None
        verify = "--no-verify" not in argv
        if "--name" in argv:
            i = argv.index("--name")
            gene_name = argv[i + 1] if i + 1 < len(argv) else None
            del argv[i:i + 2]
        if "--no-verify" in argv:
            i = argv.index("--no-verify")
            del argv[i:i + 1]
        pull_gene(arg, gene_name, verify=verify, api_url=api_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
