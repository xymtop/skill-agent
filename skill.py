
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

# ============================================================================
# Skill 扫描（同步 + 异步包装）
# ============================================================================


SKILLS_DIR = os.environ.get("SKILLS_DIR", "./skills")

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
