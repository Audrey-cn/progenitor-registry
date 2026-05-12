# 🔮 Progenitor Registry

[中文](README_CN.md) | English

<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Gatekeeper-v2.0_Open-cyan?style=for-the-badge" />
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
- [🤝 Contributing (🔓 Open Registration)](#-contributing--open-registration)
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

**For AI Agents**: The `.akashic_index.json` file maps semantic gene names (like "code-reviewer") to `content_sha256`, the primary content identity. CID, GitHub Raw, registry paths, and peer URLs are transport hints that must be verified against the hash.

**For Contributors**: Push a gene file to `genes/`, and the Gatekeeper CI automatically validates and registers it — **no approval required!**

```
  Contributor                    Agent (network)
  ────────                       ──────────────
  Submit PR → genes/{CID}         Query "hello-world"
                ↓                      ↓
           Gatekeeper CI           Read .akashic_index.json
           ├─ L1 Hash Check            ↓
           ├─ L2 Lineage Verify     Map to CID
           ├─ L3 Creator Check (Open)   ↓
           ├─ L4 Quality Gate      Pull genes/{CID}
           └─ L5 Security Scan         ↓
                ↓                   💾 Execute Locally (Sandboxed)
           Index Updated ✅
```

---

## 🚀 Quick Start

### For AI Agents — Query a Gene

```python
from akashic.compass import load_index, resolve_content_by_name

# Load the registry index (auto-fetches from GitHub Raw)
index = load_index()

# Resolve a capability name to its content identity
content_sha256, transport_hint = resolve_content_by_name("hello-world", index)
# → "4cf348cfdc6cfb50fd7bdb56a5614f76f41c7a1dacbc8194d6a9ce2a9da2c9f3"

# Then ingest the gene using the Akashic receptor
from akashic.receptor import phagocytize_gene
gene = phagocytize_gene(content_sha256=content_sha256, transport_hint=transport_hint)
```

### For Contributors — Register a Gene (No Approval Needed!)

1. **Fork** this repository
2. **Create** your gene file with YAML header in `genes/`:
   ```yaml
   # life_id: PGN@L1-G1-YOUR-GENE
   # creator: YourName
   # description: What this gene does (at least 10 characters)
   ---
   
   def main():
       # Your gene code here (Python standard library only)
       pass
   ```
3. **Rename** file to `{sha256}` (no extension)
4. **Submit** Pull Request — CI will validate automatically

---

## 🗂️ Project Structure

```
progenitor-registry/
├── .akashic_index.json          # Semantic name → CID mapping
├── .gene_score_log.json         # Gene reputation scores
├── genes/                       # Gene payloads (SHA256-named)
│   └── {sha256}                #   Raw gene files
├── .github/workflows/
│   ├── gatekeeper.yml          #   Validation trigger
│   ├── gatekeeper.py           #   Validation script (v2.0 Open)
│   └── daily_scan.yml          #   Daily security scan
├── README.md
└── README_CN.md
```

---

## 🔐 Registered Genes

<!-- REGISTRY TABLE START -->
| Capability | Lineage | Creator | SHA-256 | CID | Status |
|------|------|------|------|------|------|
| `code-reviewer` | PGN@L1-G3-CODE-REVIEWER | Audrey | `3a1bd515d22c38ed...` | `3a1bd515d22c38ed...` | Registered |
| `hello-world` |  |  | `836769a791a8d504...` | `836769a791a8d504...` | Registered |
| `hello-world-test` | PGN@L1-G1-HELLO-WORLD-TEST | Audrey | `836769a791a8d504...` | `836769a791a8d504...` | Registered |
| `json-toolkit` | PGN@L1-G5-JSON-TOOLKIT | Audrey | `5fc18c9d64678272...` | `5fc18c9d64678272...` | Registered |
| `log-parser` | PGN@L1-G4-LOG-PARSER | Audrey | `bc000444ec523efd...` | `bc000444ec523efd...` | Registered |
| `test-gene` | PGN@L1-G2-TEST-GENE | Audrey | `0c0e17638a1dffc5...` | `0c0e17638a1dffc5...` | Registered |
<!-- REGISTRY TABLE END -->

---

## 🤝 Contributing (🔓 Open Registration)

**Welcome to the open gene ecosystem!** Anyone can contribute genes to the Progenitor Registry — **no approval required!**

### Gatekeeper CI Validation (v2.0)

When you submit a gene, the Gatekeeper CI automatically checks:

1. **L0 Rate Limit** — Max 5 genes per PR, 20 genes per creator per day
2. **L1 Hash Check** — SHA-256 integrity verification
3. **L2 Lineage Verify** — `life_id` must start with `PGN@`
4. **L3 Creator Check** — 🔓 **OPEN** — Anyone can contribute
5. **L4 Quality Gate** — Minimum quality standards (description, size limits)
6. **L5 Security Scan** — Detects dangerous code patterns

### Gene Registration Requirements

| Field | Requirement |
|-------|-------------|
| `content_sha256` | Must match the SHA-256 of the gene payload |
| `cid` | Legacy/transport alias; must match `content_sha256` while present |
| `life_id` | Must start with `PGN@` (e.g., `PGN@L1-G1-YOUR-GENE`) |
| `creator` | 🔓 **OPEN** — Any name accepted |
| `description` | Required (at least 10 characters) |
| File location | `genes/{sha256}` |

### Quick Contribution Steps

1. **Fork** this repository
2. **Create** your gene file with YAML header:
   ```yaml
   # life_id: PGN@L1-G1-YOUR-GENE
   # creator: YourName
   # description: What this gene does (at least 10 characters)
   ---
   
   def main():
       # Your gene code here (Python standard library only)
       pass
   ```
3. **Calculate** SHA-256 hash of your gene file
4. **Rename** file to `{sha256}` (no extension)
5. **Submit** Pull Request — CI will validate automatically

### Gene Quality Standards

**✅ Allowed:**
- Python standard library only (zero third-party dependencies)
- Functional gene code
- Clear descriptions

**❌ Forbidden:**
- `eval()`, `exec()`, `os.system()`, `subprocess`
- Third-party libraries: `requests`, `pandas`, `numpy`, `BeautifulSoup`
- Malicious code
- Spam/garbage content
- Copyrighted material

**Size limit:** Max 1MB per gene file

**Naming convention:** `PGN@{Level}-{GeneNumber}-{GENE-NAME}`
- Example: `PGN@L1-G1-CODE-REVIEWER`

### Security Notes

All genes are executed in a **sandboxed environment** (TelomereGuard) on each Agent's local machine. The local Progenitor engine provides additional L1-L5 security validation before execution.

---

## 📜 License

This project is released under the **MIT License**.

---

*Stargate Index · Progenitor Protocol · SHA-256 Immutable · 🔓 Open Ecosystem*
