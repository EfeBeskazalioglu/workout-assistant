# Eval sonuçları

Koşum: `python -m eval.run_eval` (repo kökünden). Set: `eval/dataset.csv` — 20 gerçek girdi, 33 etiket.

**Metrikler**
- **Recall** = eşleşen kayıt / toplam etiket — model kaç kaydı yakaladı (kaçırma, B4 burada).
- **Precision** = eşleşen kayıt / modelin ürettiği kayıt — kaçı gerçek (uydurma, bölünme burada).
- **Alan doğruluğu** = sadece eşleşen çiftlerde, alan bazında doğru / eşleşen. Etiket boş + model dolu = yanlış (uydurma, A10).
- Eşleştirme: her etikete en çok alanı tutan kullanılmamış model kaydı (`similarity` ≥ 1); adlar normalize (küçük harf, tire → boşluk).

## Koşumlar

| # | Tarih | Kod | Model | Prompt | Recall | Precision | exercise | sets | reps | weight | unit | rpe | Not |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 29 Eki | skorlama commit'i | `openai/gpt-oss-20b` (Groq) | v1 — tek cümlelik `SYSTEM_PROMPT` | 27/33 | 27/29 | 17/27 | 16/27 | 21/27 | 20/27 | 19/27 | 24/27 | id 18 `json_validate_failed` (B4) |
| 2 | 29 Eki | aynı | aynı | aynı | 27/33 | 27/29 | 19/27 | 12/27 | 24/27 | 23/27 | 17/27 | 24/27 | id 18 yine düştü |

## Gözlemler

- **Gürültü:** Kod/model/prompt aynıyken alan skorları koşumdan koşuma 2-4 oynuyor (`sets` 16 → 12, `reps` 21 → 24). Recall/precision ve `rpe` sabit. Tek koşumluk farkla prompt karşılaştırması yapılamaz.
- `sets` düşerken `reps`/`weight` yükseliyor: model `AxB` gösterimini koşumdan koşuma farklı yorumluyor (A8).
- `rpe` 3 hatası = A9'daki 1, 2, 6 (`9.5 → 10`).
- id 18 üç koşumda da düştü (4 Eki + iki koşum); id 16 4 Eki'de düşmüştü, bugün geçti.
