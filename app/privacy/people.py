"""Local person identity resolution, independent of storage and anonymization."""
from dataclasses import dataclass
import re
from typing import Literal, Protocol
from uuid import UUID


@dataclass(frozen=True)
class PersonRef:
    kind: Literal["student", "contact"]
    id: UUID


@dataclass(frozen=True)
class PersonIdentity:
    ref: PersonRef
    name: str


@dataclass(frozen=True)
class PersonMention:
    # Offsets refer to the original text (Python character offsets).
    start: int
    end: int
    # More than one candidate means ambiguity, never an arbitrary ID selection.
    candidates: tuple[PersonRef, ...]


class PersonResolver(Protocol):
    def resolve(self, text: str, people: tuple[PersonIdentity, ...]) -> list[PersonMention]: ...


class ExactNameResolver:
    """Initial implementation: known full names/parts; no inflection inference."""

    def resolve(self, text: str, people: tuple[PersonIdentity, ...]) -> list[PersonMention]:
        aliases: dict[str, list[PersonRef]] = {}
        for person in people:
            for name in [person.name, *person.name.split()]:
                if len(name) < 2:
                    continue
                refs = aliases.setdefault(name.lower(), [])
                if person.ref not in refs:
                    refs.append(person.ref)
        if not aliases:
            return []
        alternatives = "|".join(re.escape(name) for name in sorted(aliases, key=len, reverse=True))
        pattern = re.compile(r"(?<!\w)(?:" + alternatives + r")(?!\w)", re.I)
        return [PersonMention(match.start(), match.end(), tuple(aliases[match.group().lower()]))
                for match in pattern.finditer(text)]
