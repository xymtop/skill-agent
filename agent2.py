"""
LangGraph Five-Node Agent with MCP Skills

修复：当 LLM 调用不存在的工具时，自动触发 skill 加载
"""

import os
import json
import subprocess
import asyncio
from pathlib import Path
from typing import TypedDict, Annotated, Literal, List, Dict, Any, Optional
from typing_extensions import NotRequired

from langchain_core.tools import tool, BaseTool
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode

from langchain_mcp_adapters.client import MultiServerMCPClient

# from llm2 import get_llm

# ============================================================================
# 配置
# ============================================================================

SKILLS_DIR = os.environ.get("SKILLS_DIR", "./skills")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen-plus")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "sk-38122d7a80584690a8c80aeefee4a534")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")


# ============================================================================
# MCP 工具管理器
# ============================================================================

class MCPToolManager:
    def __init__(self):
        self._tools: Dict[str, List[BaseTool]] = {}
        self._clients: Dict[str, MultiServerMCPClient] = {}
        self._tool_to_skill: Dict[str, str] = {}  # tool_name -> skill_id 映射
        self._lock = asyncio.Lock()

    async def load_skill_mcp_tools(self, skill_id: str, mcp_config_path: str) -> List[BaseTool]:
        async with self._lock:
            if skill_id in self._tools:
                return self._tools[skill_id]

            try:
                def read_config():
                    with open(mcp_config_path, 'r', encoding='utf-8') as f:
                        return json.load(f)

                config = await asyncio.to_thread(read_config)
                mcp_servers = config.get("mcpServers", {})

                if not mcp_servers:
                    self._tools[skill_id] = []
                    return []

                print(f"🔧 Skill {skill_id}: 连接 MCP servers: {list(mcp_servers.keys())}")

                # langchain-mcp-adapters >= 0.1.0 新 API
                client = MultiServerMCPClient(mcp_servers)
                tools = await client.get_tools()

                self._clients[skill_id] = client
                self._tools[skill_id] = tools

                # 建立 tool_name -> skill_id 映射
                for t in tools:
                    self._tool_to_skill[t.name] = skill_id

                print(f"✅ Skill {skill_id}: 加载 {len(tools)} 个工具: {[t.name for t in tools]}")
                return tools

            except Exception as e:
                print(f"❌ Skill {skill_id}: 加载失败: {e}")
                self._tools[skill_id] = []
                return []

    def get_all_tools(self) -> List[BaseTool]:
        all_tools = []
        for tools in self._tools.values():
            all_tools.extend(tools)
        return all_tools

    def get_skill_for_tool(self, tool_name: str) -> Optional[str]:
        """根据工具名查找对应的 skill_id"""
        return self._tool_to_skill.get(tool_name)

    def is_tool_loaded(self, tool_name: str) -> bool:
        """检查工具是否已加载"""
        return tool_name in self._tool_to_skill

    async def cleanup(self):
        # langchain-mcp-adapters >= 0.1.0 不需要手动关闭
        # client 会自动管理连接
        self._clients.clear()
        self._tools.clear()
        self._tool_to_skill.clear()


mcp_manager = MCPToolManager()


# ============================================================================
# 状态定义
# ============================================================================

class AgentState(MessagesState):
    available_skills: List[str]
    skill_context: Dict[str, str]
    required_skills: List[str]
    task_complete: bool
    pending_tool_calls: List[dict]  # 暂存的工具调用


# ============================================================================
# 基础工具
# ============================================================================

@tool
def view_file(path: str) -> str:
    """Read and return the content of a file at the given path."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) > 10000:
                return content[:10000] + "\n\n... [truncated]"
            return content
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def execute_bash(command: str) -> str:
    """Execute a bash command and return the output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout or result.stderr
        return output if output else f"Command completed with code {result.returncode}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error: {e}"


@tool
def list_directory(path: str = ".") -> str:
    """List files and directories at the given path."""
    try:
        return "\n".join(sorted(os.listdir(path)))
    except Exception as e:
        return f"Error: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {e}"


BASE_TOOLS: List[BaseTool] = [view_file, execute_bash, list_directory, write_file]
BASE_TOOL_NAMES = {t.name for t in BASE_TOOLS}


