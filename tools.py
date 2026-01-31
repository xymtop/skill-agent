import os
import subprocess
from pathlib import Path
from typing import Union, List
from jionlp.gadget import  parse_time
from langchain_core.tools import tool

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

@tool
def parse_times(time_contents: Union[str, List[str]]):
    """
    从中文文本中精准抽取并解析时间表达式。
    支持单个字符串或字符串列表作为输入。
    """
    # 统一转换为列表
    if isinstance(time_contents, str):
        time_list = [time_contents]
    else:
        time_list = time_contents

    data_list = []
    for time_content in time_list:
        parsed_result = parse_time(time_content)
        data_list.append({
            "time_content": time_content,
            "time_str": parsed_result.get("time","未知")
        })
    return data_list

