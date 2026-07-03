import os

import anthropic
from dotenv import load_dotenv

from careroute.tools import HANDLERS, TOOLS

MODEL = "claude-sonnet-4-6"
MAX_TURNS = 8
SYSTEM_PROMPT = (
    "You are CareRoute, an AI intake triage assistant. Gather the caller's "
    "symptoms, assess urgency, and route them to the appropriate level of "
    "care. Use the available tools when they would improve your assessment. "
    "You do not diagnose; you triage and route."
)


def _get_client() -> anthropic.Anthropic:
    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return anthropic.Anthropic(api_key=api_key)


def _execute_tool(block) -> dict:
    handler = HANDLERS.get(block.name)
    if handler is None:
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": f"Unknown tool: {block.name}",
            "is_error": True,
        }
    try:
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": str(handler(**block.input)),
        }
    except Exception as exc:
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": f"Tool error: {exc}",
            "is_error": True,
        }


def run_triage(user_input: str) -> dict:
    client = _get_client()
    messages = [{"role": "user", "content": user_input}]
    tool_calls = []
    turns = 0
    response = None

    while turns < MAX_TURNS:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        turns += 1
        if response.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append({"name": block.name, "input": block.input})
                tool_results.append(_execute_tool(block))
        messages.append({"role": "user", "content": tool_results})

    summary = next((b.text for b in response.content if b.type == "text"), "")
    return {"summary": summary, "tool_calls": tool_calls, "turns": turns}
