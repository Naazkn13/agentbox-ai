---
id: rag-pipeline
name: RAG Pipeline Expert
category: ai-engineering
level1: "For RAG pipelines — chunking, embeddings, vector stores, retrieval, reranking, evaluation"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 2
---

<!-- LEVEL 1 START -->
**RAG Pipeline Expert** — Activate for: retrieval-augmented generation, vector search, embeddings, chunking documents, semantic search, reranking, RAG evaluation, building knowledge bases for LLMs.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## RAG Pipeline Expert — Core Instructions

1. **Choose chunking strategy based on document structure** — fixed-size for uniform prose, recursive/semantic for structured docs with headers, sentence-window for Q&A. Wrong chunking is the most common cause of poor retrieval.
2. **Match embedding model to your domain** — `text-embedding-3-small` (OpenAI) for general English, `voyage-ai` for code and technical content, multilingual-e5 for non-English. Never mix embedding models between indexing and query time.
3. **Use hybrid search (BM25 + dense) for production** — pure dense retrieval misses exact keyword matches; BM25 alone misses semantic similarity. Combine both with Reciprocal Rank Fusion (RRF).
4. **Add a reranker as the final retrieval step** — retrieve top-50 with vector search, rerank with Cohere Rerank or a cross-encoder, pass top-5 to the LLM. Reranking is the highest-ROI improvement for most RAG systems.
5. **Inject context with clear delimiters** — wrap retrieved chunks in XML-style tags (`<document>`, `<source>`) so the LLM can distinguish retrieved facts from its prior knowledge.
6. **Evaluate with RAG-specific metrics** — faithfulness (does the answer come from the context?), answer relevance (does it answer the question?), and context recall (did retrieval fetch the right chunks?). Use RAGAS or TruLens.
7. **Store metadata with every chunk** — source URL, document ID, section, page number, creation date. Metadata filtering at query time is often faster and more precise than semantic search alone.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## RAG Pipeline Expert — Full Reference

### Chunking Strategies

**Fixed-size chunking** — split every N tokens with an overlap window. Simple, predictable, good baseline.
```python
from langchain.text_splitter import TokenTextSplitter

splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=64)
chunks = splitter.split_text(document_text)
# Use when: uniform prose, PDFs without clear structure
```

**Recursive character splitter** — tries to split on paragraphs, then sentences, then words. Respects natural boundaries.
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""]
)
chunks = splitter.split_documents(docs)
# Use when: markdown, HTML, documents with headers
```

**Semantic chunking** — split on embedding similarity drops between sentences. Best retrieval quality, highest cost.
```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

splitter = SemanticChunker(
    OpenAIEmbeddings(),
    breakpoint_threshold_type="percentile",  # or "standard_deviation"
    breakpoint_threshold_amount=95
)
chunks = splitter.split_text(document_text)
# Use when: quality matters more than indexing cost
```

**Chunking rules of thumb:**
- Chunk size should be 2–3x the typical answer length
- Overlap of 10–15% prevents splitting a key sentence across two chunks
- Store the parent document ID so you can fetch surrounding context at query time

### Embedding Models

| Model | Best for | Dimensions | Notes |
|---|---|---|---|
| `text-embedding-3-small` | General English, low cost | 1536 | Good default |
| `text-embedding-3-large` | High accuracy needs | 3072 | 2–3x cost of small |
| `voyage-ai/voyage-code-2` | Code, technical docs | 1536 | Best for code search |
| `intfloat/multilingual-e5-large` | Non-English content | 1024 | Open-source |
| `BAAI/bge-m3` | Hybrid dense+sparse | 1024 | Supports BM25 natively |

```python
# OpenAI embeddings
from openai import OpenAI
client = OpenAI()

response = client.embeddings.create(
    model="text-embedding-3-small",
    input=["chunk text here"],
    dimensions=1536  # can reduce for storage savings
)
embedding = response.data[0].embedding
```

### Vector Store Comparison

| Store | Best for | Hosting | Filtering |
|---|---|---|---|
| pgvector | Already using Postgres | Self-hosted | Full SQL WHERE |
| Pinecone | Managed, high scale | SaaS | Metadata filters |
| Chroma | Local dev, prototyping | Self-hosted | Basic filters |
| Weaviate | Hybrid search built-in | Self/cloud | GraphQL |
| Qdrant | High performance, on-prem | Self-hosted | Rich payload filters |

```python
# pgvector example — add to existing Postgres
# CREATE EXTENSION vector;
# ALTER TABLE documents ADD COLUMN embedding vector(1536);

