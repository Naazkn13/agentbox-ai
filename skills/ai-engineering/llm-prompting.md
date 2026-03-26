---
id: llm-prompting
name: LLM Prompting Expert
category: ai-engineering
level1: "For LLM prompt engineering, system prompts, few-shot examples, and Claude/OpenAI API patterns"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**LLM Prompting Expert** — Activate for: system prompt design, few-shot examples, chain-of-thought, Claude/OpenAI API, token optimization, structured output, tool use.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## LLM Prompting — Core Instructions

1. **System prompt = persona + rules + format.** Tell the model who it is, what constraints apply, and how to respond.
2. **Be specific about output format.** "Return JSON with fields: {name, score, reason}" beats "return structured data".
3. **Few-shot examples outperform instructions** for complex formatting or classification tasks. Show 2–3 examples.
4. **Chain-of-thought for reasoning:** add "Think step by step before answering" for math, logic, or multi-step tasks.
5. **Temperature:** 0 for deterministic/classification tasks, 0.7 for creative, 1.0 for brainstorming.
6. **Token budget:** put the most important instructions at the start AND end of the prompt (primacy + recency effect).
7. **Test with adversarial inputs** — if users can inject prompts, validate and sanitize before passing to the model.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## LLM Prompting — Full Reference

### System Prompt Structure
```
You are [persona — specific role, not generic].
[Core task or capability in 1–2 sentences.]

Rules:
- [constraint 1]
- [constraint 2]

Output format:
[exact format specification with example]

[Few-shot examples if needed]
```

### Claude API Pattern
```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="You are a helpful assistant that returns JSON only.",
    messages=[
        {"role": "user", "content": "Classify this: 'The product is broken'"}
    ],
)
print(response.content[0].text)
```

### Structured Output (JSON mode)
```python
# Force JSON by specifying in system + pre-filling assistant turn
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    system='Return valid JSON only. Schema: {"sentiment": "positive|negative|neutral", "confidence": 0.0-1.0}',
    messages=[
        {"role": "user", "content": "The product works great!"},
        {"role": "assistant", "content": "{"},  # pre-fill forces JSON
    ],
)
```

### Token Optimization
```python
# Count tokens before sending (avoid surprises)
token_count = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": long_prompt}]
)
print(f"Input tokens: {token_count.input_tokens}")

# Use Haiku for classification/simple tasks (12x cheaper than Sonnet)
ROUTING = {
    "classify": "claude-haiku-4-5-20251001",   # $0.25/M
    "generate": "claude-sonnet-4-6",            # $3/M
    "reason":   "claude-opus-4-6",              # $15/M
}
```

### Prompt Injection Prevention
```python
# Never trust user input in system prompts
# BAD:
system = f"Help the user. Their name is {user_input}."

# GOOD: sanitize and separate user data from instructions
system = "Help the user with coding questions."
user_message = f"User query: {sanitize(user_input)}"
```

### Few-Shot Example Pattern
```
Classify the sentiment of customer feedback.

Examples:
Input: "This is amazing, love it!"
Output: {"sentiment": "positive", "confidence": 0.97}

Input: "Doesn't work at all, very frustrating"
Output: {"sentiment": "negative", "confidence": 0.95}

Input: "It's okay I guess"
Output: {"sentiment": "neutral", "confidence": 0.72}

Now classify:
Input: "{user_feedback}"
Output:
```
<!-- LEVEL 3 END -->
