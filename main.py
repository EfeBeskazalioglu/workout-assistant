from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,ValidationError
from workout_parser import WorkoutParser ,api_key,model

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