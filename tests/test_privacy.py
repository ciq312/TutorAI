from uuid import UUID

import pytest

from app.privacy.people import ExactNameResolver, PersonIdentity, PersonMention, PersonRef
from app.privacy.text import TextAnonymizer

STUDENT = PersonRef("student", UUID(int=1))
CONTACT = PersonRef("contact", UUID(int=2))
PEOPLE = (PersonIdentity(STUDENT, "Анна Иванова"), PersonIdentity(CONTACT, "Мария"))


def test_free_text_resolves_db_identity_then_masks():
    text = "Анна Иванова и Мария. АННА ошиблась. Аннабель не меняем."
    mentions = ExactNameResolver().resolve(text, PEOPLE)
    assert mentions[0] == PersonMention(0, 12, (STUDENT,))
    assert mentions[1].candidates == (CONTACT,)
    assert TextAnonymizer(PEOPLE).prepare(text) == "[имя] и [имя]. [имя] ошиблась. Аннабель не меняем."


def test_id_linked_input_skips_resolver_and_uses_same_masking():
    class NeverResolve:
        def resolve(self, text, people):
            raise AssertionError("Explicit references must bypass name matching")

    text = "Помог Анне."
    mention = PersonMention(6, 10, (STUDENT,))
    assert TextAnonymizer(PEOPLE, NeverResolve()).prepare(text, [mention]) == "Помог [имя]."


def test_resolver_can_be_replaced_without_changing_masking():
    class InflectionResolver:
        def resolve(self, text, people):
            return [PersonMention(6, 10, (people[0].ref,))]

    assert TextAnonymizer(PEOPLE, InflectionResolver()).prepare("Помог Анне.") == "Помог [имя]."


def test_duplicate_names_remain_ambiguous_but_are_masked():
    people = (PersonIdentity(STUDENT, "Анна"), PersonIdentity(CONTACT, "Анна"))
    mentions = ExactNameResolver().resolve("Анна", people)
    assert mentions[0].candidates == (STUDENT, CONTACT)
    assert TextAnonymizer(people).prepare("Анна") == "[имя]"


@pytest.mark.parametrize("mention", [PersonMention(0, 4, (PersonRef("student", UUID(int=99)),)),
                                    PersonMention(-1, 4, (STUDENT,)),
                                    PersonMention(0, 99, (STUDENT,)), PersonMention(0, 4, ())])
def test_invalid_or_out_of_scope_mentions_rejected(mention):
    with pytest.raises(ValueError):
        TextAnonymizer(PEOPLE).prepare("Анна", [mention])


def test_overlapping_mentions_rejected():
    with pytest.raises(ValueError):
        TextAnonymizer(PEOPLE).prepare("Анна Иванова", [PersonMention(0, 12, (STUDENT,)),
                                                       PersonMention(0, 4, (STUDENT,))])


def test_structured_input_without_mentions_and_other_pii():
    assert TextAnonymizer(PEOPLE).prepare("anna@example.com +375291234567", []) == "[email] [телефон]"
