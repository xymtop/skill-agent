
import os
import json
import subprocess
import asyncio
from pathlib import Path
from typing import Literal, List, Dict, Any, Optional
from typing import Union, List
import httpx
from jionlp.gadget import  parse_time


from langchain_core.tools import tool, BaseTool
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, MessagesState

from langchain_mcp_adapters.client import MultiServerMCPClient

from nodes import decision_node, init_node, skill_node, tool_node, respond_node, route_after_decision
from states import AgentState


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
