from datetime import date
from sqlalchemy.orm import selectinload
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,ValidationError
from workout_parser import WorkoutParser
from database import SessionLocal, WorkoutDB, ExerciseDB
from instructor.core import InstructorRetryException
from config import settings
app = FastAPI()

class ParseRequest(BaseModel):
    text: str

class ExerciseOut(BaseModel):
    exercise: str
    sets: int | None
    reps: int | None
    weight: float | None
    unit: str | None
    rpe: int | None
    model_config = {"from_attributes": True}

class WorkoutOut(BaseModel):
    id: int
    workout_date: date
    exercises: list[ExerciseOut]

    model_config = {"from_attributes": True}

parser = WorkoutParser(api_key=settings.llm_api_key.get_secret_value(),model=settings.llm_model,timeout=settings.timeout,base_url=settings.llm_base_url)

def parse_or_error(text):
    try:
        return parser.parse(text)
    except ValidationError:
        raise HTTPException(status_code=422,detail="Be more specific about your workout!")
    except InstructorRetryException:
        raise HTTPException(status_code=503,headers={"Retry-After":"30"},detail="Try again some time later.")
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/parse")
def parse_workout(request: ParseRequest):
    return parse_or_error(text=request.text)

@app.post("/workouts",response_model=WorkoutOut)
def create_workout(request: ParseRequest):
    record = parse_or_error(text=request.text)

    workout = WorkoutDB(workout_date=record.workout_date)

    for e in record.exercises:
        exercise = ExerciseDB(exercise=e.exercise_name,sets=e.sets,reps=e.reps,weight=e.weight,unit=e.unit,rpe=e.rpe)
        workout.exercises.append(exercise)

    with SessionLocal() as session:
        session.add(workout)
        session.commit()
        session.refresh(workout)
        return WorkoutOut.model_validate(workout)

@app.get("/workouts",response_model=list[WorkoutOut])
def list_workouts():
    with SessionLocal() as session:
        workouts = session.query(WorkoutDB).options(selectinload(WorkoutDB.exercises)).all()
        return workouts

