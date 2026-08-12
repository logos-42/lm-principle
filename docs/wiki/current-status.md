---
title: lm_principle 当前状态
source: session
created: 2026-08-12
tags: [status]
status: current
---

## 已支持

- Lean 4 v4.21.0 工具链（elan），mathlib rev 308445d（lakefile git 锁定，2025-06-30 / v4.21.0 时代）
- mathlib 按需 olean：`lake exe cache get <Module>` 只下载 import 闭包，不拉全量（.lake 当前 ≈ 870M，其中源码 575M）
- 项目 `lake build` 通过；LmPrinciple.Basic 编译成功
- 实测 mathlib 可用：`#check AddMonoid`、`by omega`、`by rfl` 均通过

## 未支持 / 风险

- mathlib 目前只按需下载了 `Mathlib.Algebra.Group.Defs` 闭包（63 个 olean）；import 新模块前必须 `lake exe cache get <新模块>`，否则 lake 会本地编译（极慢）
- `lean-toolchain` 若被改回 v4.34.0-rc1 会立即编译失败（Batteries 语法错误）；VSCode 打开该文件时别保存旧内容
- `scripts/setup_mathlib.sh` 是 Windows 专用（curl schannel 修复 + 强制 v4.21.0），macOS 不要执行
- v4.34.0-rc1 工具链（537MB）已 uninstall 回收空间
