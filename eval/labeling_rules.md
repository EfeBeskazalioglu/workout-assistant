# Etiketleme Kuralları

Eval setindeki her örnek için "doğru cevap" (golden label) bu kurallara göre yazılır.
Etiket, **modelin** döndürmesi gereken çıktıdır; kodun sonradan eklediği değerler (tarih, varsayılan birim) etikette yer almaz.

## Genel ilke
- **Girdide yazmayan alan `null` olur.**
  Gerekçe: Model bilmediği bir şeyi doldurmamalı; `Optional` alanlar "belirtilmemiş" diyebilmesi için var.
  Örnek: `"bench 60kg 5 tekrar"` → `sets = null`, `reps = 5`, `weight = 60`, `unit = kg`.

## Kurallar

1. **Egzersiz içermeyen girdi → boş liste.**
   Örnek: `"chest day felt strong"` → `exercises = []` (sistem 422 döner).
   Gerekçe: Egzersiz adı, set ya da rep yok; bir egzersiz adı uydurulsa bile anlamı olmaz.

2. **`x` gösterimi kastedilen anlama göre etiketlenir, sabit bir sıra yok.**
   Örnekler: `"35x5"` → 35 ağırlık × 5 rep · `"7x90 leg curl"` → 7 rep × 90 ağırlık · `"leg raise 3x8"` → 3 set × 8 rep.
   Gerekçe: Gerçek girdilerde `x` üç farklı anlamda kullanılıyor (ilk taslaktaki "AxB = set × rep" kuralı gerçek veriyle çürüdü). Belirsizliği sayıların büyüklüğünden çözmek modelin işi; eval bunu ölçer.
   Sondaki tek sayı ya da `2x` set sayısıdır: `"face pull 40x8 2"` → `sets = 2` · `"lateral 2x 10kg"` → `sets = 2`.

3. **Birim yazılmamışsa modelin etiketi `unit = null`; kg varsayımını kod yapar.**
   Örnek: `"squat 3x8 60"` → `unit = null`.
   Gerekçe: Kullanıcılar Türkiye'de, standart kg. Ama varsayımı model değil kod yapar (tarihte olduğu gibi); böylece model uydurmaz ve "belirtilmemiş" ile "kg" ayırt edilebilir.

4. **Egzersiz adları İngilizce, tek yazımla etiketlenir.**
   Yazım: küçük harf, kelimeler tireyle (`push-up`, `bench-press`).
   Örnek: `"şınav 3x15"` → `exercise = "push-up"`.
   Gerekçe: Egzersiz adlarının standardı İngilizce. Türkçe girdide araya çeviri katmanı giriyor ve ayrıca denetlenmeli (failures.md A1).
   Varyant (tutuş, incline, tek kol) adın parçasıdır: `incline-db-press`, `wide-grip-lat-pulldown`. Gerekçe: kaldırılan ağırlıklar farklı; aynı ada yazılırsa gelişim takibinde karışır.

5. **Ağırlığı ya da rep'i farklı setler ayrı kayıt; aynı setler tek kayıt. Set sayısı yazılmamışsa `sets` boş.**
   Örnek: `"7x80 6x85 latt pulldown narrow"` → iki kayıt (80 × 7, 85 × 6), ikisinde de `sets` boş. `"30x6x7"` → iki kayıt (30 × 6, 30 × 7), `sets` boş. `"2x25x6 shoulder press"` → tek kayıt, `sets = 2`. `"lateral raise 10x10"` → `sets` boş. Aynı set metinde tekrar yazılmışsa sayısı `sets` olur: `"45x5x5 t bar"` → tek kayıt (45 × 5), `sets = 2`.
   Gerekçe: Mevcut şemada egzersiz başına tek `sets/reps/weight` var. Set listesi olan şema doğru model ama büyük değişiklik → Hafta 4 (Alembic) adayı. `sets` boş kalır çünkü modelin talimatı (`Field` description, A3) "söylenmediyse null"; etiket talimatla çelişirse eval modeli değil bu çelişkiyi ölçer. Set sayısı bilgisini kayıt sayısı taşır; kullanım için kod `sets = null` → 1 yazar (kg varsayımıyla aynı kalıp: model metinde olanı çıkarır, varsayımları kod yapar).

6. **Etiket, metnin desteklediği kadardır; bağlamdan gelen bilgi eklenmez.**
   Örnek: `"pec fly"` → `pec-fly` (pec deck mi cable mı metinden çıkmaz).
   Gerekçe: Parser'ın bağlamı yok (program, önceki hareket). Bağlam gerektiren satırlar `faz3_context_cases.md`'de — Faz 3 agent'ının test senaryosu.
   Örnek: `"hammer 8x12,5x2"` → `hammer-curl` (seated olduğu bağlamdan biliniyor, metinde yok); `"seated hammer ..."` → `seated-hammer-curl`.

7. **Gelecek zamanda yazılmış antrenman kayıt olarak etiketlenir; yapılmayacağı söylenen egzersiz kayıt değildir.**
   Örnek: `"press salonda yok yerine hex swuat yapıcam 60x8 x2"` → tek kayıt `hex-squat` (60 × 8, `sets = 2`); press kayıt değil.
   Gerekçe: Ağırlık ve tekrar belirtilmişse "yapıcam" denilip sonra yapılmış ve yazılmış demektir.

## Egzersiz adı sözlüğü
| Girdide | Etiket |
|---|---|
| incline db press | incline-db-press |
| pec fly | pec-fly |
| shd press, shoulder press | shoulder-press |
| lateral raise, lateral | lateral-raise |
| triceps pushdown, pushdpwn | triceps-pushdown |
| tricep extension, triceps extension | triceps-extension |
| wide grip latt pulldown, eide grip lat pull | wide-grip-lat-pulldown |
| latt pulldown narrow | narrow-grip-lat-pulldown |
| t bar row, tbar row, t bar | t-bar-row |
| leg raise | leg-raise |
| face pull | face-pull |
| seated hammer | seated-hammer-curl |
| hammer | hammer-curl |
| leg ext | leg-extension |
| leg curl | leg-curl |
| db press | db-press |
| bayesian curl tek kol | single-arm-bayesian-curl |
| hex swuat | hex-squat |

## Karşılaştırma
- `exercise` alanı karşılaştırılırken iki taraf da normalize edilir: küçük harf, boşluk ve tire yok sayılır (`"Push Up"` = `"push-up"`).
- Kanonik egzersiz listesi Faz 3'e (RAG) kalıyor.