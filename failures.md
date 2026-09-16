# Kırılma kaydı

Model: `nvidia/nemotron-3.5-lightning:free` (OpenRouter)
Başlangıç yöntemi (15 Eyl): çıplak API çağrısı — Instructor yok, prompt'ta JSON isteniyor, `json.loads()` ile parse ediliyor.
Güncel yöntem (16 Eyl): Pydantic modeli + Instructor `response_model`. Prompt tek cümleye indi, şema tek kaynakta.

| # | Bulgu | Durum |
|---|---|---|
| A1 | Türkçe egzersiz adı → uydurma | **açık** |
| A2 | Birim alanı serbest metin | kapandı 16 Eyl |
| A3 | Model kendi kendine kural uyduruyor | kapandı 16 Eyl |
| A4 | Egzersiz adı normalize edilmiyor | kapandı 16 Eyl |
| B1 | Model format talimatını terk ediyor | kapandı 16 Eyl |
| B2 | JSON sonrası fazladan içerik | kapandı 16 Eyl |
| C1 | Tamamen boş kayıt üretiliyor | kapandı 16 Eyl |
| D1 | temperature=0 deterministik değil | kapanmaz (LLM'in doğası) |
| D2 | Yanıt süresi değişken | kapanmaz (altyapı) |

---

## A. Veri doğruluğu

### A1. Türkçe girdi → yanlış egzersiz — AÇIK
- **Girdi:** "bugün 4x8 mekik çektim"
- **Çıktı (15 Eyl):** `exercise = "leg press"` · **Çıktı (16 Eyl, Instructor'lı):** `exercise = "leg curl"`
- **Sorun:** mekik = sit-up. Model her seferinde farklı ama hep yanlış bir egzersiz uyduruyor. JSON geçerli, veri yanlış — sessiz hata.
- **Neden kapanmadı:** Bu bir bilgi eksikliği, yapı sorunu değil. Şema, `Field(description=...)` ve Instructor yapıyı zorluyor, içeriği değil.
- **Çözüm yönü (Faz 3):** bilinen egzersiz listesi + RAG, ya da çıktıyı o listeye eşleme. RAG'ın gerekçesi bu somut bulgu.

### A2. Birim alanı serbest metin — KAPANDI
- **Girdiler:** "135 lbs" → `"lbs"` · "120 pounds" → `"pounds"` · aynı çalıştırmada düşünce metninde `pounds`, JSON'da `lbs`
- **Sorun:** Üç örnekte üç farklı string. Üzerine yazılacak her kg-çevirim kodu bir gün sessizce çalışmayacaktı.
- **Kapanış:** `class Unit(str, Enum)` — izinli değerler `kg` / `lb`. Dışındaki her şey doğrulamada duruyor.
- **Not:** Çözüm prompt'a "kg'a çevir" yazmak değil, şemaya kısıt koymak oldu. Şema kısıtı deterministik, prompt kuralı değil. Çevrim (deterministik iş) koda ait, modele değil.

### A3. Model kendi kendine kural uyduruyor — KAPANDI
- **Gözlem (temp=1):** Düşünce metninde "no set count. I should default to null or maybe 1?" diyor, sonunda `sets: 1` yazıyor. Prompt null diyordu.
- **Sorun:** Hallucination'ın görünmeyen hâli — veri uydurma değil, kural uydurma.
- **Kapanış:** `sets` alanına `Field(description=...)` ile "kullanıcı söylemediyse null, tahmin etme" niyeti eklendi. Açıklama şemayla birlikte modele gidiyor.

### A4. Egzersiz adı normalize edilmiyor — KAPANDI
- **Gözlem:** Prompt'tan few-shot örneği çıkarılınca aynı çalıştırmada `'Bench Press'` ve `'bench press'` birlikte geldi.
- **Sorun:** Veritabanında iki ayrı egzersiz olur, ilerleme grafiği ikiye bölünür.
- **Kapanış:** `exercise` alanına `Field(description="lowercase, standard name")`.
- **Ders:** Şema yapıyı garanti eder, içeriği garanti etmez. `Field.description` niyeti de tek kaynakta tutuyor.

---

## B. Format / parse

### B1. Prompt bir garanti değil, bir talep — KAPANDI
- **Gözlem (temp=1):** "Only return a json without any explanation" talimatına rağmen model düşünme sürecinin tamamını bastı ("Here's a thinking process: ..."), JSON'u cümle içine gömdü.
- **Hata:** `JSONDecodeError: Expecting value: line 1 column 1`
- **Kapanış:** Instructor `response_model` — model artık serbest metin döndüremiyor.

### B2. JSON sonrası fazladan içerik — KAPANDI
- **Hata (temp=0):** `JSONDecodeError: Extra data: line 1 column 122` — 121 karaktere kadar geçerli JSON, sonrasında fazladan içerik.
- **Kapanış:** B1 ile aynı.

---

## C. Tasarım boşluğu

### C1. Tamamen boş kayıt — KAPANDI
- **Girdi:** "chest day felt strong" → tüm alanlar `None`
- **Sorun:** Model doğru davrandı (uydurmadı) ama şemada "geçersiz girdi" kavramı yoktu; boş kayıt sessizce geçiyordu.
- **Kapanış:** `exercise: str` zorunlu bırakıldı. Artık `ValidationError` fırlıyor.
- **Açık kalan tasarım kararı:** Doğrulama hatasında ne yapılacak — çöksün mü, tekrar mı denesin, kullanıcıya hata mı dönsün? FastAPI endpoint'i yazılırken cevaplanacak.

---

## D. Kararlılık ve süre

### D1. temperature=0 deterministik değil
- **Gözlem:** Aynı cümle, aynı model. İki çağrı aynı çıktıyı verdi, üçüncüsü geçerli JSON bile değildi.
- **Not:** temp=0 token seçimini deterministik yapar ama uçtan uca tekrarlanabilirlik garanti etmez (batch'leme, farklı donanım, floating point sıralaması). "temp=0 koydum, artık sabit" yaygın bir yanılgı.

### D2. Yanıt süresi değişken
- **Çıplak API (15 Eyl):** 7 / 20 / 32 / 93 / 145 sn — aynı model, aynı cümle.
- **Instructor'lı (16 Eyl):** ilk çağrı 17 sn, sonrakiler 4-8 sn.
- **Sonuç:** FastAPI endpoint'i yazılırken timeout kararı bu veriye dayanacak.
