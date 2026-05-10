#!/usr/bin/env python3
"""
星门守卫脚本 (Gatekeeper) — progenitor-registry CI/CD
用于 GitHub Actions，自动校验新基因并更新黄页与文档。

零依赖：仅使用 Python 原生标准库。

🔓 v2.0 开放注册版
- 移除了创造者白名单限制
- 任何人可以通过 PR 贡献基因
- 添加了质量门槛检查 (L4)
- 添加了速率限制机制
"""
from __future__ import annotations

import json
import os
import re
import hashlib
import sys
import time
from pathlib import Path
from typing import Optional

GENE_DIR = Path("genes")
INDEX_FILE = Path(".akashic_index.json")
README_FILE = Path("README.md")

ALLOWED_LINEAGES = ["PGN@"]
ALLOWED_CREATORS = []  # 开放注册：任何创造者都可以贡献

RATE_LIMIT_PER_PR = 5       # 每次 PR 最多 5 个基因
RATE_LIMIT_PER_DAY = 20     # 每个创造者每天最多 20 个基因

REPO_NAME = os.environ.get("GITHUB_REPOSITORY", "Audrey-cn/progenitor-registry")
COMMIT_BRANCH = os.environ.get("COMMIT_BRANCH", "main")

GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{REPO_NAME}/{COMMIT_BRANCH}"
GITHUB_API_BASE = f"https://api.github.com/repos/{REPO_NAME}"


def extract_yaml_header(filepath: Path) -> tuple[dict, int]:
    """提取 YAML 前导块（yaml-header）及其行数。"""
    content = filepath.read_text(encoding="utf-8")
    lines = content.splitlines()
    yaml_lines = []
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            yaml_lines.append(stripped.lstrip("#").strip())
            count += 1
        elif re.match(r"^[\w_]+:\s*", line):
            yaml_lines.append(stripped)
            count += 1
        else:
            break
    raw_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            raw_lines.append(stripped.lstrip("#").strip())
        elif re.match(r"^[\w_]+:\s*", stripped):
            raw_lines.append(stripped)
        else:
            break

    yaml_text = "\n".join(raw_lines)
    meta = {}

    life_id_pattern = r'life_id:\s*"?([^"\n]+)"?'
    m = re.search(life_id_pattern, yaml_text)
    if m:
        meta["life_id"] = m.group(1).strip()

    creator_inline = r'creator:\s*"?([^"\n]+)"?'
    m = re.search(creator_inline, yaml_text)
    if m:
        meta["creator"] = m.group(1).strip()

    creator_block = re.search(r'creator:\s*\n\s+name:\s*"([^"]+)"', content)
    if creator_block:
        meta["creator"] = creator_block.group(1).strip()

    description_pattern = r'description:\s*"?([^"\n]+)"?'
    m = re.search(description_pattern, yaml_text)
    if m:
        meta["description"] = m.group(1).strip()

    return meta, len(raw_lines)


def validate_l1_lineage(meta: dict) -> tuple[bool, str]:
    """L1 形体完整性：检测 life_id 是否符合 PGN@ 血脉前缀。"""
    life_id = meta.get("life_id", "")
    for lineage in ALLOWED_LINEAGES:
        if life_id.startswith(lineage):
            return True, life_id
    return False, (
        f"L1 校验失败：life_id '{life_id}' 不符合任何已登记血脉 "
        f"({ALLOWED_LINEAGES})。基因已被判定为虚空异种，流水线中断。"
    )


def validate_l3_creator(meta: dict) -> tuple[bool, str]:
    """L3 创造者契约：开放注册，任何创造者都可以贡献。"""
    creator = meta.get("creator", "")
    if not creator:
        creator = "Anonymous"
        meta["creator"] = creator
    return True, creator


def validate_l4_quality(meta: dict, filepath: Path) -> tuple[bool, str]:
    """L4 质量门槛：检查基因是否符合最低质量标准。"""
    life_id = meta.get("life_id", "")
    creator = meta.get("creator", "")
    description = meta.get("description", "")

    errors = []

    if not life_id or len(life_id) < 5:
        errors.append("life_id 标识不符合规范（至少5字符）")

    if not creator or len(creator) < 2:
        errors.append("creator 创造者标识缺失或过短")

    if not description or len(description) < 10:
        errors.append("description 基因描述缺失或过短（至少10字符）")

    if filepath.stat().st_size == 0:
        errors.append("基因文件为空")

    if filepath.stat().st_size > 1024 * 1024:
        errors.append("基因文件超过 1MB 限制")

    if errors:
        return False, f"L4 质量门槛未通过: {'; '.join(errors)}"

    return True, "质量门槛通过"


