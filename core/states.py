from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
# 定义状态类型
class AgentState(MessagesState):
    """Agent 状态定义"""


