---
name: cron-manager
description: Linux cron 任务管理技能：支持自然语言解析定时需求（如“每天凌晨3点运行脚本”）、安全增删改查用户 crontab、cron 表达式校验与可读化解释。使用时需提供具体操作（add/remove/list/modify）及时间描述或 cron 表达式。适用于系统运维、自动化脚本部署等场景。
author: Skills Team
tags:
  - cron
  - linux
  - automation
  - sysadmin
  - scheduling
priority: 8
---

# Cron Manager Skill

## ✅ 能力概览

- **自然语言转 cron**：将中文时间描述（如“每周一至五上午8:30执行”）自动转换为标准 cron 表达式，并给出可读解释。
- **安全 crontab 操作**：仅操作当前用户 crontab（`crontab -e`），禁止 root 权限操作；所有写入前强制二次确认。
- **语法校验与诊断**：检查 cron 表达式格式、字段范围（如分钟 0–59）、常见陷阱（如 `* * * * *` 风险提示）。
- **任务列表与详情**：`list` 返回结构化任务清单（含编号、表达式、命令、上次修改时间）；`show <id>` 查看详情。
- **智能建议**：对模糊描述（如“每天一次”）推荐合理默认值（`0 0 * * *`），并说明理由。

## 🛠️ 工具集成

本 Skill 依赖以下系统命令（已预检权限）：
- `crontab -l` → 列出当前用户任务
- `crontab -e` → 安全编辑（通过临时文件 + diff 确认）
- `crontab -r` → 仅允许清空（需显式 `confirm: true`）
- `date`, `crontab --help` → 辅助诊断

> ⚠️ 注意：不执行实际命令，仅管理调度规则；命令本身需用户确保可执行且路径正确。

## 📝 输入规范（JSON Schema）

```json
{
  "type": "object",
  "required": ["action"],
  "properties": {
    "action": {
      "type": "string",
      "enum": ["add", "remove", "list", "modify", "explain"]
    },
    "expression": { "type": "string", "description": "cron 表达式，如 '0 9 * * *'" },
    "command": { "type": "string", "description": "要执行的完整命令或脚本路径" },
    "description": { "type": "string", "description": "自然语言描述，如 '每天早上9点备份数据库'" },
    "id": { "type": "integer", "description": "任务编号（用于 remove/modify/show）" },
    "confirm": { "type": "boolean", "default": false }
  }
}
```

## 🌟 示例工作流

### 场景1：添加新任务（自然语言输入）
```json
{ "action": "add", "description": "每小时整点发送服务器状态邮件给 admin@example.com" }
```
→ 自动推导：`0 * * * * /usr/local/bin/send-status.sh admin@example.com`
→ 输出：可读解释 + 确认 prompt

### 场景2：解释现有表达式
```json
{ "action": "explain", "expression": "*/5 9-17 * * 1-5" }
```
→ 输出："工作日（周一至五）上午9点至下午5点之间，每5分钟执行一次"

### 场景3：安全删除第3条任务
```json
{ "action": "remove", "id": 3, "confirm": true }
```
→ 先显示该行内容，再执行 `crontab -e` 删除对应行

## 📚 参考资源

- [Cron 表达式速查表](references/cron-cheatsheet.md)
- [Linux crontab 手册页摘要](references/man-crontab.md)
- [安全最佳实践：避免常见陷阱](references/security-notes.md)
