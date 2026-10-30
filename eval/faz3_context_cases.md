# Faz 3 — Bağlam gerektiren girdiler

Parser sadece metni görür. Buradaki girdilerde doğru kayıt için metinde olmayan bir bilgi (program, önceki antrenmanlar) gerekiyor. Eval setinde metnin desteklediği kadar etiketlenirler (kural 6); burada Faz 3 agent'ının (geçmişe bakarak) çözmesi gereken senaryo olarak durur.

| Girdi | Metinden çıkan | Bağlamla doğrusu | Neden parser bilemez |
|---|---|---|---|
| `hammer 8x12,5x2` (eval id 30) | `hammer-curl` | `seated-hammer-curl` | Seated olduğu programdan biliniyor, metinde yazmıyor |
