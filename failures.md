# Kırılma kaydı

Model: `nvidia/nemotron-3.5-lightning:free` (OpenRouter)
Yöntem: çıplak API çağrısı — Instructor yok, response_format yok, prompt'ta JSON isteniyor, `json.loads()` ile parse ediliyor.

---

## A. Veri doğruluğu

### A1. Türkçe girdi → yanlış egzersiz
- **Girdi:** "bugün 4x8 mekik çektim"
- **Çıktı:** `exercise = "leg press"`
- **Sorun:** mekik = sit-up. Model bilmediğini null bırakmak yerine makul görünen yanlış bir egzersiz uydurdu. JSON geçerli, veri yanlış — sessiz hata.

### A2. Birim alanı serbest metin
- **Girdi:** "benched 135 lbs for 5 reps" → `unit: "lbs"`
- **Girdi:** "benched 120 pounds for 9 reps" → `unit: "pounds"`
- **Girdi:** "benched 120 pounds for 9 reps" (temp=1) → düşünce metninde `pounds`, JSON'da `lbs` — aynı çalıştırmada kendi içinde tutarsız
- **Sorun:** Unit serbestliği kullanıcıya bırakıldığında pounds/lbs/lb gibi varyantlar geliyor. Üç farklı string, üç örnekte.

### A3. Model kendi kendine kural uyduruyor
- **Girdi:** "benched 120 pounds for 9 reps" (temp=1)
- **Gözlem:** Düşünce metninde "no set count. I should default to null or maybe 1?" diyor, sonunda `sets: 1` yazıyor. Prompt null diyordu.
- **Sorun:** Hallucination'ın görünmeyen hâli — veri uydurma değil, kural uydurma.

---

## B. Format / parse

### B1. Prompt bir garanti değil, bir talep (temp=1)
- **Gözlem:** "Only return a json without any explanation" talimatına rağmen model düşünme sürecinin tamamını metin olarak bastı ("Here's a thinking process: ..."), JSON'u cümle içine gömdü.
- **Hata:** `JSONDecodeError: Expecting value: line 1 column 1`
- **Sonuç:** Prompt mühendisliği tek başına yeterli değil. Faz 2'de Instructor / structured output kullanmanın gerekçesi bu.

### B2. JSON sonrası fazladan içerik (temp=0)
- **Hata:** `JSONDecodeError: Extra data: line 1 column 122`
- **Gözlem:** 121 karaktere kadar geçerli JSON var, sonrasında fazladan içerik. `json.loads()` tek bir JSON değeri bekler, arkasında başka şey olmasını kabul etmez.

---

## C. Tasarım boşluğu

### C1. Tamamen boş kayıt
- **Girdi:** "chest day felt strong"
- **Çıktı:** tüm alanlar `None`
- **Sorun:** Model doğru davrandı (uydurmadı) ama şemada "geçersiz girdi" kavramı yok. Bu kaydın veritabanına yazılıp yazılmayacağı belirsiz.

---

## D. Kararlılık ve süre

### D1. temperature=0 deterministik değil
- **Gözlem:** Aynı cümle, aynı model. İki çağrı aynı çıktıyı verdi, üçüncüsü geçerli JSON bile değildi.
- **Not:** temp=0 token seçimini deterministik yapar ama uçtan uca tekrarlanabilirlik garanti etmez (batch'leme, farklı donanım, floating point sıralaması). "temp=0 koydum, artık sabit" yaygın bir yanılgı.

### D2. Yanıt süresi değişken
- **Ölçümler:** 7 / 20 / 32 / 93 / 145 saniye — aynı model, aynı cümle.
- **Sebep:** Ücretsiz katmanda kuyruk.
- **Sonuç:** Faz 2'de FastAPI endpoint'i yazarken timeout kararı bu veriye dayanacak.
