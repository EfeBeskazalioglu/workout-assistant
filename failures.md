# Kırılma kaydı

Model: `nvidia/nemotron-3.5-lightning:free` (OpenRouter)

- **15 Eyl:** çıplak API — prompt'ta JSON isteniyor, `json.loads()` ile parse ediliyor.
- **16 Eyl:** Pydantic + Instructor `response_model`. Prompt tek cümleye indi, şema tek kaynakta.
- **17 Eyl:** İki katmanlı şema — `WorkoutLog` (modele gösterilen) ve `WorkoutRecord` (uygulamanın kaydı) ayrıldı.

| # | Bulgu | Durum |
|---|---|---|
| A1 | Türkçe egzersiz adı → uydurma / çevrilmiyor | **açık** |
| A2 | Birim alanı serbest metin | kapandı 16 Eyl |
| A3 | Model kendi kendine kural uyduruyor | kapandı 16 Eyl |
| A4 | Egzersiz adı normalize edilmiyor | kapandı 16 Eyl |
| A5 | Belirtilen alan bazen atlanıyor | **açık** |
| A6 | Şemadaki her alan modele bir davet | kapandı 17 Eyl |
| A7 | Kısıt modeli hallucination'a zorlayabilir | kapandı 17 Eyl |
| B1 | Model format talimatını terk ediyor | kapandı 16 Eyl |
| B2 | JSON sonrası fazladan içerik | kapandı 16 Eyl |
| C1 | Boş / anlamsız girdi kayıt üretiyor | kapandı 17 Eyl (iki kez açıldı) |
| D1 | temperature=0 deterministik değil | kapanmaz (LLM'in doğası) |
| D2 | Yanıt süresi değişken | kapanmaz (altyapı) |

---

## A. Veri doğruluğu

### A1. Türkçe girdi → yanlış egzersiz — AÇIK
- **Girdi:** "bugün 4x8 mekik çektim"
- **Çıktılar:** 15 Eyl → `"leg press"` · 16 Eyl → `"leg curl"` · 17 Eyl → `"mekik"` (ham metin)
- **Sorun:** mekik = sit-up. Davranış değişti (uydurma yerine ham metin) ama sorun kapanmadı — DB'de "mekik" ve "sit-up" iki ayrı egzersiz olur.
- **Neden kapanmıyor:** Bilgi eksikliği, yapı sorunu değil. Şema, `Field(description=...)` ve Instructor yapıyı zorluyor, içeriği değil. Model "sit-up"ın standart ad olduğunu bilmiyor.
- **Çözüm yönü (Faz 3):** bilinen egzersiz listesi + RAG, ya da çıktıyı o listeye eşleme.

### A2. Birim alanı serbest metin — KAPANDI
- **Girdiler:** "135 lbs" → `"lbs"` · "120 pounds" → `"pounds"` · aynı çalıştırmada düşünce metninde `pounds`, JSON'da `lbs`
- **Kapanış:** `class Unit(str, Enum)` — izinli değerler `kg` / `lb`.
- **Not:** Çözüm prompt'a "kg'a çevir" yazmak değil, şemaya kısıt koymak oldu. Çevrim (deterministik iş) koda ait, modele değil.

### A3. Model kendi kendine kural uyduruyor — KAPANDI
- **Gözlem (temp=1):** Düşünce metninde "no set count. I should default to null or maybe 1?" diyor, sonunda `sets: 1` yazıyor.
- **Kapanış:** `sets` alanına `Field(description=...)` — "kullanıcı söylemediyse null, tahmin etme".

### A4. Egzersiz adı normalize edilmiyor — KAPANDI
- **Gözlem:** Few-shot örneği prompt'tan çıkınca aynı çalıştırmada `'Bench Press'` ve `'bench press'` birlikte geldi.
- **Kapanış:** `exercise` alanına `Field(description="lowercase, standard name")`.
- **Ders:** Şema yapıyı garanti eder, içeriği garanti etmez. `Field.description` niyeti de tek kaynakta tutuyor.

### A5. Belirtilen alan bazen atlanıyor — AÇIK
- **Girdi:** "benched 135 lbs for 5 reps"
- **Çıktılar:** bir çalıştırmada `reps=5`, diğerinde `reps=None` — aynı girdi, aynı ayarlar (temp=0).
- **Sorun:** Cümlede "5 reps" açıkça yazıyor. Şema `reps`'in int-veya-null olduğunu zorluyor, doğru değeri çıkardığını değil.
- **Not:** D1'in somut bir örneği. Eval setinde ölçülecek — kaç çalıştırmada kaç kez doğru geliyor, oran olarak yazılmalı (henüz sayılmadı).

### A6. Şemadaki her alan modele bir davet — KAPANDI
- **Gözlem:** `workout_date` alanı `WorkoutLog`'dayken model 2025-08-14, 2025-08-22, 2025-08-24 gibi rastgele tarihler uydurdu. `default_factory` hiç devreye girmedi, çünkü varsayılan sadece alan gelmediğinde çalışır.
- **Sorun:** Model bugünün tarihini bilmiyor, eğitim verisinden tarih atıyor.
- **Kapanış:** LLM şeması (`WorkoutLog`, sadece `exercises`) ile uygulama modeli (`WorkoutRecord`, `exercises` + `workout_date`) ayrıldı. Tarih model yanıtı geldikten sonra kod tarafından atanıyor.
- **Ders:** Modelden gelmesini istemediğin veri, modele gösterilen şemada bulunmamalı. `Field(description=...)` ile "doldurma" demek yetmez.

### A7. Kısıt modeli hallucination'a zorlayabilir — KAPANDI
- **Gözlem:** `min_length=1` LLM şemasına (`WorkoutLog`) konunca, "chest day felt strong" girdisinde model tüm alanları null olan uydurma bir `bench press` kaydı üretti. Öncesinde dürüstçe boş liste dönüyordu.
- **Sorun:** Boş liste sessiz ama dürüst; uydurulmuş kayıt sessiz ve yanlış. İkincisi daha kötü — DB'ye girer, geçmişi kirletir.
- **Kapanış:** `min_length=1` LLM şemasından kaldırıldı, sadece `WorkoutRecord`'da bırakıldı.
- **Ders:** Şemaya koyulan her kısıt modele bir talimat. Bir kısıt modelin dürüst davranmasını imkânsız kılıyorsa, model hallucination'a zorlanır — kısıt doğru davranışı değil, uyumlu görünen davranışı üretir.

---

## B. Format / parse

### B1. Prompt bir garanti değil, bir talep — KAPANDI
- **Gözlem (temp=1):** "Only return a json without any explanation" talimatına rağmen model düşünme sürecinin tamamını bastı ("Here's a thinking process: ..."), JSON'u cümle içine gömdü.
- **Hata:** `JSONDecodeError: Expecting value: line 1 column 1`
- **Kapanış:** Instructor `response_model` — model artık serbest metin döndüremiyor.

### B2. JSON sonrası fazladan içerik — KAPANDI
- **Hata (temp=0):** `JSONDecodeError: Extra data: line 1 column 122`
- **Kapanış:** B1 ile aynı.

---

## C. Tasarım boşluğu

### C1. Boş / anlamsız girdi kayıt üretiyor — KAPANDI (iki kez açıldı)
- **Girdi:** "chest day felt strong"
- **15 Eyl:** tüm alanları `None` olan bir kayıt üretiliyordu, sessizce geçiyordu.
- **16 Eyl:** `exercise: str` zorunlu bırakıldı → `ValidationError`. Kapandı sanıldı.
- **17 Eyl:** Model davranış değiştirdi — null dolu eleman yerine hiç eleman üretmemeye başladı. `exercises=[]` geçerli bir `list[Exercise]` olduğu için kısıt devreye girmedi. Yeniden açıldı.
- **Kapanış:** `min_length=1` `WorkoutRecord`'a kondu (LLM şemasına değil — bkz. A7). Model dürüstçe boş dönüyor, veri modeli reddediyor, hata `try/except` ile yakalanıyor.
- **Ders:** Şema kısıtı bir davranışı yakalar, model başka bir davranışa geçince boşluk açılır. "Kapandı" demek için yeni davranışı da test etmek gerekiyor.
- **Hata yakalama yeri:** `parse` içinde değil, çağıran tarafta. Parser'ın işi ayrıştırmak, ne yapılacağına karar vermek değil — aynı parser FastAPI'den çağrılınca 422 dönecek, CLI'dan çağrılınca mesaj basacak.

---

## D. Kararlılık ve süre

### D1. temperature=0 deterministik değil
- **Gözlem:** Aynı cümle, aynı model. İki çağrı aynı çıktıyı verdi, üçüncüsü geçerli JSON bile değildi. A5 de bunun bir örneği.
- **Not:** temp=0 token seçimini deterministik yapar ama uçtan uca tekrarlanabilirlik garanti etmez (batch'leme, farklı donanım, floating point sıralaması). "temp=0 koydum, artık sabit" yaygın bir yanılgı.

### D2. Yanıt süresi değişken
- **Çıplak API (15 Eyl):** 7 / 20 / 32 / 93 / 145 sn
- **Instructor'lı (16 Eyl):** ilk çağrı 17 sn, sonrakiler 4-8 sn
- **17 Eyl:** 4.5 / 6.4 / 10.8 / 21 / 42 / 77 sn — aynı gün içinde
- **Sonuç:** FastAPI endpoint'i yazılırken timeout kararı bu veriye dayanacak.
