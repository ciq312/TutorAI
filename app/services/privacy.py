"""Build a student-scoped identity directory; no contact data reaches providers."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Contact, Student
from app.privacy.people import PersonIdentity, PersonRef, PersonResolver
from app.privacy.text import TextAnonymizer


async def student_anonymizer(session: AsyncSession, student: Student,
                             resolver: PersonResolver | None = None) -> TextAnonymizer:
    contacts = await session.execute(select(Contact.id, Contact.name).where(Contact.student_id == student.id))
    people = (PersonIdentity(PersonRef("student", student.id), student.name), *(
        PersonIdentity(PersonRef("contact", contact_id), name) for contact_id, name in contacts
    ))
    return TextAnonymizer(people, resolver)
