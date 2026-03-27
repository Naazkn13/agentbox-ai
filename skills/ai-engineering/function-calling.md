---
id: function-calling
name: Function Calling / Tool Use Expert
category: ai-engineering
level1: "For LLM function calling and tool use — schema design, parallel tools, error handling, streaming"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 2
---

<!-- LEVEL 1 START -->
**Function Calling / Tool Use Expert** — Activate for: LLM tool use, function calling, OpenAI tools, Anthropic tool_use, building tool loops, parallel tool calls, tool schema design, agentic workflows, structured outputs from LLMs.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Function Calling / Tool Use Expert — Core Instructions

1. **Write descriptions as if explaining to a smart intern** — the model decides when to call a tool based entirely on the description. Include when to use it, what it returns, and any limits (max items, rate limits).
2. **Make parameters unambiguous and typed** — every parameter needs a `description`, a `type`, and `enum` where applicable. Ambiguous schemas produce hallucinated arguments.
3. **Handle tool errors explicitly** — return a structured error object from the tool, do not throw an exception that crashes the loop. The model can recover from a clean error message; a Python traceback confuses it.
4. **Prefer parallel tool calls for independent operations** — modern models can call multiple tools in one turn. Batch reads, lookups, and fetches that don't depend on each other.
5. **Use `tool_choice: required` sparingly** — forcing a tool call is useful for structured extraction but breaks natural conversation. Default to `auto`.
6. **Test your tool loop to completion** — many bugs only appear after 3–4 tool turns. Write integration tests that run the full loop with a mock tool executor.
7. **Cap your agentic loops** — always enforce a maximum number of turns (e.g., 10) to prevent infinite loops on ambiguous tasks. Log every tool call for debugging.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Function Calling / Tool Use Expert — Full Reference

### OpenAI Tool Schema Format

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_orders",
            "description": (
                "Search customer orders by status or date range. "
                "Use this when the user asks about their orders, shipments, or purchase history. "
                "Returns up to 20 matching orders sorted by date descending."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "shipped", "delivered", "cancelled"],
                        "description": "Filter by order status. Omit to return all statuses."
                    },
                    "since_date": {
                        "type": "string",
                        "description": "ISO 8601 date string (YYYY-MM-DD). Only return orders placed on or after this date."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of orders to return. Default 10, max 20.",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    }
]
```

### Anthropic tool_use Format

```python
import anthropic

client = anthropic.Anthropic()

tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city. Returns temperature in Celsius, conditions, and humidity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'London' or 'New York'"
                },
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit. Defaults to celsius."
                }
            },
            "required": ["city"]
        }
    }
]

response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}]
)
```

### Parallel Tool Calls

```python
# OpenAI — model may return multiple tool calls in one response
from openai import OpenAI
import json

client = OpenAI()

def run_tool(name: str, args: dict) -> str:
    if name == "get_weather":
        return json.dumps({"temp": 22, "conditions": "sunny"})
    if name == "get_stock_price":
        return json.dumps({"price": 182.5, "change": "+1.2%"})
    return json.dumps({"error": f"Unknown tool: {name}"})

def tool_loop(messages: list, tools: list, max_turns: int = 10) -> str:
    for turn in range(max_turns):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        msg = response.choices[0].message

        if msg.tool_calls is None:
            return msg.content  # final answer

        # Process ALL tool calls (potentially parallel)
        messages.append(msg)
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = run_tool(tc.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result
            })

    raise RuntimeError(f"Tool loop exceeded {max_turns} turns")
```

### Handling Tool Errors Gracefully

```python
# Return errors as structured content — let the model decide how to proceed
def search_database(query: str, limit: int = 10) -> dict:
    try:
        results = db.search(query, limit=limit)
        return {"success": True, "results": results, "count": len(results)}
    except DatabaseTimeout:
        return {
            "success": False,
            "error": "database_timeout",
            "message": "The database query timed out. Try a more specific query or smaller limit.",
            "retry_suggested": True
        }
    except InvalidQuery as e:
        return {
            "success": False,
            "error": "invalid_query",
            "message": f"Query syntax error: {str(e)}. Use plain text keywords, not SQL.",
            "retry_suggested": False
        }

# The model reads the error message and can retry with a refined query
# rather than crashing the entire session
```

### tool_choice Modes

```python
# auto (default) — model decides when to use tools
tool_choice = "auto"

# required — model MUST call at least one tool (useful for structured extraction)
tool_choice = "required"

# specific tool — force the model to call a specific function
tool_choice = {"type": "function", "function": {"name": "extract_fields"}}

# none — disable all tools for this turn
tool_choice = "none"
```

```python
# Anthropic equivalents
# auto: let model decide
tool_choice = {"type": "auto"}

# force any tool
tool_choice = {"type": "any"}

