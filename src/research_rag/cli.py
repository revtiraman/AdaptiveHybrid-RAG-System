from __future__ import annotations

import argparse
import json

from research_rag.bootstrap import build_container


def main() -> None:
    parser = argparse.ArgumentParser(description="Adaptive Hybrid RAG CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a PDF into hybrid stores")
    ingest_parser.add_argument("--pdf", required=True, help="Path to the source PDF")
    ingest_parser.add_argument("--title", help="Optional paper title")
    ingest_parser.add_argument("--paper-id", help="Optional stable paper identifier")

    query_parser = subparsers.add_parser("query", help="Run Adaptive Hybrid RAG query")
    query_parser.add_argument("--question", required=True, help="Question to ask against the indexed PDFs")
    query_parser.add_argument("--paper-id", action="append", dest="paper_ids", help="Restrict to paper id")
    query_parser.add_argument("--section", help="Optional section filter")

    subparsers.add_parser("list-papers", help="Show indexed papers")
    subparsers.add_parser("stats", help="Show system statistics")

    serve_parser = subparsers.add_parser("serve", help="Start the HTTP API")
    serve_parser.add_argument("--host", help="Override host binding")
    serve_parser.add_argument("--port", type=int, help="Override port")

    arxiv_parser = subparsers.add_parser("arxiv-sync", help="Fetch and ingest recent relevant papers from ArXiv")
    arxiv_parser.add_argument("--query", help="ArXiv search query (defaults from env)")
    arxiv_parser.add_argument("--max-results", type=int, help="Max results to fetch")
    arxiv_parser.add_argument("--days-back", type=int, help="Only include papers updated in last N days")
    arxiv_parser.add_argument("--category", action="append", dest="categories", help="Allowed arXiv category (repeatable)")
    arxiv_parser.add_argument("--term", action="append", dest="relevance_terms", help="Relevance term filter (repeatable)")
    arxiv_parser.add_argument("--dry-run", action="store_true", help="Show matches without downloading/ingesting")

    eval_parser = subparsers.add_parser("evaluate", help="Run evaluation harness on a QA dataset (JSON or JSONL)")
    eval_parser.add_argument("--dataset", required=True, help="Path to eval dataset with question/expected_keywords")
    eval_parser.add_argument("--limit", type=int, help="Optional max number of cases to evaluate")

    args = parser.parse_args()
    container = build_container()

    if args.command == "ingest":
        summary = container.system.ingest_pdf(args.pdf, title=args.title, paper_id=args.paper_id)
        print(json.dumps(summary, indent=2))
        return

    if args.command == "query":
        filters = {"section": args.section} if args.section else None
        result = container.system.query(
            question=args.question,
            paper_ids=args.paper_ids,
            filters=filters,
        )
        print(json.dumps(result.to_dict(), indent=2))
        return

    if args.command == "list-papers":
        print(json.dumps({"papers": container.system.list_papers()}, indent=2))
        return

    if args.command == "stats":
        stats = container.system.stats()
        print(
            json.dumps(
                {
                    "papers": stats.papers,
                    "chunks": stats.chunks,
                    "embedding_provider": stats.embedding_provider,
                    "reranker_provider": stats.reranker_provider,
                },
                indent=2,
            )
        )
        return

    if args.command == "serve":
        try:
            import uvicorn
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Starting the API requires uvicorn. Install dependencies with `pip install -e .` first."
            ) from exc

        uvicorn.run(
            "research_rag.api.app:create_app",
            factory=True,
            host=args.host or container.settings.host,
            port=args.port or container.settings.port,
            reload=not container.settings.is_production,
        )
        return

    if args.command == "arxiv-sync":
        summary = container.system.arxiv_sync(
            query=args.query or container.settings.arxiv_default_query,
            max_results=args.max_results or container.settings.arxiv_max_results,
            days_back=args.days_back or container.settings.arxiv_days_back,
            categories=args.categories or container.settings.arxiv_categories,
            relevance_terms=args.relevance_terms or container.settings.arxiv_relevance_terms,
            dry_run=bool(args.dry_run),
        )
        print(json.dumps(summary, indent=2))
        return

    if args.command == "evaluate":
        summary = container.system.evaluate(dataset_path=args.dataset, limit=args.limit)
        print(json.dumps(summary, indent=2))
        return


if __name__ == "__main__":
    main()