# ============================================================================
# Skill 扫描（同步 + 异步包装）
# ============================================================================

def _scan_skills_sync(skills_dir: str) -> Dict[str, Dict[str, Any]]:
    skills_path = Path(skills_dir)
    skills = {}
    if not skills_path.exists():
        return skills

    for skill_dir in skills_path.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_id = skill_dir.name
        skill_md = skill_dir / "SKILL.md"
        mcp_config = skill_dir / "mcp_config.json"

        skill_info = {
            "id": skill_id,
            "path": str(skill_dir),
            "has_skill_md": skill_md.exists(),
            "has_mcp": mcp_config.exists(),
            "skill_md_path": str(skill_md) if skill_md.exists() else None,
            "mcp_config_path": str(mcp_config) if mcp_config.exists() else None,
            "mcp_tool_names": []
        }

        # 读取 MCP 配置中的工具名（用于匹配）
        if mcp_config.exists():
            try:
                with open(mcp_config, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    # 从 mcpServers 的 key 推断工具名前缀
                    for server_name in cfg.get("mcpServers", {}).keys():
                        skill_info["mcp_tool_names"].append(server_name)
            except:
                pass

        if skill_md.exists():
            try:
                with open(skill_md, 'r', encoding='utf-8') as f:
                    skill_info["summary"] = f.read()[:500]
            except:
                pass

        skills[skill_id] = skill_info
    return skills


def _load_skill_context_sync(skill_id: str, skills_dir: str) -> str:
    skill_md = Path(skills_dir) / skill_id / "SKILL.md"
    if skill_md.exists():
        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            pass
    return f"Skill '{skill_id}' not found."


async def scan_skills(skills_dir: str = SKILLS_DIR) -> Dict[str, Dict[str, Any]]:
    return await asyncio.to_thread(_scan_skills_sync, skills_dir)


async def load_skill_context(skill_id: str, skills_dir: str = SKILLS_DIR) -> str:
    return await asyncio.to_thread(_load_skill_context_sync, skill_id, skills_dir)


def _get_skills_prompt_sync(skills_dir: str) -> str:
    skills = _scan_skills_sync(skills_dir)
    if not skills:
        return "<available_skills>No skills.</available_skills>"

    lines = ["<available_skills>"]
    for skill_id, info in skills.items():
        summary = info.get("summary", "No description")[:200].replace("\n", " ")
        lines.append(f'  <skill id="{skill_id}" has_mcp="{info["has_mcp"]}">{summary}...</skill>')
    lines.append("</available_skills>")
    return "\n".join(lines)


async def get_skills_prompt(skills_dir: str = SKILLS_DIR) -> str:
    return await asyncio.to_thread(_get_skills_prompt_sync, skills_dir)


# ============================================================================
# 查找工具对应的 skill
# ============================================================================

def _find_skill_for_tool_sync(tool_name: str, skills_dir: str) -> Optional[str]:
    """根据工具名猜测对应的 skill_id"""
    skills = _scan_skills_sync(skills_dir)

    # 策略1：工具名包含 skill_id
    for skill_id in skills:
        if skill_id in tool_name or tool_name in skill_id:
            return skill_id

    # 策略2：工具名包含 mcp server name
    for skill_id, info in skills.items():
        for server_name in info.get("mcp_tool_names", []):
            if server_name in tool_name or tool_name.startswith(server_name):
                return skill_id

    # 策略3：模糊匹配（web-search -> web-search skill）
    tool_prefix = tool_name.split("_")[0].split("-")[0]
    for skill_id in skills:
        if tool_prefix in skill_id:
            return skill_id

    return None


async def find_skill_for_tool(tool_name: str, skills_dir: str = SKILLS_DIR) -> Optional[str]:
    return await asyncio.to_thread(_find_skill_for_tool_sync, tool_name, skills_dir)


# # ============================================================================
# # LLM
# # ============================================================================
#
def get_llm():
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=0
    )


def get_current_tools() -> List[BaseTool]:
    return BASE_TOOLS + mcp_manager.get_all_tools()


# ============================================================================
# 节点
# ============================================================================

