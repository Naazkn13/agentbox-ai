---
id: eval-testing
name: LLM Eval & Testing Expert
category: ai-engineering
level1: "For LLM evals — assertion-based tests, LLM-as-judge, regression suites, promptfoo/braintrust"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**LLM Eval & Testing Expert** — Activate for: evaluating LLM outputs, LLM-as-judge, promptfoo, braintrust, RAGAS, regression testing after prompt changes, building eval datasets, measuring faithfulness/relevance, tracking eval metrics over time.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## LLM Eval & Testing Expert — Core Instructions

1. **Treat evals as unit tests** — every prompt change must run the eval suite before shipping. Evals are not optional; they are CI.
2. **Start with deterministic assertions** — check exact strings, JSON schema conformance, and format rules before reaching for LLM-as-judge. Deterministic checks are free, instant, and never flaky.
3. **Use LLM-as-judge only for subjective quality** — tone, helpfulness, coherence. Always use a rubric with a numeric scale (1–5), never binary pass/fail without a rubric.
4. **Build your eval dataset from real failures** — every production failure or user complaint becomes a new eval case. Never use synthetic data exclusively.
5. **Measure what ships** — eval outputs, tool call correctness, latency p50/p95, and cost per call. A fast cheap bad answer is still bad.
6. **Track regressions, not just scores** — an absolute score of 4.2/5 means nothing; a drop from 4.5 to 4.2 after a prompt change is a regression and must be investigated.
7. **Separate your eval judge from your application model** — never use the same model to judge its own outputs. Use a different model or provider for the judge.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## LLM Eval & Testing Expert — Full Reference

### Evals as Unit Tests (Deterministic Assertions)

```python
# Deterministic eval — run these first, they never need an LLM judge
import json, re, pytest

def test_output_is_valid_json(llm_fn):
    response = llm_fn("List 3 fruits as a JSON array")
    try:
        parsed = json.loads(response)
        assert isinstance(parsed, list), "Expected a JSON array"
        assert len(parsed) == 3, f"Expected 3 items, got {len(parsed)}"
    except json.JSONDecodeError:
        pytest.fail(f"Response is not valid JSON: {response!r}")

def test_output_matches_schema(llm_fn):
    import jsonschema
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "score": {"type": "number"}},
        "required": ["name", "score"]
    }
    response = llm_fn("Return a name and score as JSON")
    data = json.loads(response)
    jsonschema.validate(data, schema)  # raises if invalid

def test_no_pii_in_output(llm_fn):
    response = llm_fn("Summarize this document: ...")
    assert not re.search(r"\b\d{3}-\d{2}-\d{4}\b", response), "SSN found in output"
    assert "@" not in response, "Email address found in output"

def test_exact_classification(llm_fn):
    cases = [
        ("I love this product!", "positive"),
        ("This is terrible.", "negative"),
        ("It arrived on Tuesday.", "neutral"),
    ]
    for text, expected_label in cases:
        result = llm_fn(f"Classify sentiment (positive/negative/neutral): {text}")
        assert result.strip().lower() == expected_label, \
            f"Expected {expected_label!r}, got {result!r}"
```

### LLM-as-Judge Pattern

```python
# Always use a rubric — never ask "is this good?" — ask against specific criteria
JUDGE_PROMPT = """You are an evaluator. Score the assistant response below on the given criterion.

CRITERION: {criterion}

USER INPUT: {user_input}

ASSISTANT RESPONSE: {response}

RUBRIC:
5 — Fully satisfies the criterion with no issues
4 — Mostly satisfies, minor gap
3 — Partially satisfies, noticeable gap
2 — Barely satisfies, significant issues
1 — Does not satisfy the criterion at all

Respond with JSON only: {{"score": <int>, "reason": "<one sentence>"}}"""

def llm_judge(user_input: str, response: str, criterion: str, judge_llm) -> dict:
    prompt = JUDGE_PROMPT.format(
        criterion=criterion,
        user_input=user_input,
        response=response
    )
    raw = judge_llm.complete(prompt)
    return json.loads(raw)

# Multi-criteria evaluation
def evaluate_response(user_input: str, response: str, judge_llm) -> dict:
    criteria = {
        "helpfulness": "Does the response fully address what the user asked?",
        "accuracy": "Is all factual content in the response correct?",
        "conciseness": "Is the response free of unnecessary filler and repetition?",
    }
    scores = {}
    for name, rubric in criteria.items():
        result = llm_judge(user_input, response, rubric, judge_llm)
        scores[name] = result
    scores["average"] = sum(v["score"] for v in scores.values()) / len(criteria)
    return scores
```

### Dataset-Driven Evals

```python
# eval_dataset.jsonl — one case per line
# {"id": "case-001", "input": "...", "expected_output": "...", "tags": ["classification"]}

import jsonlines

def load_eval_dataset(path: str) -> list[dict]:
    with jsonlines.open(path) as reader:
        return list(reader)

def run_eval_suite(llm_fn, judge_llm, dataset_path: str) -> dict:
    cases = load_eval_dataset(dataset_path)
    results = []
    for case in cases:
        actual = llm_fn(case["input"])
        # Deterministic check first
        exact_match = actual.strip() == case.get("expected_output", "").strip()
        # LLM judge for quality
        judge_result = evaluate_response(case["input"], actual, judge_llm)
        results.append({
            "id": case["id"],
            "exact_match": exact_match,
            "judge_scores": judge_result,
            "actual": actual
        })

    pass_rate = sum(1 for r in results if r["exact_match"]) / len(results)
    avg_quality = sum(r["judge_scores"]["average"] for r in results) / len(results)
    return {"pass_rate": pass_rate, "avg_quality": avg_quality, "cases": results}
```

