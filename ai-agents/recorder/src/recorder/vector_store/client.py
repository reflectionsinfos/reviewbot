"""ChromaDB persistent client singleton."""

from functools import lru_cache

import chromadb
import structlog

from recorder.core.config import settings

logger = structlog.get_logger()


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.PersistentClient:
    logger.info("initialising_chroma", persist_dir=settings.chroma_persist_dir)
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)
