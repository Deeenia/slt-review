# SLT Review

[中文](README.md) | [English](README.en.md)

一个成本与效率优先的 Codex Skill。它只解决一个问题：避免实现模型审查自己的代码。

```text
当前 Sol：一次布局
    ↓
Luna：一次实现与验证
    ↓
Fresh Terra：一次独立只读审查
    ↓
Sol：直接汇总，不复验
```

正常成功路径只有两次子智能体调用：一次 Luna、一次 Terra。

## 设计边界

- Sol 负责理解需求、确定范围，并写入简短的 `.slt-review/boundary.md`。
- Luna 读取 boundary，完成全部实现，只运行一次最相关的验证。
- Fresh Terra 只读审查 Luna 修改的确切文件，默认不重复运行验证。
- Terra PASS 后，Sol 直接返回结果，不再读完整代码、不重建快照、不计算摘要、不重跑测试。
- Terra 发现具体问题时，最多允许 Luna 修正一次，再由新的 Terra 复审一次。
- 当前版本不支持 Terra 实现或 Fresh Sol 审计。Luna 无法安全执行时直接 `BLOCKED`。

## 为何更快

本版本删除了此前造成延迟的流程：

- 第二个 Sol Controller
- 模型身份握手
- 风险模式与分阶段调度
- run/task/review ID
- boundary SHA-256
- candidate manifest 与多次冻结
- Sol 最终重复测试
- Terra 默认重复测试

Boundary 使用普通工作区路径，不写受保护的 `.codex` 目录。它属于控制元数据，不进入产品文件列表。

## 角色

| 显示名称 | 模型 | 权限 | 职责 |
|---|---|---|---|
| Sol | 当前 Desktop 任务选择的 Sol | 当前工作区 | 布局与汇总，不改产品文件 |
| Luna | `gpt-5.6-luna` | `workspace-write` | 实现与一次验证 |
| Terra | `gpt-5.6-terra` | `read-only` | 独立审查 |

## 安装

要求 Python 3.11+。

Windows：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\validate.ps1
python -m unittest discover -s tests -v
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\install.ps1 -Force
```

macOS/Linux：

```bash
sh scripts/validate.sh
python3 -m unittest discover -s tests -v
sh scripts/install.sh --force
```

升级安装会安全移除旧版本管理的 `sol-controller`、`terra-worker` 和 `sol-auditor`；若这些文件被修改，`--force`/`-Force` 会先备份。

安装后完全重启 Codex Desktop，新建 Sol 任务，然后只描述结果：

```text
$slt-review

请创建一个 Python 随机数生成器（0-1000）。
```

用户不需要指定测试、风险或运行模式。

## 项目结构

```text
.agents/skills/slt-review/
├─ SKILL.md
├─ agents/openai.yaml
└─ references/
   ├─ protocol.md
   └─ boundary-template.md

.codex/agents/
├─ luna-worker.toml
└─ terra-reviewer.toml
```

## 许可

Apache License 2.0。项目不代表 OpenAI 背书。