### RAGAS Metrics for RAG Systems

```python
# pip install ragas
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from datasets import Dataset

# Build evaluation dataset from your RAG pipeline
rag_eval_data = {
    "question": ["What is the capital of France?"],
    "answer": ["The capital of France is Paris."],          # RAG output
    "contexts": [["France is a country in Europe. Paris is its capital city."]],  # retrieved chunks
    "ground_truth": ["Paris"]                               # known correct answer
}

dataset = Dataset.from_dict(rag_eval_data)

result = evaluate(
    dataset=dataset,
    metrics=[faithfulness, answer_relevancy, context_recall]
)
print(result)
# {'faithfulness': 1.0, 'answer_relevancy': 0.97, 'context_recall': 1.0}
```

| RAGAS Metric | Measures | Failure Signal |
|---|---|---|
| Faithfulness | Is the answer grounded in retrieved context? | Hallucination — claims not in context |
| Answer Relevancy | Does the answer address the question? | Off-topic or tangential responses |
| Context Recall | Were all ground truth facts retrieved? | Missing chunks in retrieval |
| Context Precision | Are retrieved chunks relevant? | Noise in retrieval hurting quality |

### promptfoo Configuration

```yaml
# promptfooconfig.yaml
description: "Sentiment classifier eval"

prompts:
  - "Classify the sentiment of this text as positive, negative, or neutral: {{text}}"

providers:
  - openai:gpt-4o
  - anthropic:claude-sonnet-4-5

tests:
  - vars:
      text: "I absolutely love this product!"
    assert:
      - type: equals
        value: "positive"
      - type: latency
        threshold: 2000   # ms

  - vars:
      text: "The service was absolutely terrible."
    assert:
      - type: equals
        value: "negative"

  - vars:
      text: "The package arrived on Monday."
    assert:
      - type: equals
        value: "neutral"
      - type: cost
        threshold: 0.001   # max $0.001 per call
```

```bash
# Run evals
npx promptfoo eval

# Compare two prompt versions
npx promptfoo eval --config promptfooconfig.yaml --output results.json

# View results in browser
npx promptfoo view
```

### Braintrust Experiment Tracking

```python
# pip install braintrust
import braintrust

# Log an experiment run
experiment = braintrust.init(
    project="my-llm-app",
    experiment="prompt-v2-vs-v1"
)

for case in eval_dataset:
    actual = llm_fn(case["input"])
    scores = evaluate_response(case["input"], actual, judge_llm)

    experiment.log(
        input=case["input"],
        output=actual,
        expected=case.get("expected_output"),
        scores={
            "helpfulness": scores["helpfulness"]["score"] / 5,  # normalize to 0-1
            "accuracy": scores["accuracy"]["score"] / 5,
            "exact_match": 1.0 if actual.strip() == case.get("expected_output", "") else 0.0,
        },
        metadata={"model": "claude-sonnet-4-5", "prompt_version": "v2"}
    )

experiment.summarize()
```

### Regression Testing After Prompt Changes

```python
# regression_eval.py — run in CI on every prompt change
import sys

REGRESSION_THRESHOLD = 0.05  # max allowed drop in avg quality score

def check_regression(baseline_results: dict, new_results: dict):
    baseline_score = baseline_results["avg_quality"]
    new_score = new_results["avg_quality"]
    drop = baseline_score - new_score

    print(f"Baseline avg quality: {baseline_score:.3f}")
    print(f"New avg quality:      {new_score:.3f}")
    print(f"Delta:                {-drop:+.3f}")

    if drop > REGRESSION_THRESHOLD:
        print(f"REGRESSION DETECTED: quality dropped {drop:.3f} > threshold {REGRESSION_THRESHOLD}")
        sys.exit(1)
    else:
        print("No regression detected.")

# In CI:
# baseline = load_json("eval_results_main.json")
# new = run_eval_suite(new_llm_fn, judge_llm, "eval_dataset.jsonl")
# check_regression(baseline, new)
```

### What to Eval (Checklist)

- **Output quality** — correctness, helpfulness, tone (LLM-as-judge with rubric)
- **Format conformance** — is the output valid JSON/Markdown/code? (deterministic)
- **Tool call correctness** — did the agent call the right tool with the right args?
- **Latency** — p50 and p95 response time per use case
- **Cost** — tokens consumed per case; flag cases that use 10x average
- **Safety** — no PII, no injections passing through, no policy violations
- **Refusal accuracy** — does the model refuse exactly what it should refuse and nothing more?

### Anti-patterns to Avoid
- Using the same model to generate outputs AND judge them — self-grading inflates scores
- Binary pass/fail judging without a rubric — LLM judges are inconsistent without criteria
- Only evaluating on your training examples — test on held-out data you haven't tuned against
- Ignoring latency and cost metrics — a correct but 30-second response is a product failure
- Running evals manually instead of in CI — prompt regressions ship silently without automation
- Small eval datasets (< 50 cases) — scores are noisy and not statistically meaningful
<!-- LEVEL 3 END -->
