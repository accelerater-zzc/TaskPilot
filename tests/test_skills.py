import pytest
from skills import SkillRegistry


def test_list_skills():
    r = SkillRegistry()
    names = [s["name"] for s in r.list_skills()]
    assert set(names) >= {"weather", "calendar", "code_run"}


def test_load_skill():
    r = SkillRegistry()
    tools = r.load_skill("weather")
    assert tools[0]["name"] == "get_weather"


def test_load_unknown_skill():
    r = SkillRegistry()
    with pytest.raises(ValueError):
        r.load_skill("nonexistent")
