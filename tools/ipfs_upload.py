#!/usr/bin/env python3
"""IPFS upload tool — stdlib-only, Kubo RPC v0.

Replaces the deprecated third-party `ipfshttpclient` (incompatible with modern Kubo RPC
and a violation of the zero-dependency rule). Requires a local Kubo daemon (default
http://127.0.0.1:5001, override via PROGENITOR_IPFS_API or --api).

Upload semantics: `pin=true&raw-leaves=true&cid-version=1` — a raw-leaf CIDv1 is the
base32 of the content's SHA-256, so CID and `content_sha256` are mutually checkable.

Index safety: `update_akashic_index` never overwrites a gene entry; it only adds an
`ipfs` transport hint to an EXISTING entry matched by content hash (the former behaviour
replaced whole entries with 5-field stubs, destroying life_id/creator/trust_state).
NOTE: changing the index invalidates its signature — re-sign via tools/sign_index.py
(with REGISTRY_PRIVATE_KEY_JSON) or run with --no-index.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from pathlib import Path
from urllib import error, request

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
MAX_ADD_BYTES = 8 * 1024 * 1024  # genes are small; refuse runaway payloads


def compute_sha256(filepath) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _api_base(api_url: str | None) -> str:
    return (api_url or os.environ.get("PROGENITOR_IPFS_API") or DEFAULT_API).rstrip("/")


def upload_to_ipfs(filepath, api_url=None) -> tuple[str, int, str]:
    """Add (and pin) a file via the local Kubo RPC. Returns (cid, size, sha256)."""
    payload = Path(filepath).read_bytes()
    if len(payload) > MAX_ADD_BYTES:
        raise ValueError(f"payload exceeds {MAX_ADD_BYTES} bytes — refusing")

    boundary = "----progenitor" + uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{Path(filepath).name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()

    params = "pin=true&raw-leaves=true&cid-version=1&quiet=true&quieter=true"
    req = request.Request(
        f"{_api_base(api_url)}/api/v0/add?{params}",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with request.urlopen(req, timeout=120) as resp:
        lines = [ln for ln in resp.read().decode().splitlines() if ln.strip()]
    result = json.loads(lines[-1])  # last line is the final file entry

    cid = result["Hash"]
    size = int(result.get("Size", len(payload)))
    return cid, size, compute_sha256(filepath)


def get_gateway_url(cid, gateway=None):
    if gateway:
        return f"{gateway.rstrip('/')}/ipfs/{cid}"
    return [f"{gw}{cid}" for gw in IPFS_GATEWAYS]


def verify_upload(cid: str, filepath) -> bool:
    """Raw-leaf CIDv1 decodes to <0x01><0x55><0x12><0x20><32-byte sha256> — the CID's
    payload ends with the content's SHA-256, so CID and content hash cross-check."""
    sha = compute_sha256(filepath)
    try:
        import base64
        if not cid.startswith("b") or len(cid) < 10:
            return False
        payload = base64.b32decode(cid[1:].upper() + "=" * (-(len(cid) - 1) % 8))
        return payload[-32:].hex() == sha
    except Exception:
        return False


def update_akashic_index(gene_name, cid, sha256, size, index_file=None):
    """Attach an `ipfs` transport hint to an EXISTING index entry (never overwrite)."""
    index_file = Path(index_file or INDEX_FILE)
    index = json.loads(index_file.read_text(encoding="utf-8")) if index_file.exists() else {}

    entry = None
    key = None
    for k, v in index.items():
        if isinstance(v, dict) and (k == gene_name or v.get("content_sha256") == sha256):
            entry, key = v, k
            break
    if entry is None:
        print(f"⚠ 基因不在索引中,跳过索引更新: {gene_name} (sha256={sha256[:12]}…)")
        return False

    hints = entry.setdefault("transport_hints", [])
    hint = {"type": "ipfs", "url": cid, "priority": 90}
    if not any(h.get("type") == "ipfs" and h.get("url") == cid for h in hints):
        hints.append(hint)
    entry["cid"] = cid  # dual-reference: content hash stays authoritative

    index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8", newline="")
    print(f"✅ 阿卡西索引已附加 ipfs 传输提示: {key}")
    return True


def upload_gene(gene_path, gene_name=None, update_index=True, api_url=None):
    gene_path = Path(gene_path)
    if not gene_path.exists():
        print(f"错误: 文件不存在: {gene_path}")
        return None
    if gene_name is None:
        gene_name = gene_path.stem

    print(f"\n📤 开始上传基因片段到IPFS:")
    print(f"   文件: {gene_path}")
    print(f"   大小: {gene_path.stat().st_size} bytes")

    try:
        cid, size, sha256 = upload_to_ipfs(gene_path, api_url)
        print(f"\n✅ 上传成功!")
        print(f"   CID: {cid}")
        print(f"   SHA-256: {sha256}")
        print(f"   CID↔SHA256 互证: {'✓' if verify_upload(cid, gene_path) else '✗ (非 raw-leaf CID?)'}")
        print(f"\n🌐 网关地址:")
        for url in get_gateway_url(cid)[:2]:
            print(f"   {url}")
        if update_index:
            update_akashic_index(gene_name, cid, sha256, size)
        return {"cid": cid, "sha256": sha256, "size": size, "gateways": get_gateway_url(cid)}
    except (error.URLError, OSError) as e:
        print(f"\n❌ 上传失败(本地 Kubo daemon 在运行吗? {_api_base(api_url)}): {e}")
        return None
    except Exception as e:
        print(f"\n❌ 上传失败: {e}")
        return None


def batch_upload(genes_dir=None, api_url=None):
    genes_dir = Path(genes_dir or GENES_DIR)
    if not genes_dir.exists():
        print(f"错误: 目录不存在: {genes_dir}")
        return []
    files = [f for f in genes_dir.glob("*") if f.is_file()]
    if not files:
        print(f"警告: 目录为空: {genes_dir}")
        return []
    print(f"\n📂 批量上传: {len(files)} 个文件")
    results = []
    for i, gf in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {gf.name}")
        results.append(upload_gene(gf, api_url=api_url))
    ok = sum(1 for r in results if r)
    print(f"\n📊 批量上传完成: {ok}/{len(files)} 成功")
    return results


def main(argv=None):
    argv = list(argv) if argv is not None else sys.argv[1:]
    api_url = None
    if "--api" in argv:
        i = argv.index("--api")
        api_url = argv[i + 1] if i + 1 < len(argv) else None
        del argv[i:i + 2]
    if not argv:
        print(__doc__)
        print("""
用法:
  python ipfs_upload.py <file>            # 上传单个文件
  python ipfs_upload.py <file> --name <n> # 指定基因名称
  python ipfs_upload.py <file> --no-index # 不更新索引(索引改写需重签名)
  python ipfs_upload.py --batch           # 批量上传 genes/
  python ipfs_upload.py --list            # 列出可用网关
""")
        return 0
    if argv[0] == "--batch":
        batch_upload(api_url=api_url)
    elif argv[0] == "--list":
        print("可用IPFS网关:")
        for gw in IPFS_GATEWAYS:
            print(f"  {gw}")
    else:
        gene_name = None
        if "--name" in argv:
            i = argv.index("--name")
            gene_name = argv[i + 1] if i + 1 < len(argv) else None
            del argv[i:i + 2]
        update_index = "--no-index" not in argv
        upload_gene(argv[0], gene_name, update_index=update_index, api_url=api_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
