---
title: 校验脚本的运行时配置
source: session
created: 2026-08-12
tags: [meta, ci, validation]
status: current
---

`scripts/` 下的每个脚本都在 `# runtime: ...` 头里声明自己的运行时。
用这个矩阵决定哪些跑 CI、哪些只跑在开发机。

## ci-safe — 无需 raw 文件即可运行

| Script | What it checks | Notes |
|--------|----------------|-------|
| `wiki_check.py` | 必需文件、frontmatter、死链、log 头格式、index 引用 | 纯结构校验，无外部依赖 |
| `raw_manifest_check.py` | Manifest schema（通过 `raw_sources.meta.json`）、列、ID、status | 当 `PROJECT_RAW_ROOT` 未设时跳过 raw 文件存在性检查 |
| `untracked_raw_check.py` | 仓库里像 raw 资产但没进 manifest 的文件 | 扫描磁盘上所有东西 |
| `wiki_size_report.py` | Token 预算桶（绿/黄/红/紫）、最大页面 | 只读 `docs/wiki/` |
| `provenance_check.py --ci` | 每个非 session 页面都有 `source_hash` 字段 | 跳过实际 hash 对比 |

## dev-only — 需要 `PROJECT_RAW_ROOT` 指向真实 raw 文件

| Script | What it does | Why dev-only |
|--------|--------------|--------------|
| `provenance_check.py` (无 `--ci`) | 把 `source_hash` 跟实际 raw 文件对比 | 需要挂载 raw 文件 |
| `stale_report.py` | 报告 source 已变化的 wiki 页面 | 读 raw 的 mtime/hash |
| `delta_compile.py --write-drafts` | 为 stale/新增 raw 生成重编译草稿 | 写草稿 stub |
| `ingest_raw.py` | 遍历 raw 根目录、计算 hash、去重、更新 manifest | 会变更 manifest |
| `init_raw_root.py` | 创建 raw 目录布局 | 一次性初始化 |
| `version_check.py` | 轮询 GitHub 看有没有新的 LLM-wiki 版本 | 需要网络 |
| `export_memory_repo.py` | 把 wiki 镜像到另一个 repo | 写到 repo 之外 |

## CI workflow

`.github/workflows/wiki-lint.yml` 只跑 ci-safe 这一组。
把 dev-only 检查塞进去会因为 raw 文件没提交而失败。

如果想让 CI 跟真实 raw 文件对比，可以把它们挂载进 runner
（artifact upload、S3 sync 等等），在 job env 里设 `PROJECT_RAW_ROOT`。
别为了过 CI 就把 raw 文件提交进 Git——那会破坏 compile-first 契约。

## 本地 pre-commit 推荐

push 之前，本地跑完整集合：

```bash
python3 scripts/wiki_check.py
python3 scripts/raw_manifest_check.py
python3 scripts/untracked_raw_check.py
python3 scripts/wiki_size_report.py
python3 scripts/provenance_check.py
python3 scripts/stale_report.py
```