async def init_node(state: AgentState) -> dict:
    return {
        "available_skills": [],
        "skill_context": {},
        "required_skills": [],
        "task_complete": False,
        "pending_tool_calls": []
    }


async def decision_node(state: AgentState) -> dict:
    llm = get_llm()
    skills_prompt = await get_skills_prompt(SKILLS_DIR)

    loaded_skills = state.get("available_skills", [])
    loaded_context = ""
    if state.get("skill_context"):
        loaded_context = "\n\n<loaded_skill_contexts>\n"
        for skill_id, ctx in state["skill_context"].items():
            loaded_context += f"### {skill_id}\n{ctx}\n\n"
        loaded_context += "</loaded_skill_contexts>"

    current_tools = get_current_tools()
    tool_names = [t.name for t in current_tools]

    # 根据是否有已加载的技能调整提示
    if loaded_skills:
        action_hint = f"""## 已加载的技能
{loaded_skills}

## 当前可用工具
{tool_names}

**重要：技能已加载完成！现在请直接调用工具完成任务，不要再输出 LOAD_SKILL！**

直接使用工具调用来完成用户的请求。"""
    else:
        action_hint = f"""## 当前可用工具
{tool_names}

## 决策流程
1. 如果需要使用某个 skill 的 MCP 工具，先输出：
   ```json
   {{"action": "LOAD_SKILL", "skill_ids": ["skill_id"]}}
   ```
2. 如果工具已在可用列表中，直接调用工具。
3. 任务完成时直接回复。"""

    system_msg = f"""你是一个智能助手，可以使用工具和技能。请用中文回复。

{skills_prompt}
{loaded_context}

{action_hint}
"""

    llm_with_tools = llm.bind_tools(current_tools)
    messages = [SystemMessage(content=system_msg)] + list(state["messages"])
    response = await llm_with_tools.ainvoke(messages)

    result = {"messages": [response], "required_skills": [], "pending_tool_calls": []}

    # 检查 LOAD_SKILL 指令（只有在技能未加载时才处理）
    loaded_skills = state.get("available_skills", [])
    if response.content and "LOAD_SKILL" in response.content:
        try:
            import re
            json_match = re.search(r'\{[^{}]*"action"\s*:\s*"LOAD_SKILL"[^{}]*\}', response.content)
            if json_match:
                action_data = json.loads(json_match.group())
                skill_ids = action_data.get("skill_ids", [])
                # 过滤掉已加载的技能
                new_skill_ids = [s for s in skill_ids if s not in loaded_skills]
                if new_skill_ids:
                    result["required_skills"] = new_skill_ids
                    result["task_complete"] = False
                    return result
                # 如果全都已加载，添加提示让 LLM 直接用工具
                print(f"⚠️ 技能 {skill_ids} 已全部加载，强制 LLM 使用工具")
                # 替换消息，提示 LLM 工具已可用
                force_msg = AIMessage(
                    content=f"技能已加载，现在可用的工具有: {[t.name for t in get_current_tools()]}。请直接调用工具完成任务。"
                )
                result["messages"] = [force_msg]
                result["task_complete"] = False
                return result
        except:
            pass

    # 检查工具调用
    if response.tool_calls:
        missing_skills = []
        valid_tool_calls = []

        for tc in response.tool_calls:
            tool_name = tc["name"]
            # 检查工具是否存在
            if tool_name in BASE_TOOL_NAMES or mcp_manager.is_tool_loaded(tool_name):
                valid_tool_calls.append(tc)
            else:
                # 工具不存在，找对应的 skill
                skill_id = await find_skill_for_tool(tool_name, SKILLS_DIR)
                if skill_id and skill_id not in missing_skills:
                    missing_skills.append(skill_id)
                    print(f"⚠️ 工具 {tool_name} 未加载，需要先加载 skill: {skill_id}")

        if missing_skills:
            # 需要先加载 skill
            result["required_skills"] = missing_skills
            result["pending_tool_calls"] = response.tool_calls  # 保存待执行的调用
            result["task_complete"] = False

            # 添加提示消息
            hint_msg = AIMessage(content=f"我需要先加载技能 {missing_skills} 才能使用相关工具。")
            result["messages"] = [hint_msg]
            return result

        result["task_complete"] = False
    else:
        result["task_complete"] = True

    return result


