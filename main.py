from datetime import date
from sqlalchemy.orm import selectinload
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,ValidationError
from workout_parser import WorkoutParser ,api_key,model
from database import SessionLocal, WorkoutDB, ExerciseDB

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

parser = WorkoutParser(api_key=api_key,model=model)

def parse_or_422(text):
    try:
        return parser.parse(text)
    except ValidationError:
        raise HTTPException(status_code=422,detail="Be more specific about your workout!")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/parse")
def parse_workout(request: ParseRequest):
    return parse_or_422(text=request.text)

@app.post("/workouts",response_model=WorkoutOut)
def create_workout(request: ParseRequest):
    record = parse_or_422(text=request.text)

    workout = WorkoutDB(workout_date=record.workout_date)

    for e in record.exercises:
        exercise = ExerciseDB(exercise=e.exercise,sets=e.sets,reps=e.reps,weight=e.weight,unit=e.unit,rpe=e.rpe)
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

