import pytest
from unittest.mock import patch, MagicMock
from graph.workflow import _call_tool, MAX_ITERATIONS
from skills.registry_impl import register


def test_call_tool_success():
    @register("mock_weather")
    def mock_weather(city: str) -> str:
        return f"{city}:晴"

    span = MagicMock()
    result = _call_tool("mock_weather", {"city": "北京"}, span)
    assert "北京" in result
    span.event.assert_called_once()


def test_call_tool_retries_on_failure():
    call_count = 0

    @register("flaky_tool")
    def flaky_tool(x: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RuntimeError("临时失败")
        return "成功"

    span = MagicMock()
    result = _call_tool("flaky_tool", {"x": "test"}, span)
    assert result == "成功"
    assert call_count == 2


def test_call_tool_fails_after_retry():
    @register("always_fail")
    def always_fail(x: str) -> str:
        raise RuntimeError("永久失败")

    span = MagicMock()
    result = _call_tool("always_fail", {"x": "test"}, span)
    assert result.startswith("ERROR:")


def test_max_iterations_constant():
    assert MAX_ITERATIONS == 5


def test_call_unknown_tool():
    span = MagicMock()
    result = _call_tool("totally_unknown_tool_xyz", {}, span)
    assert "未实现" in result
