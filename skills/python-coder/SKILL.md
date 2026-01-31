---
name: python-coder
description: 专业 Python 代码生成与优化技能，支持根据自然语言需求生成可运行、带注释、符合 PEP8 的 Python 脚本；支持调试建议、性能优化、单元测试生成及常见库（如 requests、pandas、matplotlib）集成。当用户提出‘写一个Python脚本实现…’、‘用Python怎么处理…’、‘帮我优化这段Python代码’、‘加个异常处理’、‘生成测试用例’等请求时触发此 Skill。
---

# Python 代码助手（python-coder）

## ✅ 能力概览
- 根据清晰需求生成结构完整、可直接运行的 Python 脚本
- 自动添加类型提示（type hints）、文档字符串（docstring）和关键注释
- 遵循 PEP8 规范，使用 `black`/`ruff` 兼容格式
- 支持常见任务模式：文件处理、网络请求、数据清洗、图表绘制、CLI 工具等
- 可对已有代码进行重构、加固（异常/日志/输入校验）、性能分析建议
- 可生成配套 `pytest` 单元测试用例（含边界条件）

## 🛠️ 使用方式

### 1. 生成新脚本
请明确描述：
- **目标功能**（例如：从 CSV 读取用户数据，筛选年龄 >30 的人，导出为 Excel）
- **输入/输出格式**（如：文件路径、API URL、字段名）
- **特殊要求**（如：需重试机制、支持命令行参数、写入日志）

✅ 示例提示：
> “写一个 Python 脚本，从 https://jsonplaceholder.typicode.com/posts 获取前 10 篇文章，提取 title 和 body，保存为 posts.json，并打印总字数。”

### 2. 优化或修复现有代码
提供待优化的代码片段 + 具体诉求（如：“加 try-except”、“避免重复计算”、“改成异步”）

### 3. 生成测试
提供函数定义，说明测试目标（如：“测试 handle_csv() 在空文件时抛出 ValueError”）

## 📚 参考资源
- [PEP8 规范摘要](references/pep8.md)
- [常用标准库速查](references/stdlib.md)
- [requests 最佳实践](references/requests.md)
- [pytest 模板](references/pytest.md)

> 💡 提示：本 Skill 默认不执行代码，但会确保生成代码语法正确、逻辑自洽、具备健壮性。如需实际运行或调试，请配合 `execute_bash` 工具验证。