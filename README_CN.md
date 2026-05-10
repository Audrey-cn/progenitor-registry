# 🔮 Progenitor Registry · 星门索引

[English](README.md) | 中文

<p align="center">
  <img src="https://img.shields.io/badge/Status-活跃-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Gatekeeper-自动验证-purple?style=for-the-badge" />
</p>

---

> *"星门索引——记录所有变异的地方。"*
> —— Audrey · 001X

---

## 📑 目录

- [🔮 生态矩阵](#-生态矩阵)
- [📖 功能](#-功能)
- [🚀 快速开始](#-快速开始)
- [🗂️ 项目结构](#️-项目结构)
- [🔐 已注册基因](#-已注册基因)
- [🤝 贡献指南](#-贡献指南)
- [📜 许可证](#-许可证)

---

## 🔮 生态矩阵

| 仓库 | 角色 | 链接 |
|------|------|------|
| 🧬 **Protocol** | 始源引擎 | [Audrey-cn/progenitor-protocol](https://github.com/Audrey-cn/progenitor-protocol) |
| 🔮 **Registry** | 基因索引（当前页面） | [Audrey-cn/progenitor-registry](https://github.com/Audrey-cn/progenitor-registry) |

---

## 📖 功能

本注册表是 Progenitor v2.18 生态系统的**权威基因索引**，服务两类用户：

**面向 AI Agent**：`.akashic_index.json` 文件将语义基因名（如 "code-reviewer"）映射到内容标识符（CID）。当 Agent 需要某个能力，查询此索引即可定位基因。

**面向贡献者**：将基因文件推送到 `genes/` 目录，在索引中注册，星门守卫 CI 会自动验证谱系、创造者身份和 SHA-256 数据完整性。

```
  贡献者                         Agent（网络）
  ──────                        ───────────
  推送 Gene → genes/{CID}       查询能力名 "hello-world"
               ↓                    ↓
          星门守卫 CI           读取 .akashic_index.json
          ├─ L1 哈希校验            ↓
          ├─ L2 血脉检查         映射到 CID
          └─ L3 创造者审核          ↓
               ↓                拉取 genes/{CID}
          索引更新 ✅             💾 本地执行
```

---

## 🚀 快速开始

### 面向 AI Agent — 查询基因

```python
from akashic.compass import load_index, resolve_cid_by_name

# 加载注册表索引（自动从 GitHub Raw 拉取）
index = load_index()

# 将能力名解析为 CID
cid = resolve_cid_by_name("hello-world", index)
# → "4cf348cfdc6cfb50fd7bdb56a5614f76f41c7a1dacbc8194d6a9ce2a9da2c9f3"

# 然后通过阿卡夏受体摄入基因
from akashic.receptor import phagocytize_gene
gene = phagocytize_gene(gene_cid=cid)
```

### 面向贡献者 — 注册基因

1. **Fork** 本仓库
2. **放置** 你的基因文件到 `genes/{内容的sha256}`
3. **添加** 条目到 `.akashic_index.json`：
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
4. **推送** — 星门守卫 CI 自动验证你的基因

---

## 🗂️ 项目结构

```
progenitor-registry/
├── .akashic_index.json    # 语义名 → CID 映射
├── genes/                 # 基因载荷（CID 命名）
│   └── {sha256}           #   原始基因文件
├── .github/workflows/      # CI 自动验证
│   ├── gatekeeper.yml     #   验证触发器
│   └── gatekeeper.py      #   验证脚本（零依赖）
├── README.md
└── README_CN.md
```

---

## 🔐 已注册基因

<!-- REGISTRY TABLE START -->
| 基因名 | 谱系 | 创造者 | CID | 状态 |
|--------|------|--------|-----|------|
| `hello-world` | PGN@L1-G1-HELLO-WORLD | Audrey | `4cf348...` | 🟢 活跃 |
| `hello-world-test` | PGN@L1-G1-HELLO-WORLD-TEST | Audrey | `4cf348...` | 🟢 活跃 |
<!-- REGISTRY TABLE END -->

---

## 🤝 贡献指南

### 星门守卫 CI 验证

当你提交基因时，星门守卫 CI 自动检查：

1. **L1 哈希校验** — SHA-256 完整性验证
2. **L2 血脉验证** — `life_id` 必须以 `PGN@` 开头
3. **L3 创造者审核** — 创造者须在 `ALLOWED_CREATORS` 中

### 基因注册要求

| 字段 | 要求 |
|------|------|
| `cid` | 必须与 `expected_sha256` 匹配 |
| `life_id` | 必须以 `PGN@` 开头 |
| `creator` | 必须在注册表白名单中 |
| 文件位置 | `genes/{sha256}` |

---

## 📜 许可证

本项目基于 **MIT 许可证** 发布。

---

*星门索引 · Progenitor 协议 · SHA-256 不可变*
