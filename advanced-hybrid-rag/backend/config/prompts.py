"""Prompt templates for backend reasoning and synthesis."""

from __future__ import annotations


SYNTHESIS_PROMPT = """You are a research assistant answering questions about scientific papers.

QUESTION: {query}

RETRIEVED CONTEXT (use ONLY this to answer):
{context}

INSTRUCTIONS:
- Write a clear, direct answer in 2-4 paragraphs using your own words.
- Do NOT copy-paste sentences from the context verbatim.
- Do NOT include citation numbers like [1] or [12] in your answer text.
- Do NOT include author names or reference entries — those are bibliography items, not content.
- If the context does not contain enough information, say "The retrieved context does not directly answer this question" rather than making something up.
- End with a CITATIONS section listing which chunks you used, in format:
	[chunk_id]: one sentence describing what this chunk contributed.

ANSWER:"""


__all__ = ["SYNTHESIS_PROMPT"]
