"""工具函数注册表：将工具名映射到可调用的 Python 函数"""
from typing import Callable, Any

_TOOL_IMPL: dict[str, Callable] = {}


def register(name: str):
    """装饰器：注册工具实现函数

    Usage:
        @register("get_weather")
        def get_weather(city: str) -> str:
            return f"{city}：晴"
    """
    def decorator(fn: Callable) -> Callable:
        _TOOL_IMPL[name] = fn
        return fn
    return decorator


def get_impl(name: str) -> Callable | None:
    """根据工具名获取实现函数"""
    return _TOOL_IMPL.get(name)


def list_registered() -> list[str]:
    """列出所有已注册的工具名"""
    return list(_TOOL_IMPL.keys())
