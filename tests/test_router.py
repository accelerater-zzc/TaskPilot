import pytest
from unittest.mock import patch, MagicMock
from router.agent import route


@pytest.mark.parametrize("user_input,expected_skill", [
    ("北京今天天气怎么样", "weather"),
    ("帮我明天上午加个会议", "calendar"),
    ("执行这段 Python 代码", "code_run"),
])
def test_route(user_input, expected_skill):
    mock_response = MagicMock()
    mock_response.content[0].text = f'{{"skill": "{expected_skill}"}}'

    with patch("router.agent.client") as mock_client, \
         patch("router.agent.langfuse") as mock_lf:
        mock_client.messages.create.return_value = mock_response
        mock_lf.trace.return_value.span.return_value = MagicMock()
        result = route(user_input, "test_session")

    assert result == expected_skill
