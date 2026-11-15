"""Prepare only educational fields for external embedding requests."""
from app.privacy.text import TextAnonymizer

from app.db.models import Lesson

# Bump when changing redaction or chunking; old indexes then require rebuilding.
TEXT_VERSION = "v2"


def lesson_text(lesson: Lesson, anonymizer: TextAnonymizer) -> str:
    fields = (("Тема", lesson.topic), ("Заметки", lesson.notes),
              ("Трудности", lesson.difficulties), ("Заданное ДЗ", lesson.homework))
    return anonymizer.prepare("\n".join(f"{label}: {value}" for label, value in fields if value))


def chunks(text: str, size: int = 1800, overlap: int = 200) -> list[str]:
    if not 0 <= overlap < size:
        raise ValueError("overlap must be smaller than size")
    result = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary != -1:
                end = boundary
        result.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return result
