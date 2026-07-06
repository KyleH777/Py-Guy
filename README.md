# careroute

An AI intake triage agent built on the Anthropic API with tool calling. It gathers a caller's symptoms, checks them against a local knowledge base, scores urgency deterministically, and routes to a next step — without ever diagnosing.

> **Disclaimer:** CareRoute is a demo project, not medical advice. If you have a medical emergency, call 911 or your local emergency number.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Add your `ANTHROPIC_API_KEY` to `.env` (get one at [platform.claude.com](https://platform.claude.com)).

## Usage

Run a triage session from the command line:

```bash
python -m careroute "I've had a nagging cough for two weeks, mild, no blood"
```

Add `--verbose` to also see the tool calls the agent made:

```bash
python -m careroute --verbose "severe ear pain since last night, 8 out of 10"
```

Or call it from Python:

```python
from careroute.agent import run_triage

result = run_triage("I've had a mild headache for two days")
print(result["summary"])
```

`run_triage` returns `{"summary": str, "tool_calls": list, "turns": int}`.

## Architecture

```
careroute/
├── agent.py     run_triage(): the tool-use loop against the Messages API
├── prompts.py   SYSTEM_PROMPT: triage persona, workflow, and safety rules
├── tools.py     tool schemas (pydantic) + handlers wired into the loop
└── cli.py       argparse entry point (python -m careroute)
data/
└── symptoms.json  20-entry symptom knowledge base (causes + red flags)
evals/
├── cases.json     15 scripted intake scenarios
└── run_evals.py   scores urgency + tool usage per case
tests/             unit tests (mocked API, pure tool logic)
```

The agent loop (`agent.py`) sends the conversation to `claude-sonnet-4-6` with three tools and loops while `stop_reason == "tool_use"`, executing handlers and appending `tool_result` blocks, capped at 8 iterations.

The tools:

| Tool | What it does |
|---|---|
| `lookup_symptoms` | Matches reported symptoms against `data/symptoms.json`; returns possible causes and red-flag indicators |
| `score_urgency` | Pure deterministic logic: red flags → `emergency`; severity ≥ 7 → `urgent`; severity ≥ 4 or duration ≥ 7 days → `routine`; else `self_care` |
| `suggest_appointment` | Returns a clearly-marked demo appointment stub for the urgency level |

Safety behavior comes from the system prompt: red-flag descriptions escalate immediately without follow-up questions, emergency results lead with a 911 instruction, findings are always framed as "possible causes to discuss with a clinician," and every response ends with a disclaimer.

## Tests

```bash
python -m pytest tests/
```

Unit tests mock the API client, so no key or network is needed.

## Evals

```bash
python evals/run_evals.py             # all 15 cases (makes real API calls)
python evals/run_evals.py --limit 3   # cheap partial run
```

Cases cover all four urgency levels, three emergency red-flag scenarios, and two vague inputs where the correct behavior is to ask a clarifying question instead of scoring. The runner checks the urgency in the structured summary and the tools called, prints a results table, and writes `evals/results.json`. Current score: 15/15.
