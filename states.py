
from typing import  Dict
from typing import List
from langgraph.graph import  MessagesState

# ============================================================================
# 状态定义
# ============================================================================

class AgentState(MessagesState):
    available_skills: List[str]
    skill_context: Dict[str, str]
    required_skills: List[str]
    task_complete: bool
    pending_tool_calls: List[dict]  # 暂存的工具调用

