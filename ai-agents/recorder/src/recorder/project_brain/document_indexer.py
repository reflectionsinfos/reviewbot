"""Document Indexer (PB-2).

Crawls and embeds all project documentation into project_brain_{project_id}.

Supported formats: .md, .txt, .pdf, .docx, .html, Confluence, SharePoint
Chunking: 512-token chunks with 64-token overlap, heading-aware.
Each chunk metadata: source_file, section_heading, last_modified

Semantic linking: during indexing, scans docs for references to code components
and stores doc_chunk → code_summary links for retrieval-time surfacing.
"""

# Implementation: Phase 2
# Skeleton only — indexing pipeline to be implemented.

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx", ".html"}

CHUNK_SIZE_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 64


async def index_documents(project_id: str, docs_folder: str, excluded_paths: list[str]) -> int:
    """Index all documents in docs_folder into project_brain_{project_id}.

    Returns the number of chunks indexed.
    Phase 2 implementation.
    """
    raise NotImplementedError("Document indexer — Phase 2")
