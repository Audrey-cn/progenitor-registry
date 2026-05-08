# 🔮 Progenitor Registry · 星门索引矩阵

[English](README.md) | 中文

> *"星门索引——记录所有变异的地方。"*
> —— Audrey · 001X

[![Progenitor](https://img.shields.io/badge/Progenitor-L1--G1--INDEX-2448B98A?labelColor=1a1a2e&color=gold)](https://github.com/Audrey-cn/progenitor-registry)
[![Gatekeeper](https://img.shields.io/badge/Gatekeeper-Active-green?labelColor=1a1a2e)](.github/workflows/gatekeeper.yml)

---

## 🔮 生态矩阵

| 仓库 | 角色 | 链接 |
|------|------|------|
| 🧬 **Protocol** | 始源引擎 | [Audrey-cn/progenitor-protocol](https://github.com/Audrey-cn/progenitor-protocol) |
| 🔮 **Registry** | 基因索引（当前页面） | [Audrey-cn/progenitor-registry](https://github.com/Audrey-cn/progenitor-registry) |
| 🌌 **Akashic** | 存储节点 | [Audrey-cn/progenitor-akashic](https://github.com/Audrey-cn/progenitor-akashic) |

---

## 📖 功能

本注册表是 Progenitor v2.18 生态系统的**权威基因索引**，服务两类用户：

**面向 AI Agent**：`.akashic_index.json` 文件将语义基因名（如 "code-reviewer"）映射到内容标识符（CID）。当 Agent 需要某个能力，查询此索引即可定位基因。支持 Progenitor Protocol 的双索引解析（语义名 + IPFS CID 兼容）。

**面向贡献者**：将基因文件推送到 `genes/` 目录，在索引中注册，星门守卫 CI 会自动验证谱系（`PGN@` 前缀）、创造者身份（`ALLOWED_CREATORS`）和 SHA-256 数据完整性——与 Progenitor 熔炉审计的 L1–L3 层对应。

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
          索引更新 ✅             本地执行 💾
```

---

## 🗂️ 结构

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

## 🤖 致 AI Agent —— 如何查询

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

---

## 🔧 致贡献者 —— 如何注册基因

1. **Fork** 本仓库
2. 将基因文件放入 `genes/{内容的sha256}`
3. 在 `.akashic_index.json` 中添加条目：
   ```json
   {
     "你的基因名": {
       "cid": "内容的sha256",
       "expected_sha256": "内容的sha256",
       "life_id": "PGN@L1-G1-你的基因",
       "creator": "你的名字",
       "registered_at": "auto"
     }
   }
   ```
4. **推送** — 星门守卫 CI 自动：
   - 验证 `life_id` 以 `PGN@` 开头
   - 校验 SHA-256 完整性
   - 检查创造者身份
   - 更新下方的已注册基因表

---

## 🔐 已注册基因

<!-- REGISTRY TABLE START -->
| 基因名 | 谱系 | 创造者 | CID | 状态 |
|--------|------|--------|-----|------|
| `hello-world` | PGN@L1-G1-HELLO-WORLD | Audrey | `4cf348...` | 🟢 活跃 |
| `hello-world-test` | PGN@L1-G1-HELLO-WORLD-TEST | Audrey | `4cf348...` | 🟢 活跃 |
<!-- REGISTRY TABLE END -->

---

*星门索引 · Progenitor 协议 · SHA-256 不可变*
