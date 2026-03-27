---
id: agent-design
name: AI Agent Design Expert
category: ai-engineering
level1: "For designing AI agents — ReAct loops, memory types, multi-agent orchestration, guardrails"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**AI Agent Design Expert** — Activate for: designing AI agents, ReAct pattern, multi-agent systems, agent memory, tool calling loops, agent guardrails, cost control for agents, orchestrator/subagent architecture.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## AI Agent Design Expert — Core Instructions

1. **Use the ReAct loop explicitly** — every agent step is Reason → Act → Observe. Never skip the Observe step; feed tool results back into context before the next Reason.
2. **Choose the right memory type** — working memory (context window), episodic memory (retrieved past runs), semantic memory (vector DB facts). Don't overload the context window with all three at once.
3. **Define tool contracts precisely** — every tool must have a typed schema, description, and documented failure modes. Ambiguous tool descriptions cause hallucinated calls.
4. **Set hard step limits** — every agent loop must have a max_steps guard. Unbounded loops exhaust tokens and budgets silently.
5. **Validate inputs AND outputs** — apply guardrails on the way in (injection detection, scope enforcement) and on the way out (no PII leakage, format conformance).
6. **Route to cheaper models for subagents** — orchestrators need large-context reasoning; leaf task agents (summarize, classify, format) can use smaller, faster models.
7. **Test agents like distributed systems** — unit-test each tool in isolation, integration-test tool sequences, and chaos-test with injected tool failures and malformed outputs.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## AI Agent Design Expert — Full Reference

### ReAct Pattern (Reason + Act + Observe)

The ReAct loop is the foundational control flow for tool-using agents. Each iteration must complete all three phases before proceeding.

```python
# Minimal ReAct loop skeleton
def react_loop(agent_llm, tools: dict, task: str, max_steps: int = 10):
    memory = [{"role": "user", "content": task}]
    for step in range(max_steps):
        response = agent_llm.chat(memory, tools=list(tools.values()))

        # Reason phase: model emits either a tool call or a final answer
        if response.stop_reason == "end_turn":
            return response.text  # final answer

        # Act phase: execute the chosen tool
        tool_call = response.tool_use
        tool_fn = tools.get(tool_call.name)
        if tool_fn is None:
            result = {"error": f"Unknown tool: {tool_call.name}"}
        else:
            try:
                result = tool_fn(**tool_call.input)
            except Exception as e:
                result = {"error": str(e)}

        # Observe phase: return result to context
        memory.append({"role": "assistant", "content": response.raw_content})
        memory.append({
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tool_call.id, "content": str(result)}]
        })

    raise RuntimeError(f"Agent exceeded max_steps={max_steps} without resolving task")
```

### Agent Memory Types

| Type | Storage | Use Case | Retrieval |
|---|---|---|---|
| Working | Context window | Current task state | Direct (always present) |
| Episodic | Vector DB / DB | Past run summaries | Semantic search on task |
| Semantic | Vector DB | Domain facts, docs | Semantic search on query |
| Procedural | Prompt / skill file | How to use tools | Injected at task start |

```python
# Episodic memory injection pattern
def build_context_with_memory(task: str, memory_store, top_k: int = 3) -> list[dict]:
    # Retrieve relevant past episodes
    similar_runs = memory_store.search(task, k=top_k)
    memory_block = "\n".join(
        f"- Past run: {r['summary']} → outcome: {r['outcome']}"
        for r in similar_runs
    )
    system = f"""You are an agent. Relevant past experience:
{memory_block}

Use past patterns to inform your approach, but do not repeat past mistakes."""
    return [{"role": "system", "content": system}, {"role": "user", "content": task}]
```

### Multi-Agent Patterns

**Orchestrator + Subagents** — The orchestrator plans and delegates; subagents execute atomic tasks. Subagents never talk to each other directly.

```python
# Orchestrator delegates via tool calls
ORCHESTRATOR_TOOLS = [
    {
        "name": "delegate_to_researcher",
        "description": "Ask the research subagent to gather information on a topic. Returns a structured summary.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    },
    {
        "name": "delegate_to_coder",
        "description": "Ask the coding subagent to write or fix code. Returns code + explanation.",
        "input_schema": {"type": "object", "properties": {"task": {"type": "string"}, "context": {"type": "string"}}, "required": ["task"]}
    }
]

def researcher_subagent(query: str) -> dict:
    # Subagent uses a smaller model — only needs to search + summarize
    result = react_loop(cheap_llm, search_tools, task=query, max_steps=5)
    return {"summary": result}
```

