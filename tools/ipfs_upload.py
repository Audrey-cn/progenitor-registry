#!/usr/bin/env python3
"""
IPFS上传工具 - 将基因片段上传到IPFS网络
"""

import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime

try:
    import ipfshttpclient
except ImportError:
    print("错误: 需要安装 ipfshttpclient")
    print("运行: pip install ipfshttpclient")
    sys.exit(1)


IPFS_GATEWAYS = [
    "https://ipfs.io/ipfs/",
    "https://dweb.link/ipfs/",
    "https://cloudflare-ipfs.com/ipfs/",
    "https://ghproxy.com/ipfs/",
]

SCRIPT_DIR = Path(__file__).parent
REGISTRY_DIR = SCRIPT_DIR.parent.parent / "progenitor-registry"
INDEX_FILE = REGISTRY_DIR / ".akashic_index.json"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def upload_to_ipfs(filepath, api_url=None):
    """
    上传文件到IPFS网络
    返回: (cid, size, sha256)
    """
    try:
        if api_url:
            client = ipfshttpclient.connect(api_url)
        else:
            client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001")

        res = client.add(str(filepath))
        cid = res["Hash"]
        size = res["Size"]

        sha256_hash = compute_sha256(filepath)

        client.close()

        return cid, size, sha256_hash

    except Exception as e:
        raise Exception(f"IPFS上传失败: {e}")


def get_gateway_url(cid, gateway=None):
    """获取IPFS网关URL"""
    if gateway:
        return f"{gateway.rstrip('/')}/ipfs/{cid}"
    return [f"{gw}{cid}" for gw in IPFS_GATEWAYS]


def verify_upload(cid, filepath):
    """验证上传结果的完整性"""
    expected_sha = compute_sha256(filepath)
    return cid == expected_sha


def update_akashic_index(gene_name, cid, sha256, size):
    """更新阿卡西索引"""
    index = {}
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            index = json.load(f)

    index[gene_name] = {
        "cid": cid,
        "expected_sha256": sha256,
        "size": size,
        "uploaded_at": datetime.now().isoformat(),
        "source": "ipfs"
    }

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"✅ 阿卡西索引已更新: {gene_name}")


def upload_gene(gene_path, gene_name=None, update_index=True):
    """
    上传基因文件到IPFS

    参数:
        gene_path: 基因文件路径
        gene_name: 基因名称（可选，默认使用文件名）
        update_index: 是否更新阿卡西索引
    """
    gene_path = Path(gene_path)
    if not gene_path.exists():
        print(f"错误: 文件不存在: {gene_path}")
        return None

    if gene_name is None:
        gene_name = gene_path.stem

    print(f"\n📤 开始上传基因片段到IPFS:")
    print(f"   文件: {gene_path}")
    print(f"   名称: {gene_name}")
    print(f"   大小: {gene_path.stat().st_size} bytes")
    print()

    try:
        print("🔄 正在上传到IPFS网络...")
        cid, size, sha256 = upload_to_ipfs(gene_path)

        print(f"\n✅ 上传成功!")
        print(f"   CID: {cid}")
        print(f"   SHA-256: {sha256}")
        print(f"   大小: {size}")

        gateway_urls = get_gateway_url(cid)
        print(f"\n🌐 IPFS网关地址:")
        for url in gateway_urls[:2]:
            print(f"   {url}")

        if update_index:
            update_akashic_index(gene_name, cid, sha256, size)

        return {
            "cid": cid,
            "sha256": sha256,
            "size": size,
            "gateways": gateway_urls
        }

    except Exception as e:
        print(f"\n❌ 上传失败: {e}")
        return None


def batch_upload(genes_dir=None):
    """批量上传基因目录中的所有基因"""
    if genes_dir is None:
        genes_dir = REGISTRY_DIR / "genes"

    genes_dir = Path(genes_dir)
    if not genes_dir.exists():
        print(f"错误: 目录不存在: {genes_dir}")
        return []

    gene_files = list(genes_dir.glob("*"))
    if not gene_files:
        print(f"警告: 目录为空: {genes_dir}")
        return []

    print(f"\n📂 批量上传: 找到 {len(gene_files)} 个文件")
    print(f"   目录: {genes_dir}")
    print()

    results = []
    for i, gene_file in enumerate(gene_files, 1):
        if gene_file.is_file():
            print(f"[{i}/{len(gene_files)}] 上传: {gene_file.name}")
            result = upload_gene(gene_file, update_index=True)
            results.append(result)
            print()

    success = sum(1 for r in results if r is not None)
    print(f"\n📊 批量上传完成: {success}/{len(gene_files)} 成功")
    return results


def main():
    if len(sys.argv) < 2:
        print("""
IPFS上传工具 v1.0

用法:
  python ipfs_upload.py <file>           # 上传单个文件
  python ipfs_upload.py <file> --name <name>  # 指定基因名称
  python ipfs_upload.py --batch         # 批量上传genes目录
  python ipfs_upload.py --list          # 列出可用网关

示例:
  python ipfs_upload.py ../progenitor-registry/genes/<cid>
  python ipfs_upload.py --batch
        """)
        return 0

    if sys.argv[1] == "--batch":
        batch_upload()
    elif sys.argv[1] == "--list":
        print("可用IPFS网关:")
        for gw in IPFS_GATEWAYS:
            print(f"  {gw}")
    elif sys.argv[1] == "--help":
        main()
    else:
        gene_path = sys.argv[1]
        gene_name = None

        if "--name" in sys.argv:
            idx = sys.argv.index("--name")
            if idx + 1 < len(sys.argv):
                gene_name = sys.argv[idx + 1]

        upload_gene(gene_path, gene_name)

    return 0


if __name__ == "__main__":
    sys.exit(main())
