# careroute build plan

1. **Agent loop** — core conversation loop against the Anthropic API with tool-use handling.
2. **Tools** — triage tools (symptom lookup, urgency scoring, routing) with JSON schemas.
3. **Prompts** — system prompt and intake conversation prompts for the triage persona.
4. **Eval harness** — scripted intake scenarios in evals/ scored against expected routing outcomes.
5. **CLI** — interactive command-line entry point for running an intake session.
6. **Docs** — README usage guide, architecture notes, and eval results.
