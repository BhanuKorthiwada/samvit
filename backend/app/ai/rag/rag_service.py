"""RAG service for querying policy documents."""

import logging
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from app.ai.rag.vectorstore import PolicyVectorStore

logger = logging.getLogger(__name__)


class RetrievedContext(BaseModel):
    """A piece of retrieved context from the vector store."""

    content: str = Field(description="The text content of the chunk")
    source: str = Field(description="Source filename")
    policy_id: str = Field(description="ID of the policy document")
    policy_name: str = Field(default="", description="Name of the policy")
    relevance_score: float = Field(description="Relevance score (lower is better)")
    chunk_index: int = Field(default=0, description="Chunk index in the document")


class RAGQueryResult(BaseModel):
    """Result from a RAG query."""

    query: str = Field(description="Original query")
    contexts: list[RetrievedContext] = Field(description="Retrieved context chunks")
    context_text: str = Field(description="Combined context for LLM")
    total_chunks: int = Field(description="Total chunks retrieved")


@dataclass
class RAGConfig:
    """Configuration for RAG queries."""

    max_chunks: int = 5
    relevance_threshold: float = 1.5
    include_sources: bool = True


class PolicyRAGService:
    """Service for RAG-based policy queries."""

    def __init__(
        self,
        tenant_id: str,
        config: RAGConfig | None = None,
    ):
        self.tenant_id = tenant_id
        self.config = config or RAGConfig()
        self.vectorstore = PolicyVectorStore(tenant_id)

    async def retrieve_context(
        self,
        query: str,
        policy_ids: list[str] | None = None,
        max_chunks: int | None = None,
    ) -> RAGQueryResult:
        """Retrieve relevant context for a query.

        Args:
            query: The user's question
            policy_ids: Optional filter to specific policies
            max_chunks: Override default max chunks

        Returns:
            RAGQueryResult with retrieved contexts
        """
        n_results = max_chunks or self.config.max_chunks

        results = self.vectorstore.query(
            query_text=query,
            n_results=n_results,
            policy_ids=policy_ids,
        )

        contexts = []
        for result in results:
            if result["distance"] <= self.config.relevance_threshold:
                metadata = result["metadata"]
                contexts.append(
                    RetrievedContext(
                        content=result["content"],
                        source=metadata.get("filename", "unknown"),
                        policy_id=metadata.get("policy_id", ""),
                        policy_name=metadata.get("policy_name", ""),
                        relevance_score=result["distance"],
                        chunk_index=metadata.get("chunk_index", 0),
                    )
                )

        context_text = self._build_context_text(contexts)

        return RAGQueryResult(
            query=query,
            contexts=contexts,
            context_text=context_text,
            total_chunks=len(contexts),
        )

    def _build_context_text(self, contexts: list[RetrievedContext]) -> str:
        """Build combined context text for LLM prompt."""
        if not contexts:
            return "No relevant policy documents found."

        parts = ["Relevant policy information:\n"]

        seen_sources = set()
        for ctx in contexts:
            source_header = ""
            if self.config.include_sources and ctx.source not in seen_sources:
                source_header = f"\n[Source: {ctx.source}]\n"
                seen_sources.add(ctx.source)

            parts.append(f"{source_header}{ctx.content}\n")

        return "\n".join(parts)

    def format_sources(self, contexts: list[RetrievedContext]) -> list[dict[str, Any]]:
        """Format sources for citation in response."""
        sources = {}
        for ctx in contexts:
            if ctx.policy_id not in sources:
                sources[ctx.policy_id] = {
                    "policy_id": ctx.policy_id,
                    "policy_name": ctx.policy_name or ctx.source,
                    "source_file": ctx.source,
                    "chunks_used": 0,
                }
            sources[ctx.policy_id]["chunks_used"] += 1

        return list(sources.values())
