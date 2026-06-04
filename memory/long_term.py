import asyncpg
from anthropic import Anthropic
from config.settings import settings

client = Anthropic(api_key=settings.anthropic_api_key)


def _embed(text: str) -> list[float]:
    # 用 claude embed 接口；若无权限可换 openai text-embedding-3-small
    import openai
    r = openai.OpenAI(api_key=settings.openai_api_key).embeddings.create(
        model="text-embedding-3-small", input=text
    )
    return r.data[0].embedding


class LongTermMemory:
    async def save(self, session_id: str, content: str):
        embedding = _embed(content)
        conn = await asyncpg.connect(settings.database_url)
        try:
            await conn.execute(
                "INSERT INTO memories (session_id, content, embedding) VALUES ($1, $2, $3::vector)",
                session_id, content, str(embedding),
            )
        finally:
            await conn.close()

    async def search(self, query: str, session_id: str, top_k: int = 3) -> list[str]:
        embedding = _embed(query)
        conn = await asyncpg.connect(settings.database_url)
        try:
            rows = await conn.fetch(
                """SELECT content FROM memories
                   WHERE session_id = $1
                   ORDER BY embedding <=> $2::vector
                   LIMIT $3""",
                session_id, str(embedding), top_k,
            )
        finally:
            await conn.close()
        return [r["content"] for r in rows]
