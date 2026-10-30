# Eval sonuçları

Koşum: `python -m eval.run_eval` (repo kökünden). Set: `eval/dataset.csv` — 20 gerçek girdi, 33 etiket.

**Metrikler**
- **Recall** = eşleşen kayıt / toplam etiket — model kaç kaydı yakaladı (kaçırma, B4 burada).
- **Precision** = eşleşen kayıt / modelin ürettiği kayıt — kaçı gerçek (uydurma, bölünme burada).
- **Alan doğruluğu** = sadece eşleşen çiftlerde, alan bazında doğru / eşleşen. Etiket boş + model dolu = yanlış (uydurma, A10).
- Eşleştirme: her etikete en çok alanı tutan kullanılmamış model kaydı (`similarity` ≥ 1); adlar normalize (küçük harf, tire → boşluk).

**Karşılaştırma kuralı:** her ayar 3 koşum; bir değişiklik ancak alan değerleri baz çizgi aralığının dışına çıkarsa etkili sayılır. Recall oynuyorsa alan yüzdeleri karşılaştırılmaz (sadece hayatta kalan çiftler üzerinden — seçilim yanlılığı).

## Koşumlar

Model hepsinde `openai/gpt-oss-20b` (Groq, JSON_SCHEMA, temperature 0).

| # | Tarih | Kod | Prompt | Recall | Precision | exercise | sets | reps | weight | unit | rpe | Not |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 29 Eki | `a7d19c2` | v1 — tek cümle | 27/33 | 27/29 | 17/27 | 16/27 | 21/27 | 20/27 | 19/27 | 24/27 | id 18 `json_validate_failed` (B4) |
| 2 | 29 Eki | `a7d19c2` | v1 | 27/33 | 27/29 | 19/27 | 12/27 | 24/27 | 23/27 | 17/27 | 24/27 | id 18 düştü |
| 3 | 29 Eki | `a7d19c2` | v1 | 27/33 | 27/29 | 19/27 | 14/27 | 24/27 | 23/27 | 14/27 | 24/27 | id 18 düştü |
| **v1 aralık** | | | | **82%** | **93%** | **63–70%** | **44–59%** | **78–89%** | **74–85%** | **52–70%** | **89%** | baz çizgi |
| 4 | 29 Eki | `0bb2bf8` | v2 — `AxB` kuralları (A8) | 24/33 | 24/27 | 15/24 | 20/24 | 22/24 | 21/24 | 17/24 | 21/24 | id 4 düştü |
| 5 | 29 Eki | `0bb2bf8` | v2 | 22/33 | 22/22 | 13/22 | 18/22 | 22/22 | 20/22 | 21/22 | 19/22 | id 4, 16 düştü; id 30 **429** (sleep 6 sn yetmedi → 10 sn) — kirli koşum |
| 6 | 29 Eki | `0bb2bf8` + sleep 10 | v2 | 18/33 (55%) | 18/20 (90%) | 13/18 | 16/18 | 17/18 | 17/18 | 13/18 | 15/18 | id 4, 14, 16, 18 düştü |

## Gözlemler

- **Gürültü (v1):** Kod/model/prompt aynıyken alan skorları koşumdan koşuma 2-4 oynuyor (`sets` 16 → 12, `reps` 21 → 24). Recall/precision ve `rpe` sabit. Tek koşumluk farkla prompt karşılaştırması yapılamaz.
- `sets` düşerken `reps`/`weight` yükseliyor: model `AxB` gösterimini koşumdan koşuma farklı yorumluyor (A8).
- `rpe` 3 hatası = A9'daki 1, 2, 6 (`9.5 → 10`).
- id 18 v1'de üç koşumda da düştü (4 Eki dahil); id 16 4 Eki'de düşmüştü, 29 Eki v1'de geçti.
- **v2 (A8 prompt):** hayatta kalan çiftlerde `sets` ~50% → 82-89% (aralık dışı), `reps`/`weight` da yukarı. **Ama recall 82% → 55-73%**: `json_validate_failed` başka ve daha çok girdiye kaydı (4, 14, 16, 18). id 4 kısa girdi (`lateral raise 10x10 rpe 9`) → "B4 uzun girdide olur" yanlış, prompt'a bağlı. Düşen çağrılar 2.4-3.7 sn (başarılı <1 sn) → hipotez: reasoning modeli belirsiz girdide (`10x10` eşit sayılar, `90-95 10 8`) uzun düşünüyor ve geçerli JSON üretemiyor. Ondalık → `int` alan hipotezi elendi (4 ve 14'te ondalık yok).
- **Net etki v2: negatif** (recall kaybı alan kazancından büyük). Karar bekliyor: id 4 izole deneyi (v1 vs v2, 5'er koşum, süre + düşme sayısı).

## Tek girdi deneyi — 30 Eki (`python -m eval.probe`)

id 4 (`lateral raise 10x10 rpe 9`), her prompt 5 çağrı, aralarda 10 sn.

| Prompt | Düşen | Süre |
|---|---|---|
| v1 | 0/5 | 0.39–0.57 sn |
| v2 | 4/5 | düşenler 2.52–2.91 sn, başarılı 0.98 sn |

**Karar (30 Eki):** v2 geri alındı (`git revert 0bb2bf8`). `sets` kazancı gerçek ama best-effort structured output'ta `json_validate_failed`'ı tetikliyor. Kök neden ve sıradaki adım: `failures.md` B4 — strict mod, sonra v2 tekrar ölçülecek.
