import redis
from config.settings import settings

_redis = redis.from_url(settings.redis_url, decode_responses=True)
WINDOW = 10


class ShortTermMemory:
    def add(self, session_id: str, role: str, content: str):
        key = f"mem:{session_id}"
        _redis.rpush(key, f"{role}:{content}")
        _redis.ltrim(key, -WINDOW, -1)
        _redis.expire(key, 86400)

    def get(self, session_id: str) -> list[dict]:
        key = f"mem:{session_id}"
        items = _redis.lrange(key, 0, -1)
        messages = []
        for item in items:
            role, _, content = item.partition(":")
            messages.append({"role": role, "content": content})
        return messages
