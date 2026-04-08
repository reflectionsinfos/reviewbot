"""Code Indexer (PB-3).

AST parse → LLM-generated summaries at each structural level → embed summaries.
Raw code is NEVER embedded — stored on FS, retrieved by path on demand.

Indexing levels:
  module   — file purpose, key classes, external dependencies, docstring
  class    — name, responsibilities, public methods, key attributes
  endpoint — route, method, parameters, response schema, auth requirements
  schema   — table name, columns, types, relationships, constraints, indexes
  config   — key settings and what they control

Role-based access filter applied at retrieval time, not indexing time.
"""

# Implementation: Phase 2
# Skeleton only — AST parsing and LLM summary pipeline to be implemented.

BUILT_IN_EXCLUSIONS = [
    ".env", "secrets/", "credentials/", "*.key", "*.pem",
    "node_modules/", "__pycache__/", "dist/", "build/", ".git/",
    "*.egg-info/", ".venv/", "venv/",
]


async def index_codebase(
    project_id: str,
    repo_path: str,
    excluded_paths: list[str],
) -> int:
    """Index all code in repo_path into project_code_{project_id}.

    Returns the number of summaries generated and embedded.
    Phase 2 implementation.
    """
    raise NotImplementedError("Code indexer — Phase 2")


async def reindex_changed_files(
    project_id: str,
    repo_path: str,
    since_commit: str,
    excluded_paths: list[str],
) -> list[str]:
    """Re-index only files changed since the given git commit.

    Returns list of re-indexed file paths.
    Phase 2 implementation.
    """
    raise NotImplementedError("Incremental code reindex — Phase 2")
