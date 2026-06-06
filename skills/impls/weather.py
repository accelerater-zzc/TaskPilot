import httpx
from skills.registry_impl import register


@register("get_weather")
def get_weather(city: str) -> str:
    """调用 wttr.in 免费天气 API，无需 key"""
    try:
        r = httpx.get(f"https://wttr.in/{city}?format=3&lang=zh", timeout=5)
        r.raise_for_status()
        return r.text.strip()
    except httpx.TimeoutException:
        return f"ERROR: 获取 {city} 天气超时"
    except Exception as e:
        return f"ERROR: {e}"
