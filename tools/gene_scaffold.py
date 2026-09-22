#!/usr/bin/env python3
"""Gene scaffold — the first step of the external-contributor flow.

Non-interactive (script/CI friendly):

    python tools/gene_scaffold.py --name markdown-parser --creator YourName \\
        --description "Parse markdown into structured sections"

Interactive mode stays available: run with no arguments.

After scaffolding (see CONTRIBUTING.md for the full flow):
  1. rename the file to its SHA-256 and put it in genes/
  2. optionally sign it:  tools/sign_gene.py genes/<sha>  (after CREATOR_PRIVATE_KEY_JSON)
  3. open a PR — the Gatekeeper runs L0-L6 and upgrades trust_state for keyring-signed genes
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from repo_paths import REGISTRY_DIR  # noqa: E402

INDEX_FILE = REGISTRY_DIR / ".akashic_index.json"
GENES_DIR = REGISTRY_DIR / "genes"


def compute_sha256(filepath) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_next_gene_number():
    """Next G-number from the life_id series (PGN@L*-G<n>-NAME)."""
    if not INDEX_FILE.exists():
        return 1
    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    max_num = 0
    for entry in index.values():
        life_id = entry.get("life_id", "")
        if life_id.startswith("PGN@L") and "-G" in life_id:
            try:
                num = int(life_id.split("-G")[1].split("-")[0])
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


def scaffold(gene_name: str, creator: str, description: str, level: str = "L1",
             out_dir: Path | None = None) -> Path:
    if not gene_name or not gene_name.replace("-", "").replace("_", "").isalnum():
        raise ValueError(f"invalid gene name: {gene_name!r} (use letters/digits/-/_)")
    if len(description) < 10:
        raise ValueError("description must be at least 10 characters")
    if level not in ("L1", "L2", "L3"):
        level = "L1"

    gene_number = get_next_gene_number()
    content = GENE_TEMPLATE.format(
        level=level,
        gene_number=gene_number,
        gene_name_upper=gene_name.upper().replace("-", "_"),
        creator=creator,
        description=description,
        gene_name=gene_name,
    )
    out_dir = Path(out_dir) if out_dir else REGISTRY_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{gene_name}.py"
    output_path.write_text(content, encoding="utf-8", newline="")
    sha = compute_sha256(output_path)

    print("=" * 50)
    print(f"✅ gene scaffolded: {output_path}")
    print(f"   life_id: PGN@{level}-G{gene_number}-{gene_name.upper().replace('-', '_')}")
    print(f"   SHA-256: {sha}")
    print()
    print("   next steps (CONTRIBUTING.md):")
    print(f"   1. rename:  mv {output_path} {GENES_DIR / sha}")
    print(f"   2. (optional, recommended) sign it:")
    print(f"        CREATOR_PRIVATE_KEY_JSON=... python tools/sign_gene.py genes/{sha}")
    print(f"   3. open a PR — Gatekeeper runs L0-L6 automatically")
    return output_path


def scaffold_interactive():
    print("╔══════════════════════════════════════════╗")
    print("║  Progenitor 基因脚手架生成器             ║")
    print("╚══════════════════════════════════════════╝")
    print()
    gene_name = input("基因语义名 (如 markdown-parser): ").strip()
    creator = input("创造者名 [Anonymous]: ").strip() or "Anonymous"
    description = input("基因描述: ").strip()
    level = input("基因层级 L1/L2/L3 [L1]: ").strip().upper()
    try:
        scaffold(gene_name, creator, description, level)
    except ValueError as exc:
        print(f"错误: {exc}")
        sys.exit(1)


def main():
    argv = sys.argv[1:]
    if not argv:
        scaffold_interactive()
        return 0
    if argv[0] == "--hash-only":
        if len(argv) < 2:
            print("用法: python gene_scaffold.py --hash-only <文件路径>")
            return 2
        print(f"SHA-256: {compute_sha256(argv[1])}")
        return 0
    if argv[0] in ("--help", "-h"):
        print(__doc__)
        return 0

    opts = {"level": "L1", "creator": "Anonymous", "out": None}
    i = 0
    while i < len(argv):
        if argv[i] == "--name":
            opts["name"] = argv[i + 1]; i += 2
        elif argv[i] == "--creator":
            opts["creator"] = argv[i + 1]; i += 2
        elif argv[i] == "--description":
            opts["description"] = argv[i + 1]; i += 2
        elif argv[i] == "--level":
            opts["level"] = argv[i + 1]; i += 2
        elif argv[i] == "--out":
            opts["out"] = argv[i + 1]; i += 2
        else:
            print(f"未知参数: {argv[i]}"); return 2
    try:
        scaffold(opts["name"], opts["creator"], opts["description"],
                 opts["level"], opts["out"])
    except (ValueError, KeyError) as exc:
        print(f"错误: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
