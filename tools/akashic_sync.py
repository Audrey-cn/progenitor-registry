import json
import hashlib
import os
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
REGISTRY_DIR = SCRIPT_DIR.parent.parent / "progenitor-registry"

IPFS_GATEWAYS = [
    "https://ipfs.io/ipfs/",
    "https://dweb.link/ipfs/",
    "https://cloudflare-ipfs.com/ipfs/",
    "https://ghproxy.com/ipfs/",
]


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_index():
    index_path = REGISTRY_DIR / ".akashic_index.json"
    if not index_path.exists():
        return {}
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_index(index):
    index_path = REGISTRY_DIR / ".akashic_index.json"
    tmp_path = REGISTRY_DIR / ".akashic_index.json.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    tmp_path.replace(index_path)


def verify_consistency(index):
    genes_dir = REGISTRY_DIR / "genes"
    issues = []

    for name, entry in index.items():
        cid = entry.get("cid")
        if not cid:
            issues.append(f"[{name}] 缺少 cid 字段")
            continue

        gene_path = genes_dir / cid
        if not gene_path.exists():
            issues.append(f"[{name}] CID={cid[:12]}... 基因文件不存在于 genes/")
            continue

        actual_sha = compute_sha256(gene_path)
        expected = entry.get("expected_sha256", "")

        if cid != actual_sha:
            issues.append(f"[{name}] CID 不匹配文件名: 文件名={cid[:12]}... 实际SHA={actual_sha[:12]}...")

        if expected and expected != actual_sha:
            issues.append(f"[{name}] expected_sha256 与实际不匹配")

    return issues


def pull_from_remote(index_url=None):
    print("尝试从远端同步阿卡西索引...")
    try:
        from urllib.request import urlopen
        url = index_url or os.environ.get("PROGENITOR_AKASHIC_INDEX_URL", "")
        if not url:
            print("未配置远端索引 URL，跳过同步")
            return False

        with urlopen(url, timeout=15) as resp:
            remote_index = json.loads(resp.read().decode("utf-8"))

        local_index = load_index()
        new_entries = 0
        for name, entry in remote_index.items():
            if name not in local_index:
                local_index[name] = entry
                new_entries += 1

        if new_entries > 0:
            save_index(local_index)
            print(f"同步完成：新增 {new_entries} 条索引记录")
        else:
            print("本地索引已是最新")
        return True
    except Exception as e:
        print(f"同步失败: {e}")
        return False


def push_to_remote():
    print("推送功能需要配合 Git 提交使用")
    index = load_index()
    print(f"当前索引包含 {len(index)} 条记录")
    return True


def sync_with_ipfs():
    """同步IPFS网关上的基因片段"""
    print("\n🌌 IPFS阿卡夏星门同步")
    print("=" * 50)

    try:
        import ipfshttpclient
    except ImportError:
        print("⚠️ ipfshttpclient未安装，跳过IPFS同步")
        print("  安装命令: pip install ipfshttpclient")
        return False

    index = load_index()
    genes_dir = REGISTRY_DIR / "genes"
    synced = 0
    failed = 0

    for name, entry in index.items():
        cid = entry.get("cid")
        source = entry.get("source", "")

        if source != "ipfs":
            continue

        gene_path = genes_dir / cid
        if gene_path.exists():
            continue

        print(f"\n📥 同步基因: {name}")
        print(f"   CID: {cid}")

        for gateway in IPFS_GATEWAYS:
            url = f"{gateway}{cid}"
            try:
                from urllib.request import urlopen
                print(f"   尝试: {gateway}")
                with urlopen(url, timeout=30) as resp:
                    content = resp.read()
                    gene_path.write_bytes(content)
                    print(f"   ✅ 成功下载 via {gateway}")
                    synced += 1
                    break
            except Exception as e:
                continue
        else:
            print(f"   ❌ 所有网关均失败")
            failed += 1

    print(f"\n📊 IPFS同步完成: {synced} 成功, {failed} 失败")
    return True


def main():
    import sys

    if len(sys.argv) < 2:
        print("用法: python akashic_sync.py [--pull|--verify|--push|--ipfs]")
        print()
        print("  --pull    从远端同步阿卡西索引")
        print("  --verify  验证本地索引与基因文件一致性")
        print("  --push    推送本地索引（通过 Git）")
        print("  --ipfs    从IPFS网关同步基因文件")
        sys.exit(0)

    action = sys.argv[1]

    if action == "--verify":
        index = load_index()
        if not index:
            print("未找到 .akashic_index.json")
            return

        print("=" * 50)
        print("  阿卡西索引一致性验证")
        print("=" * 50)
        print(f"索引条目数: {len(index)}")

        issues = verify_consistency(index)
        if issues:
            print(f"\n发现 {len(issues)} 个问题:")
            for issue in issues:
                print(f"  ⚠️ {issue}")
        else:
            print("\n✅ 所有条目一致，无问题")
        print()

    elif action == "--pull":
        pull_from_remote()

    elif action == "--push":
        push_to_remote()

    elif action == "--ipfs":
        sync_with_ipfs()

    else:
        print(f"未知操作: {action}")
        print("可用操作: --pull, --verify, --push, --ipfs")


if __name__ == "__main__":
    main()
