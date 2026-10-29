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

FIELDS = ["exercise", "sets", "reps", "weight", "unit", "rpe"]

def normalize_name(name):
    return name.lower().replace("-", " ").strip()

def similarity(label, pred):
    score = 0
    for field in FIELDS:
        if label[field] is None:
            continue
        elif field == "exercise":
            normalized_label = normalize_name(label[field])
            normalized_pred = normalize_name(pred[field])
            if normalized_label==normalized_pred:
                score += 1
        else:
            if label[field] == pred[field]:
                score += 1
    return score

def match_records(labels, preds):
    used = set()
    pairs = []
    missing = []
    for label in labels:
        best_i = None
        best_score = 0
        for i, pred in enumerate(preds):
            if i in used:
                continue
            similarity_score = similarity(label,pred)
            if similarity_score > best_score:
                best_i = i
                best_score = similarity_score
        if best_i is not None:
            pairs.append((label,preds[best_i]))
            used.add(best_i)
        else:
            missing.append(label)
    extra = [pred for i, pred in enumerate(preds) if i not in used]
    return pairs, missing, extra

def field_correct(label, pred, field):
    if field == "exercise":
        normalized_label = normalize_name(label[field])
        normalized_pred = normalize_name(pred[field])
        return normalized_pred == normalized_label
    else:
        return label[field] == pred[field]

if __name__ == "__main__":
    cases = load_labels()
    total_labels = 0   
    total_extra = 0     
    all_pairs = []     

    for case_id, case in cases.items():
        try:
            preds = run_model(case["input"])
        except Exception as e:
            print(case_id, "HATA:", e)
            preds = []
        pairs,missing,extra = match_records(case["records"],preds)
        total_labels += len(case["records"])
        all_pairs.extend(pairs)
        total_extra += len(extra)
        time.sleep(6)
    total_preds = len(all_pairs) + total_extra
    print(f"Recall: {len(all_pairs)}/{total_labels}")
    print(f"Precision: {len(all_pairs)}/{total_preds}")
    for field in FIELDS:
        correct = 0
        for label,pred in all_pairs:
            if field_correct(label,pred,field):
                correct += 1
        print(f"{field}: {correct}/{len(all_pairs)}")
