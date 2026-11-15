"""Live smoke evaluation on fictional notes, never on the user's database.

Run: python -m app.evaluate_materials
Prints drafts for human assessment of subject accuracy and usefulness.
"""
import asyncio
import json

import httpx

from app.core.config import get_settings
from app.rag.llm import LLMError, build_llm
from app.schemas.materials import PlanContent, HomeworkContent, FeedbackContent
from app.services.materials import SYSTEM


async def main():
    settings = get_settings()
    async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
        provider = build_llm(settings, client)
        for scenario, schema, request in [
            ("plan", PlanContent, {"topic": "Квадратные уравнения", "duration_minutes": 60}),
            ("homework", HomeworkContent, {"instructions": "Практика знаков", "duration_minutes": 20, "include_answers": True}),
            ("feedback", FeedbackContent, {"recipient": "parent", "instructions": "Коротко"}),
        ]:
            payload = {"scenario": scenario, "request": request,
                       "profile": {"grade": "8 класс", "goals": "Квадратные уравнения"},
                       "sources": [{"number": 1, "text": "Тема: квадратные уравнения. Заметки: разобрали дискриминант, решили три примера. Трудности: ошибка знака при подстановке b=-3. Заданное ДЗ: пять уравнений. Выполнение не отмечено."}]}
            try:
                result = await provider.generate(SYSTEM, json.dumps(payload, ensure_ascii=False), schema)
            except LLMError as exc:
                print(f"{scenario}: {exc}")
                return 1
            if any(n != 1 for fact in result.facts for n in fact.source_numbers):
                print(f"{scenario}: invalid_sources")
                return 1
            print(json.dumps({"scenario": scenario, **result.model_dump()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
