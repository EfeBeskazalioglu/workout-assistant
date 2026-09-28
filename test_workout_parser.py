import pytest
from pydantic import ValidationError
from workout_parser import WorkoutRecord,ExerciseLLM
from datetime import date

def test_record_rejects_empty_exercises():
    with pytest.raises(ValidationError):
        WorkoutRecord(exercises=[])

def test_record_adds_today_as_date():
    record = WorkoutRecord(exercises=[ExerciseLLM(exercise_name="bench press")])
    assert record.workout_date == date.today()