import psycopg2
import numpy as np

def search_similar(query_embedding, top_k=20):
    with psycopg2.connect(DB_URL) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, content, metadata,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM documents
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding, query_embedding, top_k))
        return cur.fetchall()
```

### Hybrid Search with Reciprocal Rank Fusion

```python
from rank_bm25 import BM25Okapi

def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    """Merge multiple ranked lists into one using RRF."""
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)

def hybrid_search(query: str, top_k: int = 50) -> list[str]:
    # Dense retrieval
    query_embedding = embed(query)
    dense_results = vector_store.search(query_embedding, top_k=top_k)
    dense_ids = [r.id for r in dense_results]

    # Sparse retrieval (BM25)
    tokenized_query = query.lower().split()
    bm25_scores = bm25_index.get_scores(tokenized_query)
    bm25_ids = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
    bm25_ids = [str(i) for i in bm25_ids]

    # Fuse
    return reciprocal_rank_fusion([dense_ids, bm25_ids])
```

### Reranking

```python
import cohere

co = cohere.Client(api_key=COHERE_API_KEY)

def rerank(query: str, candidates: list[dict], top_n: int = 5) -> list[dict]:
    """Rerank top-50 candidates from retrieval down to top-5 for LLM context."""
    results = co.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=[c["content"] for c in candidates],
        top_n=top_n,
    )
    return [candidates[r.index] for r in results.results]

# Full pipeline
candidates = hybrid_search(query, top_k=50)   # retrieve broadly
final_chunks = rerank(query, candidates, top_n=5)  # rerank tightly
```

### Context Injection Patterns

```python
def build_prompt(query: str, chunks: list[dict]) -> str:
    context_blocks = "\n\n".join(
        f"<document id='{c['id']}' source='{c['source']}'>\n{c['content']}\n</document>"
        for c in chunks
    )
    return f"""Answer the question using only the documents below.
If the answer is not in the documents, say "I don't know."

{context_blocks}

Question: {query}
Answer:"""
```

### RAG Evaluation Metrics

```python
# Using RAGAS (pip install ragas)
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from datasets import Dataset

eval_data = Dataset.from_dict({
    "question": ["What is the refund policy?"],
    "answer": ["Refunds are processed within 5 business days."],
    "contexts": [["Our refund policy allows returns within 30 days..."]],
    "ground_truth": ["Refunds take 5 business days after approval."]
})

results = evaluate(eval_data, metrics=[faithfulness, answer_relevancy, context_recall])
print(results)
# faithfulness: 0.0–1.0 (is the answer grounded in context?)
# answer_relevancy: 0.0–1.0 (does the answer address the question?)
# context_recall: 0.0–1.0 (did retrieval surface the relevant chunks?)
```

### Common Failure Modes

| Symptom | Root cause | Fix |
|---|---|---|
| Answer contradicts retrieved docs | LLM using prior knowledge | Reinforce in prompt: "use ONLY the documents" |
| Relevant doc not retrieved | Chunk too large, key info buried | Smaller chunks + metadata filters |
| Retrieval returns irrelevant results | Embedding model mismatch | Match model to domain; add reranker |
| Slow query latency | No HNSW index on vector column | `CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)` |
| Answer cuts off mid-sentence | Context window overflow | Reduce top-k, compress chunks with summarization |
| Numbers/dates wrong | Stale index | Track `last_updated` metadata; re-index on source changes |

### Anti-patterns to Avoid
- Using the same chunk size for all document types — PDFs, code, and chat logs need different strategies
- Forgetting to store metadata — you'll need source attribution and date filtering before you know it
- Skipping reranking to save cost — it's a single API call that routinely improves precision by 20–40%
- Evaluating only with human eye-balling — automated RAGAS scores catch regressions in CI
- Indexing duplicate content — deduplicate by content hash before embedding or retrieval noise increases
<!-- LEVEL 3 END -->
