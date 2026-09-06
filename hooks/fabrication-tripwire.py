"""Stop hook for Claude Code and Codex. Standard-library only; fail open."""
import json
import re
import sys

from transcript import read_transcript


PATTERNS = (
    r"test result:",
    r"[0-9]+ passed[;,]",
    r"all checks were successful",
    r"Squashed and merged",
    r"To github\.com",
    r"[0-9a-f]{7,12}\.\.[0-9a-f]{7,12}",
    r"File created successfully at",
    r"has been updated successfully",
    r"HEAD is now at",
    r"-> (origin/|FETCH_HEAD)",
)


def check(event):
    # One corrective continuation per turn; do not trap either host in a loop.
    if event.get("stop_hook_active") is True:
        return None
    prose, tools = read_transcript(event["transcript_path"])
    if isinstance(event.get("last_assistant_message"), str):
        prose = event["last_assistant_message"]
    if "TRIPWIRE-ACK" in prose.splitlines():
        return None
    violations = []
    for pattern in PATTERNS:
        match = re.search(pattern, prose)
        if match and not re.search(pattern, tools):
            violations.append(f'  - "{match.group()}" [{pattern}]')
    if not violations:
        return None
    return {
        "decision": "block",
        "reason": (
            "FABRICATION TRIPWIRE — the final message contains tool-output-shaped text "
            "with NO matching tool result anywhere in this session:\n"
            + "\n".join(violations)
            + "\nRun the real tool and quote its ACTUAL output, or delete the unbacked text. "
            "For deliberate example quotations, add TRIPWIRE-ACK on a line by itself. "
            "Never report a result you did not observe."
        ),
    }


def main():
    try:
        result = check(json.load(sys.stdin))
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return  # Missing, unreadable, malformed or unsupported logs: fail open.
    if result:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
