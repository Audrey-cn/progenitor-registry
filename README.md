# 🔮 Progenitor Registry

[中文](README_CN.md) | English

<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Gatekeeper-Auto_Validate-purple?style=for-the-badge" />
</p>

---

> *"The Stargate Index — where all mutations are recorded."*
> — Audrey · 001X

---

## 📑 Table of Contents

- [🔮 Ecosystem Matrix](#-ecosystem-matrix)
- [📖 What It Does](#-what-it-does)
- [🚀 Quick Start](#-quick-start)
- [🗂️ Project Structure](#️-project-structure)
- [🔐 Registered Genes](#-registered-genes)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)

---

## 🔮 Ecosystem Matrix

| Repository | Role | Link |
|------------|------|------|
| 🧬 **Protocol** | Origin Engine | [Audrey-cn/progenitor-protocol](https://github.com/Audrey-cn/progenitor-protocol) |
| 🔮 **Registry** | Gene Index (you are here) | [Audrey-cn/progenitor-registry](https://github.com/Audrey-cn/progenitor-registry) |

---

## 📖 What It Does

This registry is the **authoritative gene index** for the Progenitor v2.18 ecosystem. It serves two audiences:

**For AI Agents**: The `.akashic_index.json` file maps semantic gene names (like "code-reviewer") to Content IDs (CIDs). When an agent needs a capability, it queries this index to find the gene.

**For Contributors**: Push a gene file to `genes/`, add its entry to the index, and the Gatekeeper CI automatically validates lineage, creator identity, and SHA-256 integrity.

```
  Contributor                    Agent (network)
  ────────                       ──────────────
  Push Gene → genes/{CID}         Query "hello-world"
               ↓                      ↓
          Gatekeeper CI           Read .akashic_index.json
          ├─ L1 Hash Check            ↓
          ├─ L2 Lineage Verify     Map to CID
          └─ L3 Creator Check         ↓
               ↓                   Pull genes/{CID}
          Index Updated ✅         💾 Execute Locally
```

---

## 🚀 Quick Start

### For AI Agents — Query a Gene

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

### For Contributors — Register a Gene

1. **Fork** this repository
2. **Place** your gene file in `genes/{sha256_of_content}`
3. **Add** an entry to `.akashic_index.json`:
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
4. **Push** — The Gatekeeper CI automatically validates your gene

---

## 🗂️ Project Structure

```
progenitor-registry/
├── .akashic_index.json    # Semantic name → CID mapping
├── genes/                 # Gene payloads (CID-named)
│   └── {sha256}           #   Raw gene files
├── .github/workflows/      # CI auto-validation
│   ├── gatekeeper.yml     #   Validation trigger
│   └── gatekeeper.py      #   Validation script (zero-dependency)
├── README.md
└── README_CN.md
```

---

## 🔐 Registered Genes

<!-- REGISTRY TABLE START -->
| 基因名 | Lineage | Creator | SHA-256 (Trinity) | CID | 状态 |
|------|------|------|------|------|------|
| `hello-world` |  | Audrey | `4cf348cfdc6cfb50...` | `4cf348cfdc6cfb50...` | 🟢 已注册 |
| `hello-world-test` |  | Audrey | `4cf348cfdc6cfb50...` | `4cf348cfdc6cfb50...` | 🟢 已注册 |
<!-- REGISTRY TABLE END -->

---

## 🤝 Contributing

### Gatekeeper CI Validation

When you submit a gene, the Gatekeeper CI automatically checks:

1. **L1 Hash Check** — SHA-256 integrity verification
2. **L2 Lineage Verify** — `life_id` must start with `PGN@`
3. **L3 Creator Check** — Creator must be in `ALLOWED_CREATORS`

### Gene Registration Requirements

| Field | Requirement |
|-------|-------------|
| `cid` | Must match `expected_sha256` |
| `life_id` | Must start with `PGN@` |
| `creator` | Must be in registry's allowlist |
| File location | `genes/{sha256}` |

---

## 📜 License

This project is released under the **MIT License**.

---

*Stargate Index · Progenitor Protocol · SHA-256 Immutable*
