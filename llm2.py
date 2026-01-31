import os

import httpx
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import traceback
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
from langchain_core.prompts import ChatPromptTemplate
import hashlib
import json
import base64
import math
import uuid
import time

from dotenv import load_dotenv


# def  get_llm():
#     # 2. 创建LLM实例
#     llm = ChatOpenAI(
#         api_key=QIANWEN_CONFIG["api_key"],
#         base_url=QIANWEN_CONFIG["base_url"],
#         model_name=QIANWEN_CONFIG["model_name"],
#         temperature=QIANWEN_CONFIG["temperature"],
#         default_headers=authentication_header(url11, APP_ID, APP_KEY),
#         extra_body={
#             "extra_body":{
#             "chat_template_kwargs": {"enable_thinking": False}
#             }
#         }
#
#     )
#     return llm


# # ============================================================================
# # LLM
# # ============================================================================
#

LLM_MODEL = os.environ.get("LLM_MODEL", "qwen-plus")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")


def get_llm():
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=0
    )
