"""Vector store integration using ChromaDB for RAG."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.ai.rag.document_loader import DocumentChunk
from app.ai.rag.embeddings import compute_content_hash, get_embedding_function

logger = logging.getLogger(__name__)


CHROMA_PERSIST_DIR = Path("data/chroma")
COLLECTION_PREFIX = "policies"


@lru_cache
def get_chroma_client() -> chromadb.PersistentClient:
    """Get or create ChromaDB client with persistent storage."""
    persist_path = CHROMA_PERSIST_DIR
    persist_path.mkdir(parents=True, exist_ok=True)

    chroma_settings = ChromaSettings(
        anonymized_telemetry=False,
        allow_reset=True,
    )

    client = chromadb.PersistentClient(
        path=str(persist_path),
        settings=chroma_settings,
    )

    logger.info("ChromaDB client initialized at %s", persist_path)
    return client


def get_tenant_collection_name(tenant_id: str) -> str:
    """Get collection name for a tenant."""
    safe_id = tenant_id.replace("-", "_")
    return f"{COLLECTION_PREFIX}_{safe_id}"


class PolicyVectorStore:
    """Vector store for tenant policy documents."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.client = get_chroma_client()
        self.collection_name = get_tenant_collection_name(tenant_id)
        self._collection = None

    @property
    def collection(self) -> chromadb.Collection:
        """Get or create the tenant's collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=get_embedding_function(),
                metadata={"tenant_id": self.tenant_id, "type": "policies"},
            )
            logger.debug(
                "Collection '%s' ready with %d documents",
                self.collection_name,
                self._collection.count(),
            )
        return self._collection

    def add_chunks(self, chunks: list[DocumentChunk], policy_id: str) -> int:
        """Add document chunks to the vector store.

        Returns the number of chunks added.
        """
        if not chunks:
            return 0

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = f"{policy_id}::{chunk.chunk_index}"
            content_hash = compute_content_hash(chunk.content)

            metadata = {
                **chunk.metadata,
                "policy_id": policy_id,
                "tenant_id": self.tenant_id,
                "content_hash": content_hash,
            }

            ids.append(chunk_id)
            documents.append(chunk.content)
            metadatas.append(metadata)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(
            "Added %d chunks for policy %s in tenant %s",
            len(chunks),
            policy_id,
            self.tenant_id,
        )
        return len(chunks)

    def delete_policy(self, policy_id: str) -> int:
        """Delete all chunks for a policy.

        Returns the number of chunks deleted.
        """
        results = self.collection.get(
            where={"policy_id": policy_id},
            include=[],
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(
                "Deleted %d chunks for policy %s",
                len(results["ids"]),
                policy_id,
            )
            return len(results["ids"])

        return 0

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        policy_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query the vector store for relevant chunks.

        Args:
            query_text: The query string
            n_results: Maximum number of results to return
            policy_ids: Optional list of policy IDs to filter by

        Returns:
            List of results with content, metadata, and distance
        """
        where_filter = None
        if policy_ids:
            where_filter = {"policy_id": {"$in": policy_ids}}

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append(
                    {
                        "id": doc_id,
                        "content": results["documents"][0][i]
                        if results["documents"]
                        else "",
                        "metadata": results["metadatas"][0][i]
                        if results["metadatas"]
                        else {},
                        "distance": results["distances"][0][i]
                        if results["distances"]
                        else 0,
                    }
                )

        logger.debug(
            "Query returned %d results for tenant %s",
            len(formatted_results),
            self.tenant_id,
        )
        return formatted_results

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        count = self.collection.count()

        policy_counts = {}
        if count > 0:
            all_metadata = self.collection.get(include=["metadatas"])
            for meta in all_metadata["metadatas"] or []:
                policy_id = meta.get("policy_id", "unknown")
                policy_counts[policy_id] = policy_counts.get(policy_id, 0) + 1

        return {
            "tenant_id": self.tenant_id,
            "collection_name": self.collection_name,
            "total_chunks": count,
            "policies": policy_counts,
        }

    def clear(self) -> int:
        """Clear all documents from the collection.

        Returns the number of documents deleted.
        """
        count = self.collection.count()
        if count > 0:
            all_ids = self.collection.get(include=[])["ids"]
            self.collection.delete(ids=all_ids)
            logger.info(
                "Cleared %d documents from collection %s",
                count,
                self.collection_name,
            )
        return count
