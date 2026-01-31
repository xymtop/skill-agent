# Skills Agent

一个基于LangGraph的智能Agent系统，支持动态加载技能和工具，能够自主完成各种任务。

## 📋 项目介绍

Skills Agent是一个功能强大的AI助手框架，具有以下特点：

- **基于LangGraph**：使用现代状态机管理AI工作流
- **动态技能加载**：按需加载技能，提高效率
- **丰富的工具集**：内置多种实用工具
- **智能决策**：AI自动分析任务并选择最佳执行路径
- **异步执行**：支持并发操作，提高性能

## 🚀 快速开始

### 环境要求

- Python 3.13+
- 一个支持OpenAI兼容接口的LLM（推荐阿里云DashScope）

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/xymtop/skill-agent
   cd skill-agent
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   复制`.env.example`文件为`.env`，并填入你的AI模型信息：
   ```env
   # AI模型配置
   LLM_MODEL=qwen-plus
   LLM_API_KEY=你的API密钥
   LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
   
   # 技能目录
   SKILLS_DIR=./skills
   ```

## 📁 项目结构

```
skills-agent/
├── skills/          # 技能库
│   ├── weather/     # 天气查询技能
│   ├── github/      # GitHub操作技能
│   └── ...          # 其他技能
├── graph.py         # LangGraph工作流定义
├── nodes.py         # 核心功能节点
├── skill.py         # 技能管理器
├── tools.py         # 工具定义
├── states.py        # 状态管理
├── mcp_manager.py   # 工具连接器
├── llm2.py          # AI模型配置
├── run.py           # 主入口
├── requirements.txt # 依赖列表
└── README.md        # 项目文档
```

## 🎯 核心功能

### 1. 技能系统

- **技能扫描**：自动扫描`skills`目录，识别所有可用技能
- **技能加载**：根据任务需求动态加载技能
- **技能上下文**：为每个技能提供详细的功能描述

### 2. 工具系统

- **基础工具**：内置文件操作、命令执行等通用工具
- **MCP工具**：从技能中加载特定领域的工具
- **工具调度**：智能选择和执行适合任务的工具

### 3. 决策系统

- **任务分析**：分析用户任务，确定所需技能和工具
- **技能决策**：判断是否需要加载新技能
- **工具选择**：选择最适合的工具执行任务

### 4. LangGraph工作流

项目使用LangGraph定义了完整的工作流：

1. **初始化**：重置状态，准备执行环境
2. **决策**：AI分析任务，决定下一步行动
3. **技能加载**：加载所需技能及其工具
4. **工具执行**：执行AI请求的工具，获取结果
5. **响应**：总结执行结果，生成最终响应

## 📖 使用方法

### 命令行执行

```bash
# 基本用法
python run.py "你的任务描述"

# 示例：查询天气
python run.py "帮我查询明天北京的天气"

# 示例：执行命令
python run.py "执行ls -la命令"
```

### 自定义技能

1. **创建技能目录**
   ```bash
   mkdir -p skills/my_skill
   ```

2. **创建技能描述文件**
   在`skills/my_skill`目录下创建`SKILL.md`文件：
   ```markdown
   # My Skill
   
   这是一个自定义技能，用于...
   
   ## 功能
   - 功能1
   - 功能2
   ```

3. **添加MCP配置（可选）**
   如果你的技能需要连接外部服务，可以创建`mcp_config.json`文件：
   ```json
   {
     "mcpServers": {
       "my_tool": {
         "url": "http://localhost:8000",
         "type": "http"
       }
     }
   }
   ```

## 🧠 工作原理

### 核心执行流程

1. **启动流程**：`run.py`中的`run_agent`函数创建并执行LangGraph工作流
2. **决策过程**：`decision_node`分析任务，决定是否需要技能或工具
3. **技能加载**：`skill_node`加载所需技能及其工具
4. **工具执行**：`tool_node`执行AI请求的工具，获取结果
5. **响应生成**：`respond_node`总结执行结果，生成最终响应

### 状态管理

项目使用`AgentState`管理执行状态：

```python
class AgentState(MessagesState):
    available_skills: List[str]    # 已加载的技能
    skill_context: Dict[str, str]   # 技能上下文
    required_skills: List[str]      # 需要加载的技能
    task_complete: bool             # 任务是否完成
    pending_tool_calls: List[dict]   # 待执行的工具调用
```

## 🛠️ 内置工具

### 基础工具

- **view_file**：读取文件内容
- **execute_bash**：执行bash命令
- **list_directory**：列出目录内容
- **write_file**：写入文件
- **parse_times**：解析时间表达式

### 技能工具

项目内置了50+种技能，包括：

- **生活助手**：查天气、导航、订外卖
- **工作工具**：写文案、做表格、查资料
- **娱乐功能**：生成图片、讲笑话、推荐电影
- **开发助手**：写代码、找bug、查文档

## 📊 项目架构

### 核心组件

- **graph.py**：定义LangGraph工作流
- **nodes.py**：实现核心功能节点
- **skill.py**：管理技能系统
- **tools.py**：定义工具
- **states.py**：管理状态
- **mcp_manager.py**：连接外部服务
- **llm2.py**：配置AI模型

### 工作流程图

```
┌─────────┐     ┌───────────┐     ┌────────────┐
│  初始化  │ ──> │   决策    │ ──> │  加载技能  │
└─────────┘     └───────────┘     └────────────┘
                   ↑                  │
                   │                  │
                   │                  ↓
                   │             ┌───────────┐
                   │             │  执行工具  │
                   │             └───────────┘
                   │                  │
                   └──────────────────┘
                                  │
                                  ↓
                            ┌────────────┐
                            │   响应     │
                            └────────────┘
```

## 🔧 配置选项

### 环境变量

| 变量名 | 描述 | 默认值 |
|-------|------|-------|
| LLM_MODEL | 语言模型名称 | qwen-plus |
| LLM_API_KEY | 语言模型API密钥 | - |
| LLM_BASE_URL | 语言模型API基础URL | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| SKILLS_DIR | 技能目录路径 | ./skills |

## 🤝 贡献指南

欢迎贡献代码和技能！请遵循以下步骤：

1. Fork项目
2. 创建分支
3. 提交更改
4. 发起Pull Request

## 📄 许可证

MIT License


**享受AI助手带来的便利！** 🎉