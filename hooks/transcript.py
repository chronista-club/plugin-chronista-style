"""Normalize Claude JSONL and Codex rollout JSONL; transcript schemas are unstable.

Only actual result records count as evidence. Prompts, reasoning, summaries and
tool-call arguments never do. Keep the session-wide evidence / latest-report
semantics of the original tripwire. Reject malformed input rather than checking
against a partially read evidence set.
"""
import json


def text_content(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        for block in value:
            if not isinstance(block, dict) or block.get("type") not in (
                "text", "input_text", "output_text", "image", "input_image",
                "image_url", "audio", "input_audio", "resource", "resource_link",
                "tool_use", "thinking", "redacted_thinking",
            ):
                raise ValueError("Unknown content block")
        return "\n".join(
            block["text"] for block in value
            if isinstance(block, dict)
            and block.get("type") in ("text", "input_text", "output_text")
            and isinstance(block.get("text"), str)
        )
    raise ValueError("Unknown text content shape")


def read_transcript(path):
    prose = ""
    tools = []
    formats = set()
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            kind = row.get("type")
            if kind in ("user", "assistant"):
                formats.add("claude")
                content = row["message"]["content"]
                if kind == "assistant":
                    text = text_content(content)
                    if text:
                        prose = text
                else:
                    results = [block for block in content if isinstance(block, dict)
                               and block.get("type") == "tool_result"] if isinstance(content, list) else []
                    if results:
                        tools.extend(text_content(block["content"]) for block in results)
                    elif not text_content(content).startswith("Stop hook feedback:"):
                        prose = ""
            elif kind == "response_item":
                formats.add("codex")
                item = row["payload"]
                if item["type"] in ("function_call_output", "custom_tool_call_output"):
                    tools.append(text_content(item["output"]))
                elif item["type"] == "message":
                    if item["role"] == "user":
                        prose = ""
                    elif item["role"] == "assistant" and item.get("phase") in (None, "final", "final_answer"):
                        prose = text_content(item["content"])
                elif item["type"].endswith("_output"):
                    raise ValueError("Unknown Codex output record")
            elif kind == "event_msg" and row.get("payload", {}).get("type") == "task_started":
                prose = ""
    if len(formats) != 1:
        raise ValueError("Unknown or mixed transcript format")
    return prose, "\n".join(tools)
