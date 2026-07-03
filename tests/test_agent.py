from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from careroute.agent import run_triage


def test_loop_exits_on_end_turn():
    response = SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text="Route to primary care.")],
    )
    client = MagicMock()
    client.messages.create.return_value = response

    with patch("careroute.agent._get_client", return_value=client):
        result = run_triage("I have a mild headache.")

    assert result == {
        "summary": "Route to primary care.",
        "tool_calls": [],
        "turns": 1,
    }
    client.messages.create.assert_called_once()
