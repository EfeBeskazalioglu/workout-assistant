import os
from dotenv import load_dotenv
import json
import time
from enum import Enum
from functools import wraps
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
model = "nvidia/nemotron-3.5-lightning:free"

SYSTEM_PROMPT = """You are a parser which should convert exercise sentences like "I did 3x10 bench press 60kg"
to a json format.
Here is few example:
{ "exercises": [ { "exercise": "bench press", "sets": 3, "reps": 10, "weight": 60, "unit": "kg", "rpe": null } ] }
For input prompt: 3x10 60 pounds bench press
{ "exercises": [ { "exercise": "bench press", "sets": 3, "reps": 10, "weight": 60, "unit": "lb", "rpe": null } ] }
If there is a missing information in input then you must fill it with null value.
Unit must be kg or lb.
Do not convert units! Only standardize the unit.
Only return a json without any explanation and markdown."""
def timer(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        t1 = time.time()
        func_to_return = func(*args,**kwargs)
        t2 = time.time()
        print(t2-t1)
        return func_to_return
    return wrapper
class Unit(str, Enum):
    KG = "kg"
    LB = "lb"
class Exercise(BaseModel):
    exercise: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None
    unit: Optional[Unit] = None
    rpe: Optional[int] = None

class WorkoutLog(BaseModel):
    exercises: list[Exercise]

class WorkoutParser:
    def __init__(self,api_key,model):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    )
    @timer   
    def parse(self,text):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0
        )
        print(repr(response.choices[0].message.content))
        data = json.loads(response.choices[0].message.content)
        log = WorkoutLog.model_validate(data)
        return log

workoutparser = WorkoutParser(api_key,model)
for i in range(1):
    data = workoutparser.parse("benched 135 lbs for 5 reps")
    for exercise in data.exercises:
        print(exercise)