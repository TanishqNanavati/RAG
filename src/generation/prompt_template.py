"""
Modular prompt template definitions for grounded RAG answer generation.
Separates prompt construction and formatting logic entirely from API execution.
"""

import logging
from typing import List, Dict, Tuple, Any
from app.services.hybrid_retrieval.schemas import HybridRetrievedChunk

logger = logging.getLogger(__name__)


class PromptTemplate:
    """Encapsulates system and user prompt designs for grounded answer generation with citations."""

    SYSTEM_PROMPT = """You are a grounded RAG assistant.

Use ONLY the retrieved context to answer.

If the retrieved context is weak, incomplete, or unrelated to the query, do NOT attempt to answer from prior knowledge. Instead respond exactly:
"The information is not available in the provided documents."

Return concise, factual answers with citations.
Every factual statement must include an inline citation corresponding to the source chunk, formatted as [1], [2], etc.
Do not use any citation IDs that were not explicitly provided in the user prompt.
"""

    @staticmethod
    def build_context_mapping(chunks: List[Any]) -> Tuple[Dict[str, str], str]:
        """
        Assigns citation IDs ([1], [2], ...) to candidate chunks BEFORE sending to LLM.

        Args:
            chunks: List of retrieved/re-ranked chunk objects.

        Returns:
            Tuple of (citation_mapping_dict, formatted_context_string).
        """
        citation_mapping: Dict[str, str] = {}
        context_blocks: List[str] = []

        for idx, chunk in enumerate(chunks, 1):
            citation_id = f"[{idx}]"
            # Handle either Pydantic model or dict/dataclass
            text = getattr(chunk, "text", "") if hasattr(chunk, "text") else chunk.get("text", "")
            
            citation_mapping[citation_id] = text
            context_blocks.append(f"{citation_id}\n{text}\n")

        formatted_context = "\n".join(context_blocks)
        logger.debug(f"Built context mapping for {len(chunks)} chunks.")
        return citation_mapping, formatted_context

    @classmethod
    def create_prompts(cls, query: str, chunks: List[Any]) -> Tuple[str, str, Dict[str, str]]:
        """
        Generates the complete system prompt, user prompt, and citation mapping.

        Args:
            query: User search query.
            chunks: List of retrieved/re-ranked chunk objects.

        Returns:
            Tuple of (system_prompt, user_prompt, citation_mapping).
        """
        citation_mapping, formatted_context = cls.build_context_mapping(chunks)

        user_prompt = f"""USER QUERY:
{query}

PROVIDED CONTEXT CHUNKS:
{formatted_context}

Please provide your grounded answer with inline citations now."""

        logger.info(f"Created prompts for query: '{query}' (Context chunks: {len(chunks)})")
        return cls.SYSTEM_PROMPT, user_prompt, citation_mapping
