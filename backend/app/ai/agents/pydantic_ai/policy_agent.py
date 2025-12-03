"""Policy Assistant Agent using Pydantic AI with RAG."""

import logging
from dataclasses import dataclass
from functools import cache
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag.rag_service import PolicyRAGService, RAGConfig
from app.core.config import settings
from app.modules.policies.repository import PolicyRepository

logger = logging.getLogger(__name__)


class PolicySource(BaseModel):
    """Source citation for policy answer."""

    policy_name: str
    source_file: str
    relevance: str


class PolicyAgentResponse(BaseModel):
    """Response from the policy agent."""

    answer: str = Field(description="The answer to the user's question")
    sources: list[PolicySource] = Field(
        default_factory=list,
        description="Sources used to generate the answer",
    )
    confidence: str = Field(
        default="medium",
        description="Confidence level: high, medium, low",
    )
    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions",
    )


@dataclass
class PolicyAgentDeps:
    """Dependencies for the policy agent."""

    session: AsyncSession
    tenant_id: str
    user_id: str
    rag_service: PolicyRAGService


POLICY_SYSTEM_PROMPT = """You are a Policy Assistant for SAMVIT HRMS. Your role is to help employees understand company policies by answering their questions accurately based on the organization's policy documents.

Guidelines:
1. **Accuracy First**: Only provide information that is explicitly stated in the policy documents. Do not make assumptions or provide generic advice.

2. **Source Citation**: When answering, reference the specific policy document(s) you're using.

3. **Clarity**: Explain policies in simple, easy-to-understand language while maintaining accuracy.

4. **Completeness**: If a question requires information from multiple policies, synthesize the information coherently.

5. **Limitations**: If the policy documents don't contain information to answer a question, clearly state that and suggest who the employee might contact (HR department, manager, etc.).

6. **Privacy**: Be mindful that some policy details might be sensitive. Stick to what's in the documents.

7. **Follow-ups**: Suggest relevant follow-up questions that might help the employee understand the topic better.

When answering:
- Start with a direct answer to the question
- Provide relevant details and context from the policies
- Note any important exceptions or conditions
- Cite your sources
- Suggest related questions if applicable

If no relevant policy information is found, respond with:
"I couldn't find specific policy information about that topic in our documents. Please contact the HR department for assistance."
"""


@cache
def get_policy_agent() -> Agent[PolicyAgentDeps, PolicyAgentResponse]:
    """Get or create the Policy Agent instance."""
    agent = Agent(
        model=settings.ai_model,
        system_prompt=POLICY_SYSTEM_PROMPT,
        deps_type=PolicyAgentDeps,
        output_type=PolicyAgentResponse,
        retries=2,
    )
    _register_tools(agent)
    return agent


def _register_tools(agent: Agent[PolicyAgentDeps, PolicyAgentResponse]) -> None:
    """Register RAG tools on the agent."""

    @agent.tool
    async def search_policies(
        ctx: RunContext[PolicyAgentDeps],
        query: str,
        max_results: int = 5,
    ) -> dict[str, Any]:
        """
        Search policy documents for information relevant to a query.

        Args:
            query: The search query or question about policies
            max_results: Maximum number of relevant chunks to return

        Returns:
            Dictionary containing relevant policy excerpts and metadata
        """
        rag_result = await ctx.deps.rag_service.retrieve_context(
            query=query,
            max_chunks=max_results,
        )

        if not rag_result.contexts:
            return {
                "found": False,
                "message": "No relevant policy information found.",
                "context": "",
                "sources": [],
            }

        sources = ctx.deps.rag_service.format_sources(rag_result.contexts)

        return {
            "found": True,
            "context": rag_result.context_text,
            "sources": sources,
            "chunk_count": rag_result.total_chunks,
        }

    @agent.tool
    async def list_available_policies(
        ctx: RunContext[PolicyAgentDeps],
    ) -> dict[str, Any]:
        """
        List all available policy documents.

        Returns a list of policy names, categories, and descriptions.
        """
        repo = PolicyRepository(ctx.deps.session, ctx.deps.tenant_id)
        policies = await repo.get_active_policies()

        policy_list = []
        for policy in policies:
            policy_list.append(
                {
                    "name": policy.name,
                    "category": policy.category,
                    "description": policy.description or "No description",
                    "version": policy.version,
                    "is_indexed": policy.is_indexed,
                }
            )

        return {
            "policies": policy_list,
            "total": len(policy_list),
        }

    @agent.tool
    async def get_policy_by_category(
        ctx: RunContext[PolicyAgentDeps],
        category: str,
    ) -> dict[str, Any]:
        """
        Get policies in a specific category.

        Args:
            category: Policy category (e.g., 'leave', 'attendance', 'benefits', 'conduct')

        Returns:
            List of policies in the specified category
        """
        repo = PolicyRepository(ctx.deps.session, ctx.deps.tenant_id)
        policies = await repo.get_by_category(category)

        policy_list = []
        for policy in policies:
            policy_list.append(
                {
                    "name": policy.name,
                    "description": policy.description or "No description",
                    "version": policy.version,
                }
            )

        return {
            "category": category,
            "policies": policy_list,
            "total": len(policy_list),
        }


async def answer_policy_question(
    question: str,
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
) -> PolicyAgentResponse:
    """
    Answer a policy-related question using RAG.

    Args:
        question: The user's question about policies
        session: Database session
        tenant_id: The tenant ID
        user_id: The user asking the question

    Returns:
        PolicyAgentResponse with answer, sources, and follow-up questions
    """
    rag_service = PolicyRAGService(
        tenant_id=tenant_id,
        config=RAGConfig(
            max_chunks=5,
            relevance_threshold=1.5,
            include_sources=True,
        ),
    )

    deps = PolicyAgentDeps(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        rag_service=rag_service,
    )

    agent = get_policy_agent()

    try:
        result = await agent.run(question, deps=deps)
        return result.output
    except Exception as e:
        logger.error("Policy agent error: %s", e, exc_info=True)
        return PolicyAgentResponse(
            answer="I apologize, but I encountered an error while processing your question. Please try again or contact HR for assistance.",
            sources=[],
            confidence="low",
            follow_up_questions=[],
        )
