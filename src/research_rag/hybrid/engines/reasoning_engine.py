from __future__ import annotations

import json
import re

from research_rag.hybrid.domain import AnswerClaim, QueryPlan, RetrievalCandidate


class ReasoningEngine:
    def __init__(self, llm_client=None) -> None:
        self.llm_client = llm_client
        self.last_llm_error: str | None = None

    def classify_query(self, question: str) -> QueryPlan:
        text = question.lower()
        multi_hop_signals = [
            "compare",
            "difference",
            "tradeoff",
            "across",
            "between",
            "versus",
            "vs",
            "and then",
        ]
        if any(signal in text for signal in multi_hop_signals) or len(re.findall(r"\b(and|then)\b", text)) >= 2:
            hops = self.decompose_multi_hop(question)
            return QueryPlan(query_type="multi_hop", hops=hops)
        return QueryPlan(query_type="simple", hops=[question])

    def decompose_multi_hop(self, question: str) -> list[str]:
        if self.llm_client:
            try:
                response = self.llm_client.complete_json(
                    instructions=(
                        "Decompose the user question into concise sequential reasoning hops. "
                        "Return strict JSON: {\"hops\": [\"...\"]}."
                    ),
                    prompt=question,
                )
                hops = response.get("hops", [])
                if isinstance(hops, list):
                    cleaned = [str(h).strip() for h in hops if str(h).strip()]
                    if cleaned:
                        return cleaned
            except Exception:
                pass

        parts = re.split(r"\b(?:and|then|vs|versus|compare)\b", question, flags=re.IGNORECASE)
        hops = [part.strip(" ,.?") for part in parts if part.strip(" ,.?")]
        return hops or [question]

    def generate_answer(self, question: str, plan: QueryPlan, contexts: list[RetrievalCandidate]) -> tuple[str, list[AnswerClaim]]:
        self.last_llm_error = None
        context_blocks = []
        for idx, candidate in enumerate(contexts, start=1):
            context_blocks.append(
                {
                    "context_id": idx,
                    "chunk_id": candidate.chunk.chunk_id,
                    "paper_id": candidate.chunk.paper_id,
                    "page_number": candidate.chunk.page_number,
                    "section": candidate.chunk.section,
                    "text": candidate.chunk.text,
                }
            )

        if self.llm_client:
            try:
                payload = self.llm_client.complete_json(
                    instructions=(
                        "Answer only from provided context. Be concise and coherent. "
                        "Do not copy noisy fragments or leading symbols (such as +, -, bullets). "
                        "If user asks what a document is about, produce a high-level overview in 2-4 complete sentences. "
                        "Return strict JSON with keys: answer (string) and claims "
                        "(array of {claim: string, context_ids: number[]})."
                    ),
                    prompt=json.dumps(
                        {
                            "question": question,
                            "query_type": plan.query_type,
                            "hops": plan.hops,
                            "contexts": context_blocks,
                        },
                        ensure_ascii=False,
                    ),
                )
                answer = str(payload.get("answer", "")).strip()
                claims_raw = payload.get("claims", [])
                claims: list[AnswerClaim] = []
                if isinstance(claims_raw, list):
                    for item in claims_raw:
                        if not isinstance(item, dict):
                            continue
                        claim = self._clean_claim_text(str(item.get("claim", "")))
                        context_ids = item.get("context_ids", [])
                        citations = self._citations_for_ids(context_blocks, context_ids)
                        if claim:
                            claims.append(AnswerClaim(claim=claim, citations=citations))
                answer = self._clean_claim_text(answer)
                if answer:
                    if not claims:
                        for fallback in self._claims_from_answer(answer):
                            citations = self._citations_for_ids(context_blocks, [1, 2, 3])
                            claims.append(AnswerClaim(claim=fallback, citations=citations))
                    return answer, claims
            except Exception as exc:
                self.last_llm_error = str(exc)
                pass

        fallback_answer, fallback_claims = self._extractive_fallback(question, contexts)
        if self.last_llm_error:
            fallback_answer = (
                "LLM generation is temporarily unavailable (provider error or quota limit). "
                "Showing evidence snippets from retrieved context. "
                f"Details: {self.last_llm_error.splitlines()[0]}\n\n"
                f"{fallback_answer}"
            )
        return fallback_answer, fallback_claims

    def _extractive_fallback(self, question: str, contexts: list[RetrievalCandidate]) -> tuple[str, list[AnswerClaim]]:
        if not contexts:
            return "I do not have enough evidence in the indexed papers to answer this question.", []

        if self._is_overview_question(question):
            return self._overview_fallback(question, contexts)

        selected = contexts[:3]
        claims: list[AnswerClaim] = []
        answer_parts: list[str] = []

        for candidate in selected:
            sentence = self._best_sentence(candidate.chunk.text)
            if not sentence:
                continue
            citations = [
                {
                    "paper_id": candidate.chunk.paper_id,
                    "chunk_id": candidate.chunk.chunk_id,
                    "page_number": candidate.chunk.page_number,
                    "section": candidate.chunk.section,
                }
            ]
            claims.append(AnswerClaim(claim=sentence, citations=citations))
            answer_parts.append(sentence)

        if not answer_parts:
            answer_parts = ["I found context, but could not extract clean evidence sentences."]

        answer = self._clean_claim_text(" ".join(answer_parts))
        return answer, claims

    def _overview_fallback(self, question: str, contexts: list[RetrievalCandidate]) -> tuple[str, list[AnswerClaim]]:
        selected = contexts[:8]
        text_blob = " ".join(item.chunk.text for item in selected)
        cleaned_blob = self._clean_claim_text(text_blob)

        is_resume = self._looks_like_resume(cleaned_blob)
        tech_stack = self._extract_tech_terms(cleaned_blob)
        project_signals = self._extract_project_phrases(cleaned_blob)

        if is_resume:
            answer_parts = [
                "This document appears to be a professional CV/resume focused on AI and machine learning work.",
            ]
            if project_signals:
                answer_parts.append(
                    "It highlights projects such as " + ", ".join(project_signals[:3]) + "."
                )
            if tech_stack:
                answer_parts.append(
                    "The profile emphasizes hands-on experience with " + ", ".join(tech_stack[:6]) + "."
                )
        else:
            evidence_sentences = self._best_overview_sentences(cleaned_blob)
            answer_parts = [
                "This document discusses its core topic through methods, results, and practical implementation details.",
            ]
            if evidence_sentences:
                answer_parts.append("Key points include: " + " ".join(evidence_sentences[:2]))
            if tech_stack:
                answer_parts.append("Important technical terms include " + ", ".join(tech_stack[:5]) + ".")

        answer = self._clean_claim_text(" ".join(answer_parts))

        claims: list[AnswerClaim] = []
        for item in selected[:3]:
            claim_text = self._best_sentence(item.chunk.text)
            if not claim_text:
                continue
            claims.append(
                AnswerClaim(
                    claim=claim_text,
                    citations=[
                        {
                            "paper_id": item.chunk.paper_id,
                            "chunk_id": item.chunk.chunk_id,
                            "page_number": item.chunk.page_number,
                            "section": item.chunk.section,
                        }
                    ],
                )
            )
        return answer, claims

    @staticmethod
    def _best_sentence(text: str) -> str:
        sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]
        if not sentences:
            cleaned = text.strip()
            cleaned = re.sub(r"\s+", " ", cleaned)
            cleaned = re.sub(r"^[^A-Za-z0-9]+", "", cleaned)
            return cleaned[:240]

        for sentence in sentences:
            alpha_count = len(re.findall(r"[A-Za-z]", sentence))
            if alpha_count >= 20:
                return ReasoningEngine._clean_claim_text(sentence[:240])
        return ReasoningEngine._clean_claim_text(sentences[0][:240])

    @staticmethod
    def _clean_claim_text(text: str) -> str:
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        cleaned = re.sub(r"^[^A-Za-z0-9]+", "", cleaned)
        cleaned = cleaned.replace("●", "").replace("•", "")
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -\t")
        return cleaned

    @staticmethod
    def _claims_from_answer(answer: str) -> list[str]:
        sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", answer) if segment.strip()]
        claims = [ReasoningEngine._clean_claim_text(sentence) for sentence in sentences]
        return [claim for claim in claims if len(claim) >= 20][:3]

    @staticmethod
    def _is_overview_question(question: str) -> bool:
        q = question.lower()
        patterns = ["what is this", "what this", "all about", "summary", "summarize", "overview"]
        return any(pattern in q for pattern in patterns)

    @staticmethod
    def _looks_like_resume(text: str) -> bool:
        q = text.lower()
        markers = ["cv", "resume", "experience", "skills", "projects", "education", "intern"]
        score = sum(1 for marker in markers if marker in q)
        return score >= 3

    @staticmethod
    def _extract_tech_terms(text: str) -> list[str]:
        vocab = [
            "python",
            "pytorch",
            "tensorflow",
            "langchain",
            "rag",
            "cnn",
            "transformer",
            "whisper",
            "hugging face",
            "faiss",
            "fastapi",
            "react",
            "docker",
        ]
        lower = text.lower()
        return [term.title() for term in vocab if term in lower]

    @staticmethod
    def _extract_project_phrases(text: str) -> list[str]:
        candidates = re.findall(r"([A-Z][A-Za-z0-9\-+& ]{6,60})", text)
        phrases: list[str] = []
        for candidate in candidates:
            cleaned = re.sub(r"\s+", " ", candidate).strip(" -")
            if len(cleaned.split()) < 2:
                continue
            if cleaned.lower() in {item.lower() for item in phrases}:
                continue
            phrases.append(cleaned)
            if len(phrases) >= 5:
                break
        return phrases

    @staticmethod
    def _best_overview_sentences(text: str) -> list[str]:
        sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]
        scored: list[tuple[int, str]] = []
        keywords = {"propose", "develop", "build", "evaluate", "result", "improve", "system"}
        for sentence in sentences:
            lower = sentence.lower()
            score = sum(1 for key in keywords if key in lower)
            if len(sentence) > 25:
                score += 1
            scored.append((score, sentence))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [ReasoningEngine._clean_claim_text(item[1]) for item in scored[:3] if item[0] > 0]

    @staticmethod
    def _citations_for_ids(context_blocks: list[dict[str, object]], context_ids: object) -> list[dict[str, object]]:
        citations: list[dict[str, object]] = []
        if not isinstance(context_ids, list):
            return citations
        id_set = {int(item) for item in context_ids if isinstance(item, int) or str(item).isdigit()}
        for block in context_blocks:
            if block["context_id"] in id_set:
                citations.append(
                    {
                        "paper_id": block["paper_id"],
                        "chunk_id": block["chunk_id"],
                        "page_number": block["page_number"],
                        "section": block["section"],
                    }
                )
        return citations
