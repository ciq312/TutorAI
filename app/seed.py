"""Validate and import demo JSON atomically, without overwriting existing records."""
import argparse
import asyncio
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.models import Contact, Lesson, Student
from app.schemas.data import ContactCreate, LessonCreate, StudentCreate


class SeedContact(ContactCreate):
    id: UUID


class SeedLesson(LessonCreate):
    id: UUID


class SeedStudent(StudentCreate):
    id: UUID
    contacts: list[SeedContact] = Field(default_factory=list)
    lessons: list[SeedLesson] = Field(default_factory=list)


class SeedData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    students: list[SeedStudent]


async def import_seed(path: Path, database_url: str | None = None) -> dict[str, int]:
    data = SeedData.model_validate_json(path.read_text(encoding="utf-8"))
    # Reject ambiguous duplicate IDs before opening a transaction.
    ids = {"students": [], "contacts": [], "lessons": []}
    for student in data.students:
        ids["students"].append(student.id)
        ids["contacts"].extend(contact.id for contact in student.contacts)
        ids["lessons"].extend(lesson.id for lesson in student.lessons)
    if any(len(values) != len(set(values)) for values in ids.values()):
        raise ValueError("Duplicate IDs in seed file")
    engine = create_async_engine(database_url or get_settings().database_url)
    counts = dict.fromkeys(ids, 0)
    try:
        async with async_sessionmaker(engine)() as session, session.begin():
            for student in data.students:
                if await session.get(Student, student.id) is None:
                    session.add(Student(**student.model_dump(exclude={"contacts", "lessons"})))
                    await session.flush()
                    counts["students"] += 1
                for model, entries, key in (
                    (Contact, student.contacts, "contacts"),
                    (Lesson, student.lessons, "lessons"),
                ):
                    for entry in entries:
                        existing = await session.get(model, entry.id)
                        if existing is None:
                            session.add(model(**entry.model_dump(), student_id=student.id))
                            counts[key] += 1
                        elif existing.student_id != student.id:
                            raise ValueError(f"{key} ID belongs to another student")
    finally:
        await engine.dispose()
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path("data/seed.json"))
    args = parser.parse_args()
    print(asyncio.run(import_seed(args.path)))


if __name__ == "__main__":
    main()
