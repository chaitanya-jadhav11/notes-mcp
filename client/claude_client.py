
from anthropic import AsyncAnthropic
from dotenv import load_dotenv


load_dotenv()
CLAUDE_MODEL="claude-haiku-4-5-20251001"
client = AsyncAnthropic()

SYSTEM_PROMPT = """
You are a notes assistant.

When the user asks to save, search, or list notes, ALWAYS use the available tools.

Do not make up notes.
Do not answer from memory.
Always call tools when relevant.
"""

async def chat(
    messages,
    system=None,
    stop_sequences=[],
    tools=None,
    thinking=False,
    thinking_budget=1024,
):
    params = {
        "model": CLAUDE_MODEL,
        "max_tokens": 4000,
        "messages": messages,
        "stop_sequences": stop_sequences,
    }

    if thinking:
        params["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget,
        }

    if tools:
        tools_clone = tools.copy()
        last_tool = tools_clone[-1].copy()
        last_tool["cache_control"] = {"type": "ephemeral"}
        tools_clone[-1] = last_tool
        params["tools"] = tools_clone

    params["system"] = [
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}
            }
    ]

    message = await client.messages.create(**params)
    return message


def add_user_message(messages, message, tool_use_id=None):
    """
    Adds user message supporting:
    - plain text
    - Anthropic tool_result
    - MCP tool result
    """

    # ---- CASE 1: Already formatted ----
    if isinstance(message, dict) and "role" in message and "content" in message:
        messages.append(message)
        return messages

    # ---- CASE 2: Tool result (Anthropic / MCP) ----
    if tool_use_id is not None:
        # Normalize MCP result
        if isinstance(message, dict):
            if "content" in message:
                content = message["content"]
            else:
                content = str(message)
        else:
            content = str(message)

        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": content,
                }
            ],
        }

        messages.append(user_message)
        return messages

    # ---- CASE 3: Message object ----
    if hasattr(message, "content"):
        message = message.content

    # ---- CASE 4: Plain text ----
    user_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": str(message)
            }
        ],
    }

    messages.append(user_message)
    return messages



def add_assistant_message(messages, message):
    """
    Appends an assistant message in Anthropic-compatible format.

    Supports:
    - Plain text
    - Tool use (function calling)
    - Mixed structured content
    - Preformatted Anthropic messages
    """

    # ---- CASE 1: Already formatted (pass-through) ----
    if isinstance(message, dict) and "role" in message and "content" in message:
        messages.append(message)
        return messages

    # ---- CASE 2: Claude response object (has .content as blocks) ----
    if hasattr(message, "content"):
        content_blocks = []

        for block in message.content:
            # TEXT BLOCK
            if block.type == "text":
                content_blocks.append({
                    "type": "text",
                    "text": block.text

                })

            # TOOL USE BLOCK (CRITICAL)
            elif block.type == "tool_use":
                content_blocks.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })

        assistant_message = {
            "role": "assistant",
            "content": content_blocks
        }

        messages.append(assistant_message)
        return messages

    # ---- CASE 3: Plain string ----
    if isinstance(message, str):
        assistant_message = {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": message
                }
            ],
        }
        messages.append(assistant_message)
        return messages

    # ---- CASE 4: Fallback (dict / JSON / unknown) ----
    assistant_message = {
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": str(message)
            }
        ],
    }

    messages.append(assistant_message)
    return messages


def convert_mcp_to_tool_result(mcp_result, tool_use_id):
    """
    Converts MCP result object → Anthropic tool_result message
    """

    content_blocks = []

    # Handle MCP structured content
    if hasattr(mcp_result, "content") and mcp_result.content:
        for item in mcp_result.content:
            # Handle TextContent
            if hasattr(item, "type") and item.type == "text":
                content_blocks.append({
                    "type": "text",
                    "text": item.text
                })
            else:
                # fallback for unknown types
                content_blocks.append({
                    "type": "text",
                    "text": str(item)
                })

    # Fallback if no content
    if not content_blocks:
        content_blocks = [{
            "type": "text",
            "text": str(mcp_result)
        }]

    return {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": content_blocks
            }
        ]
    }

