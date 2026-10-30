import time
import workout_parser
from eval.run_eval import parser

TEXT = "lateral raise 10x10 rpe 9"
V1 = "You are a parser that converts exercise sentences into structured workout data."
V2 = workout_parser.SYSTEM_PROMPT   # şu anki prompt

for name, prompt in [("v1", V1), ("v2", V2)]:
    workout_parser.SYSTEM_PROMPT = prompt
    fails = 0
    for _ in range(5):
        condition = True
        start_time = time.time()
        try:
            parser.parse(TEXT)
        except Exception:
            fails += 1
            condition = False
        finally:
            end_time = time.time()
            t = end_time - start_time
            print(f"Took: {t:.2f}")
            if condition:
                print("Success")
            else:
                print("Fail")
        # 2. try: parser.parse(TEXT) — except: fails'i artır
        # 3. her çağrının süresini ve başarılı mı olduğunu yazdır
        time.sleep(10)
    # 4. bu prompt için "v1: 0/5 düştü" gibi özet yazdır
    print(f"Number of fails: {fails}")