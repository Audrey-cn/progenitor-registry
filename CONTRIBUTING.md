# Contributing a Gene 🧬

English | [中文](#贡献一个基因-中文)

Anyone can contribute a gene. The Gatekeeper CI runs checks L0–L6 automatically on every PR —
no approval gate, no waiting on humans. Signing is optional but recommended (it upgrades your
gene's `trust_state`).

## Flow (5 minutes)

**0. Prerequisites** — Python 3.10+, git. Optional (for signing): a creator identity.

**1. Scaffold**

```bash
python tools/gene_scaffold.py --name markdown-parser \
    --creator YourName \
    --description "Parse markdown into structured sections"
```

**2. Content-address** — rename the scaffolded file to its printed SHA-256 and move it into `genes/`:

```bash
mv markdown-parser.py genes/<sha256>
```

**3. (Recommended) Sign your gene** — generate a creator identity once, keep the file private:

```bash
python tools/sign_gene.py --gen-identity your-name     # writes your-name-identity.json
```

Then sign (reads `CREATOR_PRIVATE_KEY_JSON`):

```bash
CREATOR_PRIVATE_KEY_JSON="$(cat your-name-identity.json)" python tools/sign_gene.py genes/<sha256>
```

This writes `signatures/<sha256>.sig`. **In your PR, include your public identity** (the
`public_key` / `node_id` fields from your identity file — never the private key). A maintainer
adds it to `policy/trusted_keys.json`, and your gene's `trust_state` upgrades to
`creator-signed:YourName`. Until then it shows `creator-signature-pending-review` — that is
normal for a first PR. Never signed? Your gene is still accepted as `registry_verified`.

**4. Local check** (optional but kind):

```bash
python -m pytest tests/ -q          # 50 tests, ~0.4s
python .github/workflows/gatekeeper.py --scan-only
```

**5. Open the PR.** The Gatekeeper runs L0 rate-limit → L1 lineage → L2 content-address →
L3 creator → L4 quality → L5 security scan → L6 capability honesty, then updates
`.akashic_index.json` automatically.

## Rules of the road

- A gene **declares what it needs** (`purity`, `grants`) and returns **advisory** results —
  hosts decide, nothing executes on their behalf (Gene Contract v2, docs in
  [progenitor-protocol](https://github.com/Audrey-cn/progenitor-protocol)).
- Every external byte is hostile to everyone else: content-addressing + signature is the trust
  root, not people.
- No credentials, no secrets, no network calls inside `pure` genes.

---

# 贡献一个基因（中文）

任何人都可以贡献基因。Gatekeeper CI 会对每个 PR 自动执行 L0–L6 检查——无需人工审批，无需等待。
签名可选但强烈推荐（会升级基因的 `trust_state`）。

## 流程（5 分钟）

**1. 脚手架**

```bash
python tools/gene_scaffold.py --name markdown-parser \
    --creator 你的名字 \
    --description "基因功能描述（至少10个字符）"
```

**2. 内容寻址**——把生成的文件重命名为它打印出的 SHA-256，放进 `genes/`：

```bash
mv markdown-parser.py genes/<sha256>
```

**3.（推荐）签名**——生成创造者身份（只需一次，文件保密）：

```bash
python tools/sign_gene.py --gen-identity your-name     # 生成 your-name-identity.json
```

然后签名（读取 `CREATOR_PRIVATE_KEY_JSON`）：

```bash
CREATOR_PRIVATE_KEY_JSON="$(cat your-name-identity.json)" python tools/sign_gene.py genes/<sha256>
```

生成 `signatures/<sha256>.sig`。**PR 中请附上你的公开身份**（身份文件里的 `public_key` /
`node_id` 字段——绝不提交私钥）。维护者会把它加入 `policy/trusted_keys.json`，你的基因将升级为
`creator-signed:你的名字`。在此之前显示 `creator-signature-pending-review`——首次 PR 的正常状态。
不签名也完全可以接受，状态为 `registry_verified`。

**4. 本地自检（可选）**：`python -m pytest tests/ -q` 与
`python .github/workflows/gatekeeper.py --scan-only`。

**5. 提交 PR**——Gatekeeper 自动跑完 L0 限速 → L1 血脉 → L2 内容寻址 → L3 创造者 → L4 质量 →
L5 安全扫描 → L6 能力诚实性，并自动更新 `.akashic_index.json`。

## 铁律

- 基因**声明所需**（`purity`/`grants`），输出仅为**建议**——宿主决定，绝不代替宿主执行（Gene Contract v2）。
- 内容寻址 + 签名是信任根，不是人。
- 禁止凭据/密钥/网络调用进 `pure` 基因。