**Handoff Protocol** — When one agent hands off to another, pass a structured context packet, not raw conversation history.

```python
# Handoff packet — always structured, never raw history
handoff = {
    "task_id": "run-123",
    "original_goal": "Refactor auth module",
    "work_completed": ["Read auth.py", "Identified 3 issues"],
    "current_subtask": "Fix token expiry bug on line 47",
    "relevant_files": ["src/auth.py"],
    "constraints": ["Do not change the public API signature"]
}
```

### Guardrails

**Input guardrails** — run before the agent acts on user input.

```python
import re

INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"you are now",
    r"disregard your (system )?prompt",
]

def input_guardrail(user_input: str) -> str:
    lower = user_input.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower):
            raise ValueError(f"Input failed guardrail: possible injection attempt")
    if len(user_input) > 10_000:
        raise ValueError("Input exceeds maximum allowed length")
    return user_input
```

**Output guardrails** — run before returning to the user.

```python
import json

PII_PATTERNS = [r"\b\d{3}-\d{2}-\d{4}\b", r"\b[A-Z]{2}\d{6}\b"]  # SSN, passport

def output_guardrail(response: str) -> str:
    for pattern in PII_PATTERNS:
        if re.search(pattern, response):
            raise ValueError("Output guardrail: PII detected in response")
    # Enforce JSON output format when required
    try:
        json.loads(response)
    except json.JSONDecodeError:
        raise ValueError("Output guardrail: expected JSON, got free text")
    return response
```

### Cost Control

```python
# Model routing — route by task complexity
def route_model(task_type: str) -> str:
    routing = {
        "plan": "claude-opus-4-5",        # complex reasoning
        "summarize": "claude-haiku-3-5",   # cheap, fast
        "classify": "claude-haiku-3-5",
        "code_review": "claude-sonnet-4-5",
        "default": "claude-sonnet-4-5"
    }
    return routing.get(task_type, routing["default"])

# Token budget enforcement
def enforce_budget(messages: list, max_tokens: int = 8000) -> list:
    """Trim oldest non-system messages when context grows too large."""
    total = sum(len(m["content"]) // 4 for m in messages)  # rough token estimate
    while total > max_tokens and len(messages) > 2:
        # Remove oldest non-system message
        messages = [messages[0]] + messages[2:]
        total = sum(len(m["content"]) // 4 for m in messages)
    return messages
```

### When Agents Fail

| Failure Mode | Symptom | Fix |
|---|---|---|
| Infinite loop | step counter hits max | Set max_steps, add progress assertion each step |
| Hallucinated tool call | tool name not in registry | Validate tool name before execution, return error result |
| Context overflow | API returns context length error | Summarize and compress history every N steps |
| Tool returns ambiguous data | Agent reasks same question | Enforce typed return schemas on all tools |
| Stuck subagent | Subagent returns no answer | Set per-subagent timeout; escalate to orchestrator |

### Testing Agents

```python
# Unit test a single tool
def test_search_tool():
    result = search_tool(query="Python typing module")
    assert isinstance(result, list)
    assert all("url" in r and "snippet" in r for r in result)

# Integration test: tool sequence
def test_research_then_summarize_sequence():
    agent = react_loop(llm, tools={"search": search_tool, "summarize": summarize_tool},
                       task="Summarize the latest news on LLM evals")
    assert len(agent) > 50  # non-trivial answer

# Chaos test: inject tool failure
def test_agent_handles_tool_error():
    def broken_tool(**kwargs):
        raise ConnectionError("Service unavailable")

    # Agent should recover, not crash
    result = react_loop(llm, tools={"search": broken_tool},
                        task="Search for X", max_steps=3)
    assert "error" in result.lower() or "unable" in result.lower()
```

### Anti-patterns to Avoid
- Putting entire conversation history into every subagent call — pass structured handoff packets instead
- Tools with vague descriptions like "does stuff with the database" — models hallucinate calls with unclear contracts
- No max_steps limit — a misbehaving agent will silently drain your API budget
- Catching all exceptions in tool executors and returning empty strings — always return `{"error": "..."}` so the agent can reason about failures
- Using the same large model for every step — route cheap tasks to cheap models
- Testing only the happy path — agents fail at boundaries; always test malformed inputs and tool errors
<!-- LEVEL 3 END -->
