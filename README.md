# 🔮 Progenitor Registry

[中文](README_CN.md) | English

> *"The Stargate Index — where all mutations are recorded."*
> — Audrey · 001X

[![Progenitor](https://img.shields.io/badge/Progenitor-L1--G1--INDEX-2448B98A?labelColor=1a1a2e&color=gold)](https://github.com/Audrey-cn/progenitor-registry)
[![Gatekeeper](https://img.shields.io/badge/Gatekeeper-Active-green?labelColor=1a1a2e)](.github/workflows/gatekeeper.yml)

---

## 🔮 Ecosystem Matrix

| Repository | Role | Link |
|------------|------|------|
| 🧬 **Protocol** | Origin Engine | [Audrey-cn/progenitor-protocol](https://github.com/Audrey-cn/progenitor-protocol) |
| 🔮 **Registry** | Gene Index (you are here) | [Audrey-cn/progenitor-registry](https://github.com/Audrey-cn/progenitor-registry) |

---

## 📖 What It Does

This registry is the **authoritative gene index** for the Progenitor v2.18 ecosystem. It serves two audiences:

**For AI Agents**: The `.akashic_index.json` file maps semantic gene names (like "code-reviewer") to Content IDs (CIDs). When an agent needs a capability, it queries this index to find the gene. Works with the Progenitor Protocol's dual-index resolution (legacy semantic names + IPFS CIDs).

**For Contributors**: Push a gene file to `genes/`, add its entry to the index, and the Gatekeeper CI automatically validates lineage (`PGN@` prefix), creator identity (`ALLOWED_CREATORS`), and SHA-256 integrity — mirroring the L1–L3 layers of the Progenitor Crucible audit.

```
  贡献者                         Agent (网络)
  ──────                        ───────────
  推送 Gene → genes/{CID}       查询能力名 "hello-world"
               ↓                    ↓
          Gatekeeper CI         读取 .akashic_index.json
          ├─ L1 哈希校验            ↓
          ├─ L2 血脉检查         映射到 CID
          └─ L3 创造者审核          ↓
               ↓                拉取 genes/{CID}
          索引更新 ✅             💾 本地执行
```

---

## 🗂️ Structure

```
progenitor-registry/
├── .akashic_index.json    # 语义名 → CID 映射
├── genes/                 # 基因载荷（CID 命名）
│   └── {sha256}           #   原始基因文件
├── .github/workflows/     # CI 自动验证
│   ├── gatekeeper.yml     #   验证触发器
│   └── gatekeeper.py      #   验证脚本（零依赖）
├── README.md
└── README_CN.md
```

---

## 🤖 For AI Agents — How To Query

```python
from akashic.compass import load_index, resolve_cid_by_name

# Load the registry index (auto-fetches from GitHub Raw)
index = load_index()

# Resolve a capability name to its CID
cid = resolve_cid_by_name("hello-world", index)
# → "4cf348cfdc6cfb50fd7bdb56a5614f76f41c7a1dacbc8194d6a9ce2a9da2c9f3"

# Then ingest the gene using the Akashic receptor
from akashic.receptor import phagocytize_gene
gene = phagocytize_gene(gene_cid=cid)
```

---

## 🔧 For Contributors — How To Register a Gene

1. **Fork** this repository
2. Place your gene file in `genes/{sha256_of_content}`
3. Add an entry to `.akashic_index.json`:
   ```json
   {
     "your-gene-name": {
       "cid": "sha256_of_content",
       "expected_sha256": "sha256_of_content",
       "life_id": "PGN@L1-G1-YOUR-GENE",
       "creator": "YourName",
       "registered_at": "auto"
     }
   }
   ```
4. **Push** — The Gatekeeper CI automatically:
   - Validates `life_id` starts with `PGN@`
   - Verifies SHA-256 integrity
   - Checks creator identity
   - Updates the registered entities table below

---

## 🔐 Registered Genes

<!-- REGISTRY TABLE START -->
| 基因名 | Lineage | Creator | SHA-256 (Trinity) | CID | 状态 |
|------|------|------|------|------|------|
| `hello-world` |  | Audrey | `4cf348cfdc6cfb50...` | `4cf348cfdc6cfb50...` | 🟢 已注册 |
| `hello-world-test` |  | Audrey | `4cf348cfdc6cfb50...` | `4cf348cfdc6cfb50...` | 🟢 已注册 |
<!-- REGISTRY TABLE END -->

---

*Stargate Index · Progenitor Protocol · SHA-256 Immutable*
