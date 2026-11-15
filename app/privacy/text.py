"""Shared processing for name-resolved and explicitly ID-linked mentions."""
import re

from app.privacy.people import ExactNameResolver, PersonIdentity, PersonMention, PersonResolver


def redact(text: str, mentions: list[PersonMention]) -> str:
    """Consume resolved mentions only; never match names or access the database."""
    ordered = sorted(mentions, key=lambda mention: mention.start)
    end = 0
    parts = []
    for mention in ordered:
        if not (end <= mention.start < mention.end <= len(text)) or not mention.candidates:
            raise ValueError("Invalid or overlapping person mention")
        parts.extend((text[end:mention.start], "[имя]"))
        end = mention.end
    parts.append(text[end:])
    result = "".join(parts)
    result = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[email]", result)
    return re.sub(r"(?<!\w)\+?\d[\d ()-]{6,}\d(?!\w)", "[телефон]", result)


class TextAnonymizer:
    def __init__(self, people: tuple[PersonIdentity, ...], resolver: PersonResolver | None = None):
        self.people = people
        self.resolver = resolver if resolver is not None else ExactNameResolver()
        self.allowed_refs = {person.ref for person in people}

    def prepare(self, text: str, mentions: list[PersonMention] | None = None) -> str:
        # Explicit ID-linked mentions skip name resolution. An empty list is an
        # intentional structured input with no mentions, unlike None/free text.
        resolved = self.resolver.resolve(text, self.people) if mentions is None else mentions
        if any(ref not in self.allowed_refs for mention in resolved for ref in mention.candidates):
            raise ValueError("Person reference is outside the selected student's scope")
        return redact(text, resolved)
