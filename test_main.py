from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import main
from workout_parser import ExerciseLLM, WorkoutLLM
from instructor.core import InstructorRetryException

client = TestClient(main.app)


def test_parse_valid_input_returns_200(monkeypatch):
    fake_llm = MagicMock()
    fake_llm.chat.completions.create.return_value = WorkoutLLM(
        exercises=[ExerciseLLM(exercise_name="squat", sets=3, reps=8, weight=60, unit="kg")]
    )
    monkeypatch.setattr(main.parser, "client", fake_llm)

    response = client.post("/parse", json={"text": "3x8 squat 60kg"})

    assert response.status_code == 200
    assert response.json()["exercises"][0]["exercise_name"] == "squat"


def test_parse_empty_list_returns_422(monkeypatch):
    fake_llm = MagicMock()
    fake_llm.chat.completions.create.return_value = WorkoutLLM(exercises=[])
    monkeypatch.setattr(main.parser, "client", fake_llm)
    
    response = client.post("/parse", json={"text":"chest day felt strong"})
    
    assert response.status_code == 422

def test_parse_llm_failure_returns_503(monkeypatch):
    fake_llm = MagicMock()
    fake_llm.chat.completions.create.side_effect = InstructorRetryException("LLM Failed",n_attempts=1,total_usage=0)
    monkeypatch.setattr(main.parser, "client", fake_llm)
    
    response = client.post("/parse", json={"text":"3x8 squat"})

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "30"

def test_parse_missing_text_returns_422():
    response = client.post("/parse", json={})

    assert response.status_code == 422

def test_parse_empty_text_returns_422():
    response = client.post("/parse", json={"text":""})

    assert response.status_code == 422