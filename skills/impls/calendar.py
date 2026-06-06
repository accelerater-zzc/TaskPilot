import json
import uuid
from pathlib import Path
from skills.registry_impl import register

DB = Path("data/calendar.json")


def _load() -> list:
    return json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else []


def _save(events: list):
    DB.parent.mkdir(exist_ok=True)
    DB.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")


@register("create_event")
def create_event(title: str, start_time: str, duration_minutes: int = 60) -> str:
    events = _load()
    event = {"id": str(uuid.uuid4()), "title": title, "start": start_time, "duration": duration_minutes}
    events.append(event)
    _save(events)
    return f"已创建：{title} @ {start_time}（{duration_minutes} 分钟）"


@register("list_events")
def list_events(date: str) -> str:
    events = [e for e in _load() if e["start"].startswith(date)]
    if not events:
        return f"{date} 无日程"
    return json.dumps(events, ensure_ascii=False)
