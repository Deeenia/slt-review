# SLT Review

[中文](README.md) | [English](README.en.md)

一个成本与效率优先的 Codex Skill：由 Sol 负责规划和限定任务边界，Luna 以较低成本完成实现，Terra 通过独立审查降低单一模型的判断偏差。

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
- Terra 不参与实现，也不担任实现者的唯一审查者。Luna 无法安全执行时直接 `BLOCKED`。

## 成本与效率策略

- 只让高能力的 Sol 完成需求理解、任务布局、边界制定与最终汇总。
- 将主要编码工作交给 Luna，降低实现阶段的模型成本。
- Terra 只审查 Luna 的实际改动，以不同模型视角发现遗漏和偏差。
- 正常成功路径只调用 Luna 和 Terra 各一次。
- 默认不重复运行已经成功的验证；只有 Terra 报告具体缺陷时才进入一次修正和复审。

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
