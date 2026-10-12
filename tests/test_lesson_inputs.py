import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import lesson_parser
from models import ParseLessonRequest


@pytest.mark.parametrize("count", [-1, 0, 2001])
def test_student_count_matches_interface_bounds(count):
    with pytest.raises(ValidationError):
        ParseLessonRequest(text="A lesson", num_students=count)


def test_blank_lesson_is_rejected():
    with pytest.raises(ValidationError):
        ParseLessonRequest(text=" \n ")


@pytest.mark.parametrize("payload", [{"text": "wrong shape"}, [None], [{"text": 42}], [{"text": "A lesson", "concepts": "not a list"}]])
def test_invalid_provider_chunks_are_rejected(payload, monkeypatch):
    message = SimpleNamespace(content=json.dumps(payload))
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=message)])
    )))
    monkeypatch.setenv("GROQ_API_KEY", "test-only")
    monkeypatch.setattr(lesson_parser, "Groq", lambda **kwargs: client)
    with pytest.raises(ValueError):
        lesson_parser.parse_lesson("A lesson")


def test_fenced_provider_response_gets_defaults_and_sequential_order(monkeypatch):
    message = SimpleNamespace(content='```json\n[{"text":"Mass is matter.","order":99}]\n```')
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=message)])
    )))
    monkeypatch.setenv("GROQ_API_KEY", "test-only")
    monkeypatch.setattr(lesson_parser, "Groq", lambda **kwargs: client)
    assert lesson_parser.parse_lesson("Mass is matter.") == [
        {"text": "Mass is matter.", "order": 1, "concepts": [], "prerequisites": []}
    ]
