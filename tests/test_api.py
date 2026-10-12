import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def parser_client(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-only")
    monkeypatch.setattr(main, "parse_lesson", lambda text: [
        {"order": 1, "text": text, "concepts": ["mass"], "prerequisites": []},
    ])
    with TestClient(main.app) as client:
        yield client


@pytest.mark.parametrize("embeddings", [[], [[]], [[1.0], [1.0]]])
def test_bad_embedding_shape_is_rejected(parser_client, monkeypatch, embeddings):
    monkeypatch.setattr(main, "embed_texts", lambda texts: embeddings)
    response = parser_client.post("/parse-lesson", json={"text": "Mass is matter."})
    assert response.status_code == 502


def test_parser_handoff_runs_through_simulation_without_a_provider(parser_client, monkeypatch):
    monkeypatch.setattr(main, "embed_texts", lambda texts: [[0.5, -0.5]])
    response = parser_client.post("/parse-lesson", json={"text": "Mass is matter.", "num_students": 7})
    assert response.status_code == 200
    handoff = response.json()
    assert len(handoff["students"]) == 7
    assert all(len(student["knowledge_vector"]) == 2 for student in handoff["students"])

    simulation_dir = Path(__file__).resolve().parents[1] / "person_b" / "socraticsem-main"
    monkeypatch.syspath_prepend(str(simulation_dir))
    monkeypatch.delenv("GROQ_API_KEY")
    spec = importlib.util.spec_from_file_location("lucida_simulation_api", simulation_dir / "main.py")
    simulation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(simulation)
    with TestClient(simulation.app) as client:
        empty = client.post("/simulate/chunks-only", json={})
        assert empty.status_code == 400
        output = client.post("/simulate/chunks-only", json=handoff)
        assert output.status_code == 200, output.text
        assert output.json()["results"]["summary"]["total_students_simulated"] == 7
        assert client.post("/simulate", json={"lesson_text": "Mass is matter.", "n_students": 0}).status_code == 422

    import analyzer
    fixes = analyzer.generate_fix_suggestions([{
        "chunk_index": 0, "chunk_text": "Mass is matter.", "key_concepts": ["mass"],
        "lost_pct": 80, "spike": 80, "avg_comprehension": 0.1,
    }])
    assert fixes[0]["suggestion_source"] == "template"
    assert fixes[0]["rewritten_chunk"] == "Mass is matter."
