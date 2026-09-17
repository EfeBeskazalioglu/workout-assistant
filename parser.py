import os
from dotenv import load_dotenv
import json
import time
from enum import Enum
from functools import wraps
from pydantic import BaseModel,Field, ValidationError
from typing import Optional
from openai import OpenAI
from datetime import date
import instructor
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
model = "nvidia/nemotron-3.5-lightning:free"

SYSTEM_PROMPT = """You are a parser that converts exercise sentences into structured workout data."""
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
    exercise: str = Field(description="lowercase letters,standard name")
    sets: Optional[int] = Field(default=None,description="If none then do not assume")
    reps: Optional[int] = None
    weight: Optional[float] = None
    unit: Optional[Unit] = None
    rpe: Optional[int] = None
#Modele verilen
class WorkoutLog(BaseModel):
    exercises: list[Exercise]
#Modelden beklenilen, model workoutrecordu görmez bundan kaynaklı şemaya uydurmak için saçma veri üretmesinden kaçınılıyor
class WorkoutRecord(BaseModel):
    exercises: list[Exercise] = Field(min_length=1)
    workout_date: date = Field(default_factory=date.today)

class WorkoutParser:
    def __init__(self,api_key,model):
        self.api_key = api_key
        self.model = model
        self.client = instructor.from_openai(OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    ))
    @timer   
    def parse(self,text):
        log = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            response_model=WorkoutLog,
            temperature=0
        )
        record = WorkoutRecord(exercises=log.exercises)
        return record



test_cases = [
    "chest day felt strong"
]

workoutparser = WorkoutParser(api_key,model)
for case in test_cases:
    try:
        log = workoutparser.parse(case)
        print(log)
        for exercise in log.exercises:
            print(exercise)
    except ValidationError as e:
        print(f"PARSE FAILED: {case}")
        print(e)