

from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SkillMetadata:
    """技能元数据"""
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    category: str = "general"
    priority: int = 0

    @classmethod
    def from_yaml(cls, yaml_data: Dict[str, Any]) -> 'SkillMetadata':
        """从 YAML 数据创建元数据对象"""
        return cls(
            name=yaml_data.get('name', ''),
            description=yaml_data.get('description', ''),
            version=yaml_data.get('version', '1.0.0'),
            author=yaml_data.get('author', ''),
            tags=yaml_data.get('tags', []),
            dependencies=yaml_data.get('dependencies', []),
            category=yaml_data.get('category', 'general'),
            priority=yaml_data.get('priority', 0)
        )

@dataclass
class Skill:
    """技能对象"""
    skill_id: str
    metadata: SkillMetadata
    content: str
    skill_path: Path
    loaded_at: datetime = field(default_factory=datetime.now)


    # MCP 配置
    mcp_config: Optional[Dict[str, Any]] = None

    # 资源文件
    resources: Dict[str, Path] = field(default_factory=dict)
    scripts: Dict[str, Path] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'skill_id': self.skill_id,
            'name': self.metadata.name,
            'description': self.metadata.description,
            'version': self.metadata.version,
            'author': self.metadata.author,
            'tags': self.metadata.tags,
            'category': self.metadata.category,
            'priority': self.metadata.priority,
            'loaded_at': self.loaded_at.isoformat(),
            'has_mcp': self.mcp_config is not None,
            'resources_count': len(self.resources),
            'scripts_count': len(self.scripts)
        }