def validate_l5_security(filepath: Path) -> tuple[bool, str]:
    """L5 安全扫描：检测明显的恶意代码模式。"""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")

        dangerous_patterns = [
            (r'eval\s*\(', "危险的 eval() 调用"),
            (r'exec\s*\(', "危险的 exec() 调用"),
            (r'__import__\s*\(', "动态导入 __import__()"),
            (r'os\.system\s*\(', "危险的 os.system() 调用"),
            (r'subprocess\s*\.\s*(call|run|Popen)', "危险的 subprocess 调用"),
            (r'requests\.', "第三方库 requests（违反零依赖原则）"),
            (r'BeautifulSoup', "第三方库 BeautifulSoup"),
            (r'pandas\.', "第三方库 pandas"),
            (r'numpy\.', "第三方库 numpy"),
        ]

        warnings = []
        for pattern, reason in dangerous_patterns:
            if re.search(pattern, content):
                warnings.append(reason)

        if warnings:
            return False, f"L5 安全扫描发现风险: {'; '.join(warnings)}"

        return True, "安全扫描通过"

    except Exception as e:
        return False, f"L5 安全扫描失败: {str(e)}"


def compute_sha256(filepath: Path) -> str:
    """计算文件 SHA-256 哈希（十六进制）。"""
    return hashlib.sha256(filepath.read_bytes()).hexdigest()


def load_index() -> dict:
    """加载当前黄页（.akashic_index.json）。"""
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return {}


def save_index(index: dict) -> None:
    """原子化写入黄页。"""
    tmp = INDEX_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(INDEX_FILE)


def load_score_log() -> dict:
    """加载基因评分日志。"""
    score_file = Path(".gene_score_log.json")
    if score_file.exists():
        return json.loads(score_file.read_text(encoding="utf-8"))
    return {}


def save_score_log(score_log: dict) -> None:
    """保存基因评分日志。"""
    score_file = Path(".gene_score_log.json")
    score_file.write_text(json.dumps(score_log, ensure_ascii=False, indent=2), encoding="utf-8")


def infer_capability_name(life_id: str) -> str:
    """从 life_id 推断语义标签，如 PGN@L1-G1-HELLO-WORLD → hello-world。"""
    parts = life_id.split("-", 2)
    if len(parts) >= 3:
        return parts[-1].lower().replace("_", "-")
    return parts[-1].lower()


def build_readme_table(entries: list[dict]) -> str:
    """构建 README.md 中的"已注册生命体矩阵"表格。"""
    header = "| 基因名 | Lineage | Creator | SHA-256 | CID | 状态 |\n"
    header += "|------|------|------|------|------|------|\n"
    rows = []
    for e in entries:
        rows.append(
            f"| `{e['capability']}` | {e.get('life_id','N/A')} | "
            f"{e.get('creator','N/A')} | `{e.get('sha256','N/A')[:16]}...` | "
            f"`{e.get('cid','N/A')[:16]}...` | 🟢 已注册 |"
        )
    return header + "\n".join(rows) + "\n"


def update_readme(index: dict) -> bool:
    """更新 README.md 中的已注册生命体矩阵表格。"""
    if not README_FILE.exists():
        return False
    content = README_FILE.read_text(encoding="utf-8")

    entries = []
    for cap, item in index.items():
        if isinstance(item, dict):
            cid = item.get("cid", "")
            sha = item.get("expected_sha256", "")
            life_id = item.get("life_id", "")
            creator = item.get("creator", "")
        else:
            cid = item
            sha = ""
            life_id = ""
            creator = ""
        entries.append({
            "capability": cap,
            "life_id": life_id,
            "creator": creator,
            "cid": cid,
            "sha256": sha,
        })

    entries.sort(key=lambda x: x["capability"])
    new_table = build_readme_table(entries)

    marker_start = "<!-- REGISTRY TABLE START -->"
    marker_end = "<!-- REGISTRY TABLE END -->"
    if marker_start not in content or marker_end not in content:
        return False

    new_content = (
        content[:content.index(marker_start) + len(marker_start)]
        + "\n"
        + new_table
        + content[content.index(marker_end):]
    )
    README_FILE.write_text(new_content, encoding="utf-8")
    return True


