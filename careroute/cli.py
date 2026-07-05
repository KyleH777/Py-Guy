import argparse
import json
import re

from careroute.agent import run_triage

COLORS = {
    "emergency": "\033[1;91m",
    "urgent": "\033[1;93m",
    "routine": "\033[1;94m",
    "self_care": "\033[1;92m",
}
RESET = "\033[0m"


def highlight_urgency(summary: str) -> str:
    pattern = r"^.*urgency level\W+(emergency|urgent|routine|self[\s_-]?care).*$"

    def colorize(match: re.Match) -> str:
        level = re.sub(r"[\s-]", "_", match.group(1).lower())
        return f"{COLORS.get(level, RESET)}{match.group(0)}{RESET}"

    return re.sub(pattern, colorize, summary, flags=re.IGNORECASE | re.MULTILINE)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="careroute",
        description="Run a CareRoute triage session on a free-text complaint.",
    )
    parser.add_argument("complaint", help="Free-text description of the symptoms")
    parser.add_argument("--verbose", action="store_true", help="Also print the tool calls made")
    args = parser.parse_args()

    result = run_triage(args.complaint)

    if args.verbose:
        print(f"Tool calls ({len(result['tool_calls'])}, {result['turns']} turns):")
        for call in result["tool_calls"]:
            print(f"  {call['name']}({json.dumps(call['input'])})")
        print()

    print(highlight_urgency(result["summary"]))


if __name__ == "__main__":
    main()
