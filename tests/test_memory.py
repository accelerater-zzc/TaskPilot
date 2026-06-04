import pytest
from unittest.mock import MagicMock, patch
from memory.short_term import ShortTermMemory


def test_short_term_add_and_get():
    with patch("memory.short_term._redis") as mock_redis:
        mock_redis.lrange.return_value = ["user:hello", "assistant:hi"]
        mem = ShortTermMemory()
        mem.add("s1", "user", "hello")
        result = mem.get("s1")
        assert result == [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
