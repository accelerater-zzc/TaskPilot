import yaml
from pathlib import Path
from typing import Any

SKILLS_DIR = Path(__file__).parent


class SkillRegistry:
    def __init__(self):
        self._skills: dict[str, dict] = {}
        self._load_all()

    def _load_all(self):
        for f in SKILLS_DIR.glob("*.yaml"):
            data = yaml.safe_load(f.read_text())
            self._skills[data["name"]] = data

    def list_skills(self) -> list[dict]:
        return [{"name": v["name"], "description": v["description"]} for v in self._skills.values()]

    def load_skill(self, name: str) -> list[dict]:
        skill = self._skills.get(name)
        if not skill:
            raise ValueError(f"Skill '{name}' not found")
        return skill.get("tools", [])
