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
load_dotenv()


def getUUID():
    return "".join(str(uuid.uuid4()).split("-"))


def authentication_header(URL, APPID, APPKey):
    appid = APPID
    appKey = APPKey
    uuid = getUUID()

    appName = URL.split('/')[3]
    for i in range(24 - len(appName)):
        appName += "0"
    capabilityname = appName
    csid = appid + capabilityname + uuid
    tmp_xServerParam = {
        "appid": appid,
        "csid": csid
    }
    xCurTime = str(math.floor(time.time()))

    xServerParam = str(base64.b64encode(json.dumps(tmp_xServerParam).encode('utf-8')), encoding="utf8")

    xCheckSum = hashlib.md5(bytes(appKey + xCurTime + xServerParam, encoding="utf8")).hexdigest()
    header = {
        "appKey": appKey,
        "X-Server-Param": xServerParam,
        "X-CurTime": xCurTime,
        "X-CheckSum": xCheckSum,
        'content-type': 'application/json;charset=UTF-8'
    }


    return header


QIANWEN_CONFIG = {
    "api_key": "EMPTY",
    "base_url": os.getenv("model_url"),
    "model_name": os.getenv("model_name"),
    "temperature": 0.3
}


url11 = os.getenv("model_url")
APP_ID = os.getenv("model_id")
APP_KEY = os.getenv("model_key")

print("Qianwen LLM init...")
print(f"{url11}")


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
LLM_API_KEY = os.environ.get("LLM_API_KEY", "sk-38122d7a80584690a8c80aeefee4a534")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")


def get_llm():
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=0
    )
