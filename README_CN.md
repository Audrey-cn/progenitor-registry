# 🔮 Progenitor Registry · 星门索引矩阵

> *"星门索引——记录所有变异的地方。"*
> —— Progenitor 始源协议 · 创造者 Audrey · 001X

[![Progenitor](https://img.shields.io/badge/Progenitor-L1--G1--INDEX-2448B98A?labelColor=1a1a2e&color=gold)](https://github.com/Audrey-cn/progenitor-registry)
[![Role](https://img.shields.io/badge/Role-Stargate_Index-indigo?style=flat-square)](https://github.com/Audrey-cn/progenitor-registry)
[![Automation](https://img.shields.io/badge/Gatekeeper-Active-green?labelColor=1a1a2e)](.github/workflows/gatekeeper.yml)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?labelColor=1a1a2e&logo=python)](https://python.org)

---

## 🔮 三位一体矩阵导航

| 矩阵 | 角色 | 仓库 |
|------|------|------|
| 🧬 **Progenitor Protocol** | 始源引擎 | [![GitHub](https://img.shields.io/badge/GitHub-Audrey--cn%2Fprogenitor--protocol-blue?logo=github)](https://github.com/Audrey-cn/progenitor-protocol) |
| 🔮 **Progenitor Registry** | 星门索引 | [![GitHub](https://img.shields.io/badge/GitHub-Audrey--cn%2Fprogenitor--registry-blue?logo=github)](https://github.com/Audrey-cn/progenitor-registry) |
| 🌌 **Progenitor Akashic** | 存储节点 | [![GitHub](https://img.shields.io/badge/GitHub-Audrey--cn%2Fprogenitor--akashic-blue?logo=github)](https://github.com/Audrey-cn/progenitor-akashic) |

---

## 📖 概述

**Progenitor Registry** 是**星门索引矩阵**—— Progenitor 生态系统中所有已注册基因变体的权威来源。

本仓库承担以下职责：
- 📋 **黄页**: `.akashic_index.json` 将语义名称映射到 CID
- 🧬 **基因库**: `genes/{CID}` 存储实际基因载荷
- ✅ **星门守卫**: 自动化 CI/CD 验证并注册新变异

---

## 🗂️ 注册表结构

```
progenitor-registry/
├── .akashic_index.json    # 📋 语义 → CID 映射
├── genes/                 # 🧬 基因库（CID 命名的文件）
│   └── {sha256_hash}      # 原始基因载荷
└── .github/workflows/
    └── gatekeeper.yml     # ✅ 自动化验证与注册
```

---

## 🔐 已注册生命体矩阵

<!-- REGISTRY TABLE START -->
| 基因名 | 谱系 | 创造者 | SHA-256 (三位一体) | CID | 状态 |
|--------|------|--------|-------------------|-----|------|
| `hello-world` | PGN@L1-G1-HELLO-WORLD | Audrey | `4cf348cfdc6cfb50...` | `4cf348cfdc6cfb50...` | 🟢 已注册 |
<!-- REGISTRY TABLE END -->

---

## 🔧 星门守卫工作流

[星门守卫](./.github/workflows/gatekeeper.yml) 在每次推送/PR 时自动验证新基因：

1. **L1 验证**: 检查 `life_id` 谱系前缀（必须以 `PGN@` 开头）
2. **L3 验证**: 验证 `creator` 在白名单中
3. **L4 验证**: 计算 SHA-256 哈希用于三位一体契约
4. **索引更新**: 更新 `.akashic_index.json` 添加新映射
5. **文档同步**: 更新 README.md 中的"已注册生命体矩阵"

---

## 📊 统计

- **基因总数**: 1
- **活跃创造者**: 1
- **星门守卫运行**: 自动