async def skill_node(state: AgentState) -> dict:
    required = state.get("required_skills", [])
    loaded = state.get("available_skills", [])
    new_skills = [s for s in required if s not in loaded]

    if not new_skills:
        return {}

    new_context = {}
    skills_info = await scan_skills(SKILLS_DIR)
    loaded_mcp_tools = []

    for skill_id in new_skills:
        context = await load_skill_context(skill_id, SKILLS_DIR)
        new_context[skill_id] = context
        print(f"📖 加载技能上下文: {skill_id}")

        skill_info = skills_info.get(skill_id, {})
        if skill_info.get("has_mcp") and skill_info.get("mcp_config_path"):
            mcp_tools = await mcp_manager.load_skill_mcp_tools(
                skill_id, skill_info["mcp_config_path"]
            )
            if mcp_tools:
                loaded_mcp_tools.extend([t.name for t in mcp_tools])

    tools_msg = f" 可用工具: {loaded_mcp_tools}" if loaded_mcp_tools else ""
    skill_loaded_msg = AIMessage(
        content=f"✅ 已加载技能: {', '.join(new_skills)}.{tools_msg}"
    )

    return {
        "available_skills": loaded + new_skills,
        "skill_context": {**state.get("skill_context", {}), **new_context},
        "required_skills": [],
        "messages": [skill_loaded_msg],
        "pending_tool_calls": []  # 清空，回到 decision 重新决策
    }


async def tool_node(state: AgentState) -> dict:
    """异步执行工具调用"""
    current_tools = get_current_tools()
    tools_by_name = {t.name: t for t in current_tools}

    messages = state.get("messages", [])
    last_msg = messages[-1] if messages else None

    if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
        return {}

    tool_messages = []
    for tc in last_msg.tool_calls:
        tool_name = tc["name"]
        tool_args = tc["args"]
        tool_id = tc["id"]

        tool = tools_by_name.get(tool_name)
        if not tool:
            tool_messages.append(ToolMessage(
                content=f"Error: Tool '{tool_name}' not found.",
                tool_call_id=tool_id
            ))
            continue

        try:
            # 使用异步调用
            result = await tool.ainvoke(tool_args)
            tool_messages.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_id
            ))
        except Exception as e:
            tool_messages.append(ToolMessage(
                content=f"Error: {e}",
                tool_call_id=tool_id
            ))

    return {"messages": tool_messages}


async def respond_node(state: AgentState) -> dict:
    return {}


# ============================================================================
# 路由
# ============================================================================

def route_after_decision(state: AgentState) -> Literal["skill_node", "tool_node", "respond"]:
    # 优先加载 skill
    required = state.get("required_skills", [])
    loaded = state.get("available_skills", [])
    if required:
        new_skills = [s for s in required if s not in loaded]
        if new_skills:
            return "skill_node"

    # 工具调用
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
            return "tool_node"

    return "respond"


# ============================================================================
# Graph
# ============================================================================

def create_agent() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("init", init_node)
    graph.add_node("decision", decision_node)
    graph.add_node("skill_node", skill_node)
    graph.add_node("tool_node", tool_node)
    graph.add_node("respond", respond_node)

    graph.set_entry_point("init")
    graph.add_edge("init", "decision")

    graph.add_conditional_edges(
        "decision",
        route_after_decision,
        {"skill_node": "skill_node", "tool_node": "tool_node", "respond": "respond"}
    )

    graph.add_edge("skill_node", "decision")
    graph.add_edge("tool_node", "decision")
    graph.add_edge("respond", END)

    return graph


graph = create_agent().compile()


# ============================================================================
# CLI
# ============================================================================

async def run_agent(message: str):
    print(f"\n{'='*60}\n🎯 Task: {message}\n{'='*60}")
    try:
        result = await graph.ainvoke({"messages": [HumanMessage(content=message)]})
        print(f"\n{'='*60}\n📤 RESULT:\n{'='*60}")
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                print(msg.content)
                break
        return result
    finally:
        await mcp_manager.cleanup()


def main():
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "你好"
    asyncio.run(run_agent(query))


if __name__ == "__main__":
    main()