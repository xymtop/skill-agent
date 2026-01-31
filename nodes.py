
import json
from typing import Literal
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from llm2 import get_llm
from mcp_manager import get_current_tools, BASE_TOOL_NAMES, mcp_manager
from skill import get_skills_prompt, SKILLS_DIR, find_skill_for_tool, scan_skills, load_skill_context
from states import AgentState


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
        action_hint = f"""## 用户当前用的是macos，请将用户体验拉到最好
        ## 已加载的技能
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

