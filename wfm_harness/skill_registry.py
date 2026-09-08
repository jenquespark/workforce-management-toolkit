"""
Skill management for Workforce Management Harness.

Provides agent-friendly skills for deterministic WFM operations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import json
import yaml
from pathlib import Path

class SkillType(str, Enum):
    FORECASTING = "forecasting"
    FORECAST_EVALUATION = "forecast_evaluation"
    STAFFING = "staffing"
    SCHEDULING = "scheduling"
    OPTIMIZATION = "optimization"
    INTRADAY_ORCHESTRATION = "intraday_orchestration"
    CAPACITY_PLANNING = "capacity_planning"
    VALIDATION = "validation"
    BI_DELIVERY = "bi_delivery"

class SkillComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"

@dataclass
class SkillParameter:
    """Skill parameter definition."""
    name: str
    type: str
    required: bool = True
    description: str = ""
    default_value: Any = None
    validation_rules: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SkillOutput:
    """Skill output definition."""
    type: str
    description: str
    format: str = "json"
    schema: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SkillConstraint:
    """Skill constraint definition."""
    type: str
    description: str
    constraint: str
    error_message: str = ""

@dataclass
class SkillExample:
    """Skill usage example."""
    title: str
    description: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    explanation: str = ""

@dataclass
class WFMPluginSkill:
    """Agent-friendly skill for Workforce Management operations."""

    identifier: str
    name: str
    description: str
    skill_type: SkillType
    complexity: SkillComplexity
    version: str = "1.0.0"
    author: str = "Workforce Management Harness"
    created_at: datetime = field(default_factory=datetime.utcnow)
    parameters: List[SkillParameter] = field(default_factory=list)
    outputs: List[SkillOutput] = field(default_factory=list)
    constraints: List[SkillConstraint] = field(default_factory=list)
    examples: List[SkillExample] = field(default_factory=list)
    implementation: Dict[str, Any] = field(default_factory=dict)
    deterministic: bool = True
    llm_override_prohibited: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "identifier": self.identifier,
            "name": self.name,
            "description": self.description,
            "skill_type": self.skill_type.value,
            "complexity": self.complexity.value,
            "version": self.version,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "required": p.required,
                    "description": p.description,
                    "default_value": p.default_value,
                    "validation_rules": p.validation_rules
                }
                for p in self.parameters
            ],
            "outputs": [
                {
                    "type": o.type,
                    "description": o.description,
                    "format": o.format,
                    "schema": o.schema
                }
                for o in self.outputs
            ],
            "constraints": [
                {
                    "type": c.type,
                    "description": c.description,
                    "constraint": c.constraint,
                    "error_message": c.error_message
                }
                for c in self.constraints
            ],
            "examples": [
                {
                    "title": e.title,
                    "description": e.description,
                    "input": e.input,
                    "output": e.output,
                    "explanation": e.explanation
                }
                for e in self.examples
            ],
            "implementation": self.implementation,
            "deterministic": self.deterministic,
            "llm_override_prohibited": self.llm_override_prohibited,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WFMPluginSkill":
        """Create WFMPluginSkill from dictionary."""
        return cls(
            identifier=data["identifier"],
            name=data["name"],
            description=data["description"],
            skill_type=SkillType(data["skill_type"]),
            complexity=SkillComplexity(data["complexity"]),
            version=data.get("version", "1.0.0"),
            author=data.get("author", "Workforce Management Harness"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            parameters=[
                SkillParameter(
                    name=p["name"],
                    type=p["type"],
                    required=p.get("required", True),
                    description=p.get("description", ""),
                    default_value=p.get("default_value"),
                    validation_rules=p.get("validation_rules", {})
                )
                for p in data.get("parameters", [])
            ],
            outputs=[
                SkillOutput(
                    type=o["type"],
                    description=o["description"],
                    format=o.get("format", "json"),
                    schema=o.get("schema", {})
                )
                for o in data.get("outputs", [])
            ],
            constraints=[
                SkillConstraint(
                    type=c["type"],
                    description=c["description"],
                    constraint=c["constraint"],
                    error_message=c.get("error_message", "")
                )
                for c in data.get("constraints", [])
            ],
            examples=[
                SkillExample(
                    title=e["title"],
                    description=e["description"],
                    input=e["input"],
                    output=e["output"],
                    explanation=e.get("explanation", "")
                )
                for e in data.get("examples", [])
            ],
            implementation=data.get("implementation", {}),
            deterministic=data.get("deterministic", True),
            llm_override_prohibited=data.get("llm_override_prohibited", True),
            metadata=data.get("metadata", {})
        )

class WFMSkillRegistry:
    """Registry for managing WFM plugin skills."""

    def __init__(self):
        self.skills: Dict[str, WFMPluginSkill] = {}
        self._load_default_skills()

    def _load_default_skills(self):
        """Load default skill definitions."""
        # This will be populated with core skills
        pass

    def register_skill(self, skill: WFMPluginSkill):
        """Register a new skill."""
        self.skills[skill.identifier] = skill

    def get_skill(self, identifier: str) -> Optional[WFMPluginSkill]:
        """Get skill by identifier."""
        return self.skills.get(identifier)

    def list_skills(self, skill_type: Optional[SkillType] = None, complexity: Optional[SkillComplexity] = None) -> List[WFMPluginSkill]:
        """List skills with optional filters."""
        skills = list(self.skills.values())
        
        if skill_type is not None:
            skills = [s for s in skills if s.skill_type == skill_type]
        
        if complexity is not None:
            skills = [s for s in skills if s.complexity == complexity]
        
        return skills

    def list_deterministic_skills(self) -> List[WFMPluginSkill]:
        """List skills that are deterministic (safe for small models)."""
        return [s for s in self.skills.values() if s.deterministic and s.llm_override_prohibited]

    def export_skills(self, format: str = "json") -> str:
        """Export skills in specified format."""
        if format.lower() == "json":
            return json.dumps([s.to_dict() for s in self.skills.values()], indent=2)
        elif format.lower() == "yaml":
            return yaml.dump([s.to_dict() for s in self.skills.values()], default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_skills(self, data: str, format: str = "json"):
        """Import skills from specified format."""
        if format.lower() == "json":
            skills_data = json.loads(data)
        elif format.lower() == "yaml":
            skills_data = yaml.safe_load(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        for skill_data in skills_data:
            skill = WFMPluginSkill.from_dict(skill_data)
            self.register_skill(skill)
