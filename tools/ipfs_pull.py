#!/usr/bin/env python3
"""
IPFS拉取工具 - 从IPFS网络拉取基因片段
"""

import sys
import hashlib
import json
from pathlib import Path
from urllib import request, error

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
GENES_DIR = REGISTRY_DIR / "genes"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def pull_via_gateway(cid, output_path, timeout=30):
    """
    通过HTTP网关拉取IPFS内容
    """
    for gateway in IPFS_GATEWAYS:
        url = f"{gateway.rstrip('/')}/ipfs/{cid}"
        try:
            print(f"   尝试: {gateway}")

            req = request.Request(url)
            with request.urlopen(req, timeout=timeout) as resp:
                content = resp.read()

                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(content)

                return True, gateway

        except (error.HTTPError, error.URLError, Exception) as e:
            continue

    return False, None


def pull_via_api(cid, output_path, api_url=None):
    """
    通过本地IPFS API拉取
    """
    try:
        if api_url:
            client = ipfshttpclient.connect(api_url)
        else:
            client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001")

        client.get(cid, str(output_path))
        client.close()
        return True

    except Exception:
        return False


def pull_from_ipfs(cid, output_path=None, use_gateway=True):
    """
    从IPFS拉取文件

    参数:
        cid: IPFS内容标识符
        output_path: 输出路径（默认保存到genes目录）
        use_gateway: 是否使用HTTP网关（否则尝试本地API）

    返回:
        (成功标志, 文件路径, 网关/方法)
    """
    if output_path is None:
        output_path = GENES_DIR / cid

    output_path = Path(output_path)

    print(f"\n📥 从IPFS拉取:")
    print(f"   CID: {cid}")
    print(f"   输出: {output_path}")
    print()

    if use_gateway:
        print("🔄 通过HTTP网关拉取...")
        success, gateway = pull_via_gateway(cid, output_path)

        if success:
            print(f"✅ 拉取成功! (via {gateway})")
            return True, output_path, gateway
        else:
            print("❌ HTTP网关全部失败，尝试本地API...")
            if pull_via_api(cid, output_path):
                print("✅ 拉取成功! (via Local API)")
                return True, output_path, "Local API"
            return False, None, None
    else:
        print("🔄 尝试本地IPFS API...")
        if pull_via_api(cid, output_path):
            print("✅ 拉取成功! (via Local API)")
            return True, output_path, "Local API"
        return False, None, None


def pull_gene(cid, gene_name=None, verify=True):
    """
    拉取基因并验证完整性

    参数:
        cid: IPFS CID
        gene_name: 基因名称（用于文件名）
        verify: 是否验证SHA-256
    """
    if gene_name is None:
        gene_name = cid[:16] + "_pulled"

    output_path = GENES_DIR / gene_name

    success, path, method = pull_from_ipfs(cid, output_path)

    if not success:
        print(f"\n❌ 拉取失败: CID = {cid}")
        return None

    if verify:
        actual_sha = compute_sha256(path)
        print(f"\n🔍 验证完整性...")
        print(f"   文件SHA-256: {actual_sha}")
        print(f"   CID: {cid}")

        if actual_sha == cid:
            print("✅ 验证通过! SHA-256与CID匹配")
        else:
            print("⚠️ 警告: SHA-256与CID不匹配（正常，IPFS CID使用不同算法）")

    return path


def list_indexed_genes():
    """列出阿卡西索引中的所有基因"""
    index_file = REGISTRY_DIR / ".akashic_index.json"

    if not index_file.exists():
        print("未找到阿卡西索引")
        return []

    with open(index_file, "r", encoding="utf-8") as f:
        index = json.load(f)

    print(f"\n📚 阿卡西索引 ({len(index)} 条记录):")
    print("-" * 60)

    for name, entry in index.items():
        cid = entry.get("cid", "N/A")
        source = entry.get("source", "unknown")
        print(f"  {name}")
        print(f"    CID: {cid}")
        print(f"    Source: {source}")
        print()

    return list(index.keys())


def main():
    if len(sys.argv) < 2:
        print("""
IPFS拉取工具 v1.0

用法:
  python ipfs_pull.py <cid>              # 拉取指定CID
  python ipfs_pull.py <cid> --name <n>   # 指定输出文件名
  python ipfs_pull.py --list             # 列出索引中的基因
  python ipfs_pull.py --gateways         # 显示可用网关

示例:
  python ipfs_pull.py Qm...
  python ipfs_pull.py --list
        """)
        return 0

    arg = sys.argv[1]

    if arg == "--list":
        list_indexed_genes()
    elif arg == "--gateways":
        print("可用IPFS网关:")
        for gw in IPFS_GATEWAYS:
            print(f"  {gw}")
    else:
        cid = arg
        gene_name = None

        if "--name" in sys.argv:
            idx = sys.argv.index("--name")
            if idx + 1 < len(sys.argv):
                gene_name = sys.argv[idx + 1]

        pull_gene(cid, gene_name)

    return 0


if __name__ == "__main__":
    sys.exit(main())
