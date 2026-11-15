"""Evaluate the real configured embedding model against fictional seed sources."""
import argparse
import asyncio
import json
from pathlib import Path
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.rag.embeddings import build_provider
from app.schemas.context import ContextRequest
from app.services.context import search_context


async def evaluate(path: Path):
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    config = get_settings()
    engine = create_async_engine(config.database_url)
    results = []
    try:
        async with httpx.AsyncClient(timeout=config.embedding_timeout) as client:
            provider = build_provider(config, client)
            for case in cases:
                async with async_sessionmaker(engine)() as session:
                    result = await search_context(session, UUID(case["student_id"]), ContextRequest(
                        query=case["query"], recent_lessons_limit=0, semantic_limit=5,
                    ), provider)
                expected = set(case["expected_lesson_ids"])
                found = [str(source["lesson_id"]) for source in result["sources"]]
                relevant = expected & set(found)
                results.append({
                    "query": case["query"], "found_lesson_ids": found,
                    "recall_at_5": len(relevant) / len(expected),
                    "precision_at_5": len(relevant) / len(found) if found else 0,
                    "warnings": result["warnings"], "semantic_status": result["semantic_status"],
                })
    finally:
        await engine.dispose()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path("data/retrieval_eval.json"))
    args = parser.parse_args()
    results = asyncio.run(evaluate(args.path))
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if any(result["semantic_status"] != "ready" or result["warnings"] for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
