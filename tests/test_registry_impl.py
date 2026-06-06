import pytest
from unittest.mock import patch, MagicMock, call
from skills.registry_impl import register, get_impl, list_registered


def test_register_and_get():
    @register("test_tool")
    def my_tool(x: str) -> str:
        return f"result:{x}"

    assert get_impl("test_tool")("hello") == "result:hello"


def test_get_unknown_returns_none():
    assert get_impl("nonexistent_xyz") is None


def test_list_registered():
    @register("another_tool")
    def fn(): pass

    assert "another_tool" in list_registered()
