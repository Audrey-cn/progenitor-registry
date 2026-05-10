# 🔮 Progenitor Registry · 星门索引

[English](README.md) | 中文

<p align="center">
  <img src="https://img.shields.io/badge/Status-活跃-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Gatekeeper-v2.0_开放注册-cyan?style=for-the-badge" />
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
- [🤝 贡献指南 (🔓 开放注册)](#-贡献指南--开放注册)
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

**面向贡献者**：将基因文件推送到 `genes/` 目录，星门守卫 CI 自动验证并注册——**无需审核！**

```
  贡献者                         Agent（网络）
  ──────                        ───────────
  提交 PR → genes/{CID}        查询能力名 "hello-world"
               ↓                    ↓
          星门守卫 CI           读取 .akashic_index.json
          ├─ L1 哈希校验            ↓
          ├─ L2 血脉检查         映射到 CID
          ├─ L3 创造者审核 (开放)    ↓
          ├─ L4 质量门槛         拉取 genes/{CID}
          └─ L5 安全扫描             ↓
               ↓                💾 本地执行（沙箱隔离）
          索引更新 ✅
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

### 面向贡献者 — 注册基因（无需审核！）

1. **Fork** 本仓库
2. **创建** 基因文件（包含 YAML 头），放入 `genes/` 目录：
   ```yaml
   # life_id: PGN@L1-G1-YOUR-GENE
   # creator: 你的名字
   # description: 这个基因的功能描述（至少10个字符）
   ---
   
   def main():
       # 你的基因代码（仅限 Python 标准库）
       pass
   ```
3. **重命名** 文件为 `{sha256}`（无扩展名）
4. **提交** Pull Request — CI 自动验证

---

## 🗂️ 项目结构

```
progenitor-registry/
├── .akashic_index.json          # 语义名 → CID 映射
├── .gene_score_log.json         # 基因评分日志
├── genes/                       # 基因载荷（SHA256 命名）
│   └── {sha256}                #   原始基因文件
├── .github/workflows/
│   ├── gatekeeper.yml          #   验证触发器
│   ├── gatekeeper.py           #   验证脚本（v2.0 开放）
│   └── daily_scan.yml          #   每日安全扫描
├── README.md
└── README_CN.md
```

---

## 🔐 已注册基因

<!-- REGISTRY TABLE START -->
| 基因名 | Lineage | Creator | SHA-256 | CID | 状态 |
|------|------|------|------|------|------|
| `hello-world` | PGN@L1-G1-HELLO-WORLD | Audrey | `4cf348cfdc6cfb50...` | `4cf348cfdc6cfb50...` | 🟢 已注册 |
| `hello-world-test` | PGN@L1-G1-HELLO-WORLD-TEST | Audrey | `4cf348cfdc6cfb50...` | `4cf348cfdc6cfb50...` | 🟢 已注册 |
<!-- REGISTRY TABLE END -->

---

## 🤝 贡献指南 (🔓 开放注册)

**欢迎来到开放的基因生态系统！** 任何人都可以为 Progenitor 注册表贡献基因——**无需审核！**

### 星门守卫 CI 验证 (v2.0)

当你提交基因时，星门守卫 CI 自动检查：

1. **L0 速率限制** — 每次 PR 最多 5 个基因，每人每天最多 20 个基因
2. **L1 哈希校验** — SHA-256 完整性验证
3. **L2 血脉验证** — `life_id` 必须以 `PGN@` 开头
4. **L3 创造者审核** — 🔓 **开放** — 任何人都可以贡献
5. **L4 质量门槛** — 最低质量标准（描述、文件大小限制）
6. **L5 安全扫描** — 检测危险代码模式

### 基因注册要求

| 字段 | 要求 |
|------|------|
| `cid` | 必须与 `expected_sha256` 匹配 |
| `life_id` | 必须以 `PGN@` 开头（例如 `PGN@L1-G1-YOUR-GENE`）|
| `creator` | 🔓 **开放** — 任何名字都可以 |
| `description` | 必须提供（至少 10 个字符）|
| 文件位置 | `genes/{sha256}` |

### 快速贡献步骤

1. **Fork** 本仓库
2. **创建** 包含 YAML 头的基因文件：
   ```yaml
   # life_id: PGN@L1-G1-YOUR-GENE
   # creator: 你的名字
   # description: 这个基因的功能描述（至少10个字符）
   ---
   
   def main():
       # 你的基因代码（仅限 Python 标准库）
       pass
   ```
3. **计算** 基因文件的 SHA-256 哈希
4. **重命名** 文件为 `{sha256}`（无扩展名）
5. **提交** Pull Request — CI 自动验证

### 基因质量标准

**✅ 允许：**
- 仅使用 Python 标准库（零第三方依赖）
- 功能性的基因代码
- 清晰的描述

**❌ 禁止：**
- `eval()`、`exec()`、`os.system()`、`subprocess`
- 第三方库：`requests`、`pandas`、`numpy`、`BeautifulSoup`
- 恶意代码
- 垃圾/无意义内容
- 侵犯版权的材料

**文件大小限制：** 每个基因文件最大 1MB

**命名规范：** `PGN@{Level}-{GeneNumber}-{GENE-NAME}`
- 示例：`PGN@L1-G1-CODE-REVIEWER`

### 安全说明

所有基因在每个 Agent 的本地机器上都以**沙箱环境**（端粒守卫 TelomereGuard）执行。本地 Progenitor 引擎在执行前提供额外的 L1-L5 安全验证。

---

## 📜 许可证

本项目基于 **MIT 许可证** 发布。

---

*星门索引 · Progenitor 协议 · SHA-256 不可变 · 🔓 开放生态系统*