# force specific tool
tool_choice = {"type": "tool", "name": "extract_fields"}
```

### Streaming with Tool Calls

```python
# OpenAI streaming — tool arguments arrive in chunks
from openai import OpenAI
import json

client = OpenAI()

def stream_with_tools(messages, tools):
    tool_call_accumulator = {}

    with client.chat.completions.stream(
        model="gpt-4o",
        messages=messages,
        tools=tools
    ) as stream:
        for chunk in stream:
            delta = chunk.choices[0].delta

            # Accumulate streaming tool call arguments
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_call_accumulator:
                        tool_call_accumulator[idx] = {
                            "id": tc.id,
                            "name": tc.function.name or "",
                            "arguments": ""
                        }
                    if tc.function.arguments:
                        tool_call_accumulator[idx]["arguments"] += tc.function.arguments

            # Text content streams normally
            if delta.content:
                print(delta.content, end="", flush=True)

    # After stream ends, execute accumulated tool calls
    for tc in tool_call_accumulator.values():
        args = json.loads(tc["arguments"])
        result = run_tool(tc["name"], args)
        # append tool result to messages and continue loop
```

### When to Use Tools vs. Few-Shot

| Situation | Use tools | Use few-shot |
|---|---|---|
| Real-time data (weather, stock, DB) | Yes | No |
| Side effects (send email, write file) | Yes | No |
| Structured extraction from text | Yes (with `required`) | Sometimes |
| Format transformation (JSON→CSV) | No | Yes |
| Math that fits in context | No | Yes |
| Decision in a workflow | No | Yes |

Tools are for **retrieval and actions**. Few-shot is for **reasoning patterns and output formats**.

### Building Reliable Tool Loops

```python
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class ToolLoopConfig:
    max_turns: int = 10
    log_tool_calls: bool = True
    allowed_tools: set[str] | None = None  # None = all tools allowed

def safe_tool_loop(messages, tools, config: ToolLoopConfig = ToolLoopConfig()):
    for turn in range(config.max_turns):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        msg = response.choices[0].message

        if msg.tool_calls is None:
            logger.info(f"Loop completed in {turn + 1} turn(s)")
            return msg.content

        for tc in msg.tool_calls:
            tool_name = tc.function.name

            # Enforce allowed tools list for security
            if config.allowed_tools and tool_name not in config.allowed_tools:
                logger.warning(f"Model tried to call disallowed tool: {tool_name}")
                result = {"error": f"Tool '{tool_name}' is not available in this context."}
            else:
                args = json.loads(tc.function.arguments)
                if config.log_tool_calls:
                    logger.info(f"Tool call: {tool_name}({args})")
                result = run_tool(tool_name, args)
                if config.log_tool_calls:
                    logger.info(f"Tool result: {result}")

            messages.append(msg)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result)
            })

    logger.error(f"Tool loop hit max_turns ({config.max_turns}) without finishing")
    raise RuntimeError("Tool loop did not complete within the turn limit")
```

### Testing Tool-Using Agents

```python
import pytest
from unittest.mock import patch

def fake_tool_executor(name: str, args: dict) -> dict:
    """Deterministic fake for integration tests."""
    if name == "search_orders" and args.get("status") == "shipped":
        return {"results": [{"id": "ord-1", "item": "Widget", "status": "shipped"}]}
    return {"results": []}

def test_order_lookup_end_to_end():
    messages = [{"role": "user", "content": "Show me my shipped orders"}]

    with patch("myapp.agent.run_tool", side_effect=fake_tool_executor):
        result = tool_loop(messages, tools=ORDER_TOOLS, max_turns=5)

    assert "ord-1" in result or "Widget" in result
    # Verify the loop didn't exceed expected turns
    assert len(messages) <= 10  # user + assistant + tool_result + final

def test_tool_loop_handles_error_gracefully():
    messages = [{"role": "user", "content": "Search for orders"}]

    def always_errors(name, args):
        return {"success": False, "error": "service_unavailable", "message": "Try again later"}

    with patch("myapp.agent.run_tool", side_effect=always_errors):
        result = tool_loop(messages, tools=ORDER_TOOLS, max_turns=5)

    # Model should tell the user the service is down, not crash
    assert result is not None
    assert "unavailable" in result.lower() or "try again" in result.lower()
```

### Anti-patterns to Avoid
- Tool descriptions that only say what the tool is, not when to use it — the model won't call it at the right time
- Raising exceptions from tool executors — return structured error dicts instead
- No turn limit on the agent loop — one ambiguous task can spin forever
- Tool schemas with optional parameters that aren't marked optional — the model will hallucinate values for them
- Calling tools serially when they could be parallel — triples latency for multi-step lookups
- Logging only errors, not all tool calls — you cannot debug an agent loop you cannot observe
<!-- LEVEL 3 END -->