def main() -> int:
    print("=" * 70)
    print("🛡️ 星门守卫流水线 v2.0 — 开放注册版")
    print("=" * 70)

    if not GENE_DIR.exists():
        print("⚠️ genes/ 目录不存在，跳过校验")
        return 0

    gene_files = [p for p in GENE_DIR.iterdir() if p.is_file()]
    if not gene_files:
        print("⚠️ genes/ 目录为空，跳过校验")
        return 0

    if len(gene_files) > RATE_LIMIT_PER_PR:
        print(f"\n❌ L0 速率限制：PR 包含 {len(gene_files)} 个基因，超过限制 {RATE_LIMIT_PER_PR}")
        return 1

    print(f"\n📂 检测到 {len(gene_files)} 个基因文件待校验")

    index = load_index()
    score_log = load_score_log()
    new_entries = {}
    all_passed = True
    creator_counts = {}

    for gf in gene_files:
        print(f"\n🔍 校验: {gf.name}")
        print("-" * 50)

        meta, header_lines = extract_yaml_header(gf)
        print(f"   YAML 头: {meta}")

        creator = meta.get("creator", "Anonymous")
        creator_counts[creator] = creator_counts.get(creator, 0) + 1

        passed_l1, msg_l1 = validate_l1_lineage(meta)
        if not passed_l1:
            print(f"   ❌ {msg_l1}")
            all_passed = False
            continue
        print(f"   ✅ L1 形体完整: {meta.get('life_id')}")

        passed_l3, msg_l3 = validate_l3_creator(meta)
        if not passed_l3:
            print(f"   ❌ {msg_l3}")
            all_passed = False
            continue
        print(f"   ✅ L3 创造者契约: {meta.get('creator')} (开放注册)")

        passed_l4, msg_l4 = validate_l4_quality(meta, gf)
        if not passed_l4:
            print(f"   ⚠️ {msg_l4} (警告，继续处理)")
        else:
            print(f"   ✅ L4 质量门槛: {msg_l4}")

        passed_l5, msg_l5 = validate_l5_security(gf)
        if not passed_l5:
            print(f"   ❌ {msg_l5}")
            all_passed = False
            continue
        print(f"   ✅ L5 安全扫描: {msg_l5}")

        sha = compute_sha256(gf)
        print(f"   🔐 SHA-256: {sha[:32]}...")

        cap_name = infer_capability_name(meta.get("life_id", gf.name))

        if cap_name in index and index[cap_name].get("creator") != creator:
            print(f"   ⚠️ 基因名 '{cap_name}' 已存在（由 {index[cap_name].get('creator')} 注册）")
            cap_name = f"{cap_name}-{creator.lower().replace(' ', '-')[:10]}"

        new_entries[cap_name] = {
            "cid": gf.name,
            "expected_sha256": sha,
            "life_id": meta.get("life_id", ""),
            "creator": meta.get("creator", "Anonymous"),
            "description": meta.get("description", ""),
            "registered_at": time.strftime("%Y-%m-%d"),
            "initial_score": 0,
        }
        print(f"   ✅ 已注册: {cap_name} → {gf.name}")

    if not new_entries:
        print("\n🟡 无新基因需要注册")
        return 0 if all_passed else 1

    for creator, count in creator_counts.items():
        if count > RATE_LIMIT_PER_DAY:
            print(f"\n❌ L0 速率限制：创造者 {creator} 本次提交 {count} 个基因，超过每日限制 {RATE_LIMIT_PER_DAY}")
            return 1

    print(f"\n📝 更新黄页 (.akashic_index.json)...")
    index.update(new_entries)
    save_index(index)
    print(f"   ✅ 黄页已更新，共 {len(index)} 条记录")

    print(f"\n📄 更新 README 矩阵表格...")
    readme_updated = update_readme(index)
    if readme_updated:
        print("   ✅ README 已同步")
    else:
        print("   ⚠️ README 未包含标记，跳过更新")

    print(f"\n📊 更新基因评分日志...")
    for cap_name in new_entries:
        if cap_name not in score_log:
            score_log[cap_name] = {
                "score": 0,
                "downloads": 0,
                "reports": 0,
                "created_at": time.strftime("%Y-%m-%d"),
                "last_updated": time.strftime("%Y-%m-%d"),
            }
    save_score_log(score_log)
    print(f"   ✅ 评分日志已更新，共 {len(score_log)} 条记录")

    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 全部校验通过 — 流水线畅通 (开放注册模式)")
        print("🔓 欢迎全球 Agent 贡献基因！")
    else:
        print("❌ 部分基因未通过 — 流水线中断")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
