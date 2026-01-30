"""
Agent Skills Manager - 完备的技能管理系统
支持 Agent Skills 标准格式的加载、管理和 MCP 工具转换
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import re
import logging
from enum import Enum

from core.entity.skill import Skill, SkillMetadata

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)





class SkillManager:
    """Agent Skills 管理器（支持 MCP）"""

    def __init__(self, skills_dirs: Optional[List[str]] = None):
        """
        初始化技能管理器

        Args:
            skills_dirs: 技能目录列表
        """
        self.skills: Dict[str, Skill] = {}
        self.skills_by_category: Dict[str, List[str]] = {}
        self.skills_by_tag: Dict[str, List[str]] = {}

        # 默认技能目录
        if skills_dirs is None:
            home = Path.home()
            skills_dirs = [
                str(home / '.config' / 'goose' / 'skills'),
                str(home / '.claude' / 'skills'),
                str(home / '.config' / 'agent' / 'skills'),
                './.github/skills',
                './skills'
            ]

        self.skills_dirs = [Path(d) for d in skills_dirs]
        self.discover_skills()

        logger.info(f"技能管理器初始化完成，搜索路径: {[str(d) for d in self.skills_dirs]}")

    def discover_skills(self) -> int:
        """
        自动发现并加载所有技能

        Returns:
            加载的技能数量
        """
        loaded_count = 0

        for skills_dir in self.skills_dirs:
            if not skills_dir.exists():
                logger.debug(f"技能目录不存在: {skills_dir}")
                continue

            logger.info(f"扫描技能目录: {skills_dir}")

            # 遍历目录查找 SKILL.md 文件
            for skill_file in skills_dir.rglob('SKILL.md'):
                skill_path = skill_file.parent

                try:
                    skill = self._load_skill(skill_path)
                    if skill:
                        self.skills[skill.skill_id] = skill
                        loaded_count += 1
                        mcp_status = "✓ 有 MCP" if skill.mcp_config else ""
                        logger.info(f"✓ 加载技能: {skill.metadata.name} ({skill.skill_id}) {mcp_status}")
                except Exception as e:
                    logger.error(f"✗ 加载技能失败 {skill_path}: {e}")

        logger.info(f"技能发现完成，共加载 {loaded_count} 个技能")
        return loaded_count

    def _load_skill(self, skill_path: Path) -> Optional[Skill]:
        """
        加载单个技能

        Args:
            skill_path: 技能文件夹路径

        Returns:
            Skill 对象或 None
        """
        skill_file = skill_path / 'SKILL.md'

        if not skill_file.exists():
            logger.warning(f"SKILL.md 文件不存在: {skill_path}")
            return None

        # 读取文件内容
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析 YAML frontmatter
        metadata = self._parse_frontmatter(content)

        if not metadata:
            logger.warning(f"无法解析技能元数据: {skill_path}")
            return None

        # 生成唯一 ID
        skill_id =metadata.name

        # 加载 MCP 配置
        mcp_config = self._load_mcp_config(skill_path)

        # 扫描资源和脚本
        resources = self._scan_resources(skill_path)
        scripts = self._scan_scripts(skill_path)

        # 创建技能对象
        skill = Skill(
            skill_id=skill_id,
            metadata=metadata,
            content=content,
            skill_path=skill_path,
            mcp_config=mcp_config,
            resources=resources,
            scripts=scripts
        )

        return skill

    def _parse_frontmatter(self, content: str) -> Optional[SkillMetadata]:
        """解析 YAML frontmatter"""
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            logger.warning("未找到 YAML frontmatter")
            return None

        try:
            yaml_content = match.group(1)
            yaml_data = yaml.safe_load(yaml_content)
            return SkillMetadata.from_yaml(yaml_data)
        except yaml.YAMLError as e:
            logger.error(f"YAML 解析错误: {e}")
            return None

    def _load_mcp_config(self, skill_path: Path) -> Optional[Dict[str, Any]]:
        """
        加载 MCP 配置文件

        Args:
            skill_path: 技能路径

        Returns:
            MCP 配置字典或 None
        """
        mcp_config_file = skill_path / 'mcp_config.json'

        if not mcp_config_file.exists():
            return None

        try:
            with open(mcp_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            logger.info(f"加载 MCP 配置: {skill_path.name}")
            return config
        except Exception as e:
            logger.error(f"加载 MCP 配置失败 {skill_path}: {e}")
            return None

    def _generate_skill_id(self, skill_path: Path, name: str) -> str:
        """生成技能唯一 ID"""
        path_hash = hash(str(skill_path))
        name_slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        return f"{name_slug}-{abs(path_hash) % 10000:04d}"

    def _scan_resources(self, skill_path: Path) -> Dict[str, Path]:
        """扫描技能资源文件"""
        resources = {}
        resource_exts = ['.txt', '.json', '.yaml', '.yml', '.csv', '.md']

        for ext in resource_exts:
            for file in skill_path.rglob(f'*{ext}'):
                if file.name not in ['SKILL.md', 'mcp_config.json']:
                    rel_path = file.relative_to(skill_path)
                    resources[str(rel_path)] = file

        return resources

    def _scan_scripts(self, skill_path: Path) -> Dict[str, Path]:
        """扫描技能脚本文件"""
        scripts = {}
        script_exts = ['.py', '.sh', '.js', '.ts']

        for ext in script_exts:
            for file in skill_path.rglob(f'*{ext}'):
                rel_path = file.relative_to(skill_path)
                scripts[str(rel_path)] = file

        return scripts

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取指定技能"""
        return self.skills.get(skill_id)

    def get_all_skills_summary(self) -> str:
        """获取所有技能的摘要信息"""
        if not self.skills:
            return "当前没有加载任何技能。"

        summary_lines = ["可用技能列表：\n"]
        for skill in sorted(self.skills.values(), key=lambda s: s.metadata.name):
            mcp_indicator = " [有 MCP 工具]" if skill.mcp_config else ""
            summary_lines.append(
                f"- {skill.metadata.name}: {skill.metadata.description} "
                f"[分类: {skill.metadata.category}]{mcp_indicator}"
            )

        return "\n".join(summary_lines)

    def get_mcp_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有技能的 MCP 配置

        Returns:
            {skill_id: mcp_config} 字典
        """
        mcp_configs = {}
        for skill in self.get_skills_with_mcp():
            mcp_configs[skill.skill_id] = skill.mcp_config

        return mcp_configs

    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """通过名称获取技能（支持模糊匹配）"""
        # 精确匹配
        for skill in self.skills.values():
            if skill.metadata.name.lower() == name.lower():
                return skill

        # 模糊匹配
        for skill in self.skills.values():
            if name.lower() in skill.metadata.name.lower():
                return skill

        return None



skill_m = SkillManager(["../skills"])
print(skill_m.get_all_skills_summary())
skill = skill_m.get_skill("web-search")
print(skill)

