import sys
import os
import hashlib
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
GIT_DIR = SCRIPT_DIR.parent


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_next_gene_number():
    registry_dir = GIT_DIR.parent / "progenitor-registry"
    index_path = registry_dir / ".akashic_index.json"

    if not index_path.exists():
        return 1

    import json
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    max_num = 0
    for entry in index.values():
        life_id = entry.get("life_id", "")
        if life_id.startswith("PGN@L") and "-G" in life_id:
            try:
                g_part = life_id.split("-G")[1].split("-")[0]
                num = int(g_part)
                max_num = max(max_num, num)
            except (ValueError, IndexError):
                pass

    return max_num + 1


GENE_TEMPLATE = '''# life_id: PGN@{level}-G{gene_number}-{gene_name_upper}
# creator: {creator}
# description: {description}

"""
{description}
"""


def main():
    return {{"status": "success", "gene": "{gene_name}"}}


if __name__ == "__main__":
    print(main())
'''


def scaffold_interactive():
    print("╔══════════════════════════════════════════╗")
    print("║  Progenitor 基因脚手架生成器 v1.0       ║")
    print("╚══════════════════════════════════════════╝")
    print()

    gene_name = input("基因语义名 (如 markdown-parser): ").strip()
    if not gene_name:
        print("基因名不能为空")
        sys.exit(1)

    creator = input("创造者名 [Anonymous]: ").strip()
    if not creator:
        creator = "Anonymous"

    description = input("基因描述: ").strip()
    if len(description) < 10:
        print("描述至少需要 10 个字符")
        sys.exit(1)

    level = input("基因层级 L1/L2/L3 [L1]: ").strip().upper()
    if level not in ("L1", "L2", "L3"):
        level = "L1"

    gene_number = get_next_gene_number()
    gene_name_upper = gene_name.upper().replace("-", "_")

    content = GENE_TEMPLATE.format(
        level=level,
        gene_number=gene_number,
        gene_name_upper=gene_name_upper,
        creator=creator,
        description=description,
        gene_name=gene_name
    )

    output_name = f"{gene_name}.py"
    output_path = GIT_DIR / output_name

    if output_path.exists():
        overwrite = input(f"文件 {output_name} 已存在，覆盖? (y/N): ").strip().lower()
        if overwrite != "y":
            print("已取消")
            sys.exit(0)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    sha = compute_sha256(output_path)

    print()
    print("=" * 50)
    print(f"✅ 基因文件已生成: {output_path}")
    print(f"   生命ID: PGN@{level}-G{gene_number}-{gene_name_upper}")
    print(f"   SHA-256: {sha}")
    print(f"   下一步: 将文件重命名为 {sha} 并复制到 progenitor-registry/genes/")
    print("=" * 50)


def hash_only(filepath):
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        sys.exit(1)
    sha = compute_sha256(filepath)
    print(f"SHA-256: {sha}")
    return sha


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--hash-only":
            if len(sys.argv) < 3:
                print("用法: python gene_scaffold.py --hash-only <文件路径>")
                sys.exit(1)
            hash_only(sys.argv[2])
            return
        elif arg == "--help":
            print("用法: python gene_scaffold.py [--hash-only <file>]")
            print()
            print("  无参数    交互式创建基因脚手架")
            print("  --hash-only <file>  计算文件 SHA-256 哈希")
            sys.exit(0)

    scaffold_interactive()


if __name__ == "__main__":
    main()
