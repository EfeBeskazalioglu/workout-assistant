import csv
from collections import defaultdict
import time
from config import settings
from workout_parser import WorkoutParser

parser = WorkoutParser(
    api_key=settings.llm_api_key.get_secret_value(),
    model=settings.llm_model,
    timeout=settings.timeout,
    base_url=settings.llm_base_url,
)

def run_model(text):
    record = parser.parse(text)
    return [
        {
            "exercise": ex.exercise_name,
            "sets": ex.sets,
            "reps": ex.reps,
            "weight": ex.weight,
            "unit": ex.unit.value if ex.unit else None,
            "rpe": ex.rpe,
        }
        for ex in record.exercises
    ]

def to_num(value, kind):
    return kind(value) if value else None

def load_labels(path="eval/dataset.csv"):
    cases = defaultdict(lambda: {"input": None, "records": []})
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            case = cases[row["id"]]
            case["input"] = row["input"]
            case["records"].append({
                "exercise": row["exercise"],
                "sets": to_num(row["sets"], int),
                "reps": to_num(row["reps"], int),
                "weight": to_num(row["weight"], float),
                "unit": row["unit"] or None,
                "rpe": to_num(row["rpe"], float),
            })
    return cases


if __name__ == "__main__":
    cases = load_labels()
    for case_id, case in cases.items():
        try:
            preds = run_model(case["input"])
        except Exception as e:
            print(case_id, "HATA:", e)
            preds = []
        print(case_id, case["input"])
        print("  etiket:", case["records"])
        print("  model :", preds)
        time.sleep(6)