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

from tools import view_file, execute_bash, list_directory, write_file, parse_times


# ============================================================================
# MCP 工具管理器
# ============================================================================

def create_client(headers,auth,timeout):
    headers = {
        "Authorization": "Bearer sk-fe2215fdc69b4976bdabfad1dfd65d40"
    }
    return httpx.AsyncClient(verify=False, headers=headers,timeout=120)



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
                for name, mcp_settings in mcp_servers.items():
                    if name == "bocha-mcp":
                        print(f"🔧 Skill {skill_id}: 配置 MCP 服务器: {mcp_settings}")
                        mcp_servers['bocha-mcp']['httpx_client_factory'] = create_client

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

BASE_TOOLS: List[BaseTool] = [view_file, execute_bash, list_directory, write_file,parse_times]
BASE_TOOL_NAMES = {t.name for t in BASE_TOOLS}


mcp_manager = MCPToolManager()
def get_current_tools() -> List[BaseTool]:
    return BASE_TOOLS + mcp_manager.get_all_tools()

