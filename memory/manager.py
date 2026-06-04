from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory


class MemoryManager:
    def __init__(self):
        self.short = ShortTermMemory()
        self.long = LongTermMemory()

    async def get_context(self, session_id: str, query: str) -> str:
        short = self.short.get(session_id)
        long_results = await self.long.search(query, session_id)

        parts = []
        if long_results:
            parts.append("【相关记忆】\n" + "\n".join(f"- {r}" for r in long_results))
        if short:
            history = "\n".join(f"{m['role']}: {m['content']}" for m in short[-6:])
            parts.append(f"【近期对话】\n{history}")
        return "\n\n".join(parts)
