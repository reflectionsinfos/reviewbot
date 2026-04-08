# Project Brain Indexing

## Use When

- implementing document indexing
- implementing code indexing
- building incremental sync
- changing retrieval semantics or metadata

## Current Reality

- `document_indexer.py`, `code_indexer.py`, and `incremental_sync.py` are mostly stubs.
- Chroma client and namespace helpers exist.
- Retrieval helpers already encode the intended separation between transcript, project brain, code, and persona-domain memory.

## Core Invariants

- Profile Card is injected directly. Never store it as a retrieved chunk.
- Raw code is not embedded. Only natural-language summaries go into the code namespace.
- Exclusion rules must run before parsing/indexing.
- Retrieval is role-filtered, especially for code access.
- Stale-index warnings matter; do not hide them.

## Main Files

- `src/recorder/project_brain/document_indexer.py`
- `src/recorder/project_brain/code_indexer.py`
- `src/recorder/project_brain/incremental_sync.py`
- `src/recorder/project_brain/context_injection.py`
- `src/recorder/project_brain/profile_card.py`
- `src/recorder/vector_store/client.py`
- `src/recorder/vector_store/namespaces.py`
- `src/recorder/vector_store/retrieval.py`

## Implementation Order

1. Define chunk/summary metadata clearly.
2. Implement deterministic extraction/parsing.
3. Add embedding/write path to Chroma.
4. Add retrieval filters and stale checks.
5. Only then add LLM-powered summarization polish.

## Common Mistakes

- embedding source code directly
- mixing project-brain and project-code namespace responsibilities
- forgetting file-path or last-modified metadata
- implementing retrieval without role filters

## Minimum Validation

- verify namespace names stay stable
- verify metadata supports stale detection
- verify retrieval still returns empty lists cleanly on missing collections
