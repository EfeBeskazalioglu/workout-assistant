from datetime import date
from sqlalchemy.orm import selectinload
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,ValidationError
from workout_parser import WorkoutParser ,api_key,model
from database import SessionLocal, Workout, Exercise
app = FastAPI()

class ParseRequest(BaseModel):
    text: str

parser = WorkoutParser(api_key=api_key,model=model)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/parse")
def parse_workout(request: ParseRequest):
    try:
        return parser.parse(request.text)
    except ValidationError as e:
        raise HTTPException(status_code=422,detail="Be more specific about your workout!")

@app.post("/workouts")
def create_workout(request: ParseRequest):
    try:
        record = parser.parse(request.text)
    except ValidationError as e:
        raise HTTPException(status_code=422,detail="Be more specific about your workout!")

    workout = Workout(workout_date=record.workout_date)

    for e in record.exercises:
        exercise = Exercise(exercise=e.exercise,sets=e.sets,reps=e.reps,weight=e.weight,unit=e.unit,rpe=e.rpe)
        workout.exercises.append(exercise)

    with SessionLocal() as session:
        session.add(workout)
        session.commit()
    return record

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

@app.get("/workouts",response_model=list[WorkoutOut])
def list_workouts():
    with SessionLocal() as session:
        workouts = session.query(Workout).options(selectinload(Workout.exercises)).all()
        return workouts

