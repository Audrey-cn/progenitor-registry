# 🔮 Progenitor Registry

> *"The Stargate Index — where all mutations are recorded."*
> — Progenitor Primordial Protocol · Creator Audrey · 001X

[![Progenitor](https://img.shields.io/badge/Progenitor-L1--G1--INDEX-2448B98A?labelColor=1a1a2e&color=gold)](https://github.com/Audrey-cn/progenitor-registry)
[![Role](https://img.shields.io/badge/Role-Stargate_Index-indigo?style=flat-square)](https://github.com/Audrey-cn/progenitor-registry)
[![Automation](https://img.shields.io/badge/Gatekeeper-Active-green?labelColor=1a1a2e)](.github/workflows/gatekeeper.yml)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?labelColor=1a1a2e&logo=python)](https://python.org)

---

## 🔮 Trinity Matrix Navigation

| Matrix | Role | Repository |
|--------|------|------------|
| 🧬 **Progenitor Protocol** | Origin Engine | [![GitHub](https://img.shields.io/badge/GitHub-Audrey--cn%2Fprogenitor--protocol-blue?logo=github)](https://github.com/Audrey-cn/progenitor-protocol) |
| 🔮 **Progenitor Registry** | Stargate Index | [![GitHub](https://img.shields.io/badge/GitHub-Audrey--cn%2Fprogenitor--registry-blue?logo=github)](https://github.com/Audrey-cn/progenitor-registry) |
| 🌌 **Progenitor Akashic** | Storage Node | [![GitHub](https://img.shields.io/badge/GitHub-Audrey--cn%2Fprogenitor--akashic-blue?logo=github)](https://github.com/Audrey-cn/progenitor-akashic) |

---

## 📖 Overview

**Progenitor Registry** is the **Stargate Index Matrix** — the authoritative source for all registered gene variants within the Progenitor ecosystem.

This repository serves as:
- 📋 **Yellow Pages**: `.akashic_index.json` maps semantic names to CIDs
- 🧬 **Gene Vault**: `genes/{CID}` stores the actual gene payloads
- ✅ **Gatekeeper**: Automated CI/CD validates and registers new mutations

---

## 🗂️ Registry Structure

```
progenitor-registry/
├── .akashic_index.json    # 📋 Semantic → CID mapping
├── genes/                 # 🧬 Gene vault (CID-named files)
│   └── {sha256_hash}      # Raw gene payload
└── .github/workflows/
    └── gatekeeper.yml     # ✅ Automated validation & registration
```

---

## 🔐 Registered Entities Matrix

<!-- REGISTRY TABLE START -->
| 基因名 | Lineage | Creator | SHA-256 (Trinity) | CID | 状态 |
|------|------|------|------|------|------|
| `hello-world` |  | Audrey | `4cf348cfdc6cfb50...` | `4cf348cfdc6cfb50...` | 🟢 已注册 |
| `hello-world-test` |  | Audrey | `4cf348cfdc6cfb50...` | `4cf348cfdc6cfb50...` | 🟢 已注册 |
<!-- REGISTRY TABLE END -->

---

## 🔧 Gatekeeper Workflow

The [Gatekeeper](./.github/workflows/gatekeeper.yml) automatically validates new genes on every push/PR:

1. **L1 Validation**: Checks `life_id` lineage prefix (must start with `PGN@`)
2. **L3 Validation**: Verifies `creator` is in the whitelist
3. **L4 Validation**: Computes SHA-256 hash for the Trinity contract
4. **Index Update**: Updates `.akashic_index.json` with new mappings
5. **Documentation**: Syncs the "Registered Entities Matrix" in README.md

---

## 📊 Statistics

- **Total Genes**: 1
- **Active Creators**: 1
- **Gatekeeper Runs**: Automated
