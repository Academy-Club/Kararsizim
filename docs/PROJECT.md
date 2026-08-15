# Kararsızım — Proje Planı ve Teknik Şartname

> **Bu dosya nasıl kullanılır?**
> 1. Boş bir repo aç, bu dosyayı `docs/PROJECT.md` olarak koy.
> 2. Repo kökünde şu içerikle bir `CLAUDE.md` oluştur:
>    `Bu projenin tam şartnamesi docs/PROJECT.md dosyasındadır. Her görevden önce oku. Fazlar sırayla uygulanır, faz atlanmaz.`
> 3. Claude Code'u aç ve şu şekilde ilerle: `docs/PROJECT.md dosyasını oku ve Faz 0'ı uygula.`
> 4. Her fazın sonunda "Kabul kriterleri" listesini birlikte doğrula, commit at, sonra bir sonraki faza geç.

---

## 1. Proje Özeti

**Kararsızım**, kullanıcıların kararsız kaldıkları konuları küçük anketlere dönüştürüp kalabalığa danıştığı bir web uygulamasıdır.

- **Slogan:** Sen sor, kalabalık karar versin.
- **Tipik kullanım:** "Bugün sinemaya mı gitsem, restorana mı?" → 2–5 seçenek → herkes oylar → sonuç anlık görünür.
- **Bu aşamanın hedefi:** Çalışan, deploy edilmiş, gösterilebilir bir **prototip**. Ölçeklenebilirlik, mikro servisler, karmaşık altyapı **şu an hedef değil**.

### Ürün kuralları (değişmez)

| Kural | Detay |
|---|---|
| Takip sistemi yok | Kullanıcılar birbirini takip etmez. Tek bir genel akış vardır. |
| Herkes her anketi görür | Gizli/özel anket yok. |
| Oy vermek için üyelik gerekmez | Anonim ziyaretçi de oy kullanabilir. |
| Anket oluşturmak için üyelik **gerekir** | Giriş yapmamış kullanıcı oluşturma sayfasına gitmeye çalışırsa girişe yönlendirilir. |
| Kayıt alanları | e-posta + parola + kullanıcı adı (üçü de zorunlu). |
| E-posta asla görünmez | Ne arayüzde, ne API cevaplarında, ne HTML kaynağında. Sadece kullanıcı adı gösterilir. |
| Seçenek sayısı | En az 2, en fazla 5. |
| Bir kişi bir ankete bir kez oy verir | Oy değiştirilemez (v1'de). |

### v1 kapsamı dışında (şimdilik yapma)

Takip/arkadaşlık, yorumlar, bildirimler, özel mesaj, resim yükleme, kategori/etiket sistemi, e-posta doğrulama, parola sıfırlama e-postası, sosyal giriş, mobil uygulama, çok dillilik, admin paneli özelleştirmesi, gerçek zamanlı websocket.

---

## 2. Teknoloji Yığını

| Katman | Seçim | Not |
|---|---|---|
| Dil | Python 3.14 | Yerelde kurulu güncel sürüm; Vercel build sırasında kendi runtime'ını seçer |
| Backend | Django 6.x (güncel sürüm) | Template engine dahil, ayrı API katmanı yok. (Not: ilk yazımda 5.1 pinliydi; 5.1 artık EOL olduğu için 2026-08-15'te güncel sürüme geçildi.) |
| Veritabanı | Supabase (PostgreSQL) | Sadece Postgres olarak kullanılır — Supabase Auth/RLS **kullanılmaz** |
| DB sürücüsü | `psycopg[binary]` (psycopg 3) | |
| Kimlik doğrulama | Django built-in auth + custom User modeli | Supabase Auth'a hiç dokunma |
| Frontend | HTML + CSS + Vanilla JS | Aynı repo, Django template'leri içinde. React/Vue/Tailwind/Bootstrap **yok** |
| Statik dosyalar | WhiteNoise | |
| Deployment | Vercel (Serverless Python) | |
| Bağımlılık | `requirements.txt` | Poetry/uv yok |

### Neden böyle?
Prototip aşamasında tek bir Django süreci hem HTML üretiyor hem de küçük JSON uçları veriliyor. DRF, Celery, Redis, Docker **eklenmeyecek**. Yeni bir bağımlılık gerekiyorsa Claude Code önce sorar.

### requirements.txt (başlangıç)

```
Django==6.1.*
psycopg[binary]==3.3.*
dj-database-url==3.1.*
python-dotenv==1.2.*
whitenoise==6.12.*
```

---

## 3. Repo Yapısı

```
kararsizim/
├── CLAUDE.md
├── docs/
│   └── PROJECT.md              # bu dosya
├── config/                     # Django project
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/                   # kullanıcı, kayıt, giriş
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── polls/                      # anket, seçenek, oy
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── services.py             # oylama iş mantığı
│   ├── selectors.py            # sorgular
│   └── urls.py
├── templates/
│   ├── base.html
│   ├── partials/
│   │   ├── header.html
│   │   ├── poll_card.html
│   │   ├── option_row.html
│   │   └── toast.html
│   ├── polls/
│   │   ├── index.html
│   │   ├── detail.html
│   │   ├── create.html
│   │   └── profile.html
│   ├── accounts/
│   │   ├── register.html
│   │   └── login.html
│   ├── 404.html
│   └── 500.html
├── static/
│   ├── css/
│   │   ├── tokens.css
│   │   ├── base.css
│   │   └── components.css
│   ├── js/
│   │   ├── vote.js
│   │   ├── poll-form.js
│   │   └── toast.js
│   └── img/
│       └── logo.svg
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── vercel.json                 # opsiyonel — sadece maxDuration gibi ayarlar için
```

**Kural:** View'lar ince olur. Veritabanı yazma mantığı `services.py`, okuma sorguları `selectors.py` içinde durur. Template içinde sorgu tetikleyen kod yazma.

---

## 4. Veri Modeli

### 4.1 `accounts.User` (AbstractUser'dan türetilir)

`AUTH_USER_MODEL = "accounts.User"` ilk migration'dan **önce** ayarlanır.

| Alan | Tip | Kural |
|---|---|---|
| `username` | CharField(20), unique | 3–20 karakter, regex `^[a-zA-Z0-9_]{3,20}$`, büyük/küçük harf duyarsız benzersizlik (kayıtta `lower()` ile kontrol) |
| `email` | EmailField, unique, **zorunlu** | Normalize edilir (lowercase) |
| `date_joined` | otomatik | |

Yasaklı kullanıcı adları listesi: `admin, root, api, static, anket, giris, kayit, cikis, kullanici, hakkinda`.

### 4.2 `polls.Poll`

| Alan | Tip | Kural |
|---|---|---|
| `public_id` | CharField(12), unique, index | URL'de kullanılır. `secrets.token_urlsafe` tabanlı 10–12 karakterlik base62. Türkçe slug derdi ve id tahmini olmaz. |
| `question` | CharField(140) | 10–140 karakter, zorunlu |
| `description` | CharField(280), blank | Opsiyonel açıklama |
| `author` | FK → User, `on_delete=CASCADE`, `related_name="polls"` | |
| `status` | CharField choices: `active`, `closed` | Varsayılan `active` |
| `total_votes` | PositiveIntegerField, default 0 | Denormalize sayaç, sıralama için |
| `created_at` | DateTimeField(auto_now_add), index | |
| `closes_at` | DateTimeField, null | Opsiyonel otomatik kapanış |

- `is_open` property: `status == "active"` ve (`closes_at` boş veya gelecekte).
- `get_absolute_url()` → `/anket/<public_id>/`
- Meta ordering: `-created_at`

### 4.3 `polls.Option`

| Alan | Tip | Kural |
|---|---|---|
| `poll` | FK → Poll, CASCADE, `related_name="options"` | |
| `text` | CharField(80) | 1–80 karakter, boş olamaz |
| `position` | PositiveSmallIntegerField | 0–4 |
| `vote_count` | PositiveIntegerField, default 0 | Denormalize sayaç |

- `UniqueConstraint(poll, position)`
- Meta ordering: `position`
- Aynı anket içinde büyük/küçük harf duyarsız aynı metin iki kez olamaz (form validasyonu).

### 4.4 `polls.Vote`

| Alan | Tip | Kural |
|---|---|---|
| `poll` | FK → Poll, CASCADE | |
| `option` | FK → Option, CASCADE | |
| `user` | FK → User, null, blank, SET_NULL | Anonim oyda boş |
| `voter_key` | CharField(64), index | Anonim oy için oturum türevli hash |
| `created_at` | DateTimeField(auto_now_add) | |

Constraint'ler:

```python
UniqueConstraint(fields=["poll", "user"], condition=Q(user__isnull=False), name="uniq_vote_per_user")
UniqueConstraint(fields=["poll", "voter_key"], condition=Q(user__isnull=True), name="uniq_vote_per_anon")
```

**`voter_key` üretimi:** `sha256(session_key + VOTER_KEY_SALT)` → hexdigest. Oturum yoksa `request.session.save()` ile oluşturulur. Giriş yapmış kullanıcıda da doldurulur ama benzersizlik `user` üzerinden işler.

**Bilinen sınır (kabul edilmiş):** Çerezini temizleyen anonim kullanıcı tekrar oy verebilir. Prototipte kabul edilebilir; Faz 7'de IP tabanlı hız sınırı ile hafifletilir. Ham IP adresi **saklanmaz**, gerekirse tuzlanmış hash saklanır.

---

## 5. Sayfa ve URL Haritası

| URL | View | Erişim | İş |
|---|---|---|---|
| `/` | `polls.index` | Herkes | Anket akışı. Sekmeler: **Yeni**, **Popüler** (son 7 günün oy sayısı), **Kapananlar**. Sayfa başı 20 kayıt, "Daha fazla göster" butonu (`?page=2`). |
| `/anket/<public_id>/` | `polls.detail` | Herkes | Anket detayı, oy verme veya sonuç görünümü |
| `/anket/olustur/` | `polls.create` | **Giriş gerekli** | Anket oluşturma formu |
| `/anket/<public_id>/oy/` | `polls.vote` (POST) | Herkes | Oy kaydı. JSON veya redirect döner |
| `/anket/<public_id>/sonuc/` | `polls.results` (GET, JSON) | Herkes | Anlık sonuçlar |
| `/anket/<public_id>/kapat/` | `polls.close` (POST) | Sadece sahibi | Anketi kapatır |
| `/anket/<public_id>/sil/` | `polls.delete` (POST) | Sadece sahibi | Anketi siler (onay ekranı ile) |
| `/kullanici/<username>/` | `polls.profile` | Herkes | O kullanıcının anketleri + toplam anket/oy sayısı. **E-posta yok.** |
| `/kayit/` | `accounts.register` | Anonim | Kayıt formu, başarıda otomatik giriş |
| `/giris/` | `accounts.login` | Anonim | `?next=` desteği |
| `/cikis/` | `accounts.logout` (POST) | Giriş yapmış | |
| `/admin/` | Django admin | Superuser | Sadece geliştirme/moderasyon |

**Not:** Giriş yapmamış kullanıcı `/anket/olustur/` adresine giderse `/giris/?next=/anket/olustur/` adresine yönlendirilir ve giriş sayfasında "Anket oluşturmak için giriş yapman gerekiyor" bilgi kutusu gösterilir.

---

## 6. İş Kuralları

### Oy verme akışı
1. Anket kapalıysa → oy reddedilir, sonuçlar gösterilir.
2. `option_id` gerçekten bu ankete ait mi? Değilse 400.
3. Bu kişi (user veya voter_key) daha önce oy vermiş mi? Vermişse 409 ve sonuçlar döner.
4. `transaction.atomic()` içinde: `Vote` oluştur → `Option.vote_count` ve `Poll.total_votes` alanlarını `F()` ifadesiyle artır.
5. `IntegrityError` yakalanır → "Bu ankete zaten oy verdin" mesajı.
6. Oy verilen anket id'si `request.session["voted_polls"]` listesine eklenir (hızlı UI kontrolü için).

### Sonuç görünürlüğü
- Oy vermeden önce yüzdeler **gizlidir** (sürü psikolojisini kırmak için). Sadece toplam oy sayısı görünür: "142 kişi oy verdi".
- Oy verildikten sonra veya anket kapandıktan sonra tüm yüzdeler açılır.
- Kendi anketinin sahibi oy vermeden de sonuçları görebilir.

### Anket oluşturma
- Form: soru + açıklama (ops.) + 2 seçenek (varsayılan görünür) + "Seçenek ekle" ile 5'e kadar.
- Sunucu tarafında da 2–5 kontrolü yapılır (JS'e güvenme).
- Boş bırakılan seçenek satırları yok sayılır; geriye 2'den az kalırsa hata.
- Aynı kullanıcı günde en fazla **10** anket açabilir (spam koruması).

---

## 7. Arayüz ve Tasarım Sistemi

### Yön
Hedef kitle genç. Arayüz **açık zeminli, canlı renkli, kalın ve neşeli** ama dağınık değil. Cesaret tek bir yerde harcanır: **karar çubuğu**. Geri kalan her şey sakin ve disiplinli durur.

### Renk paleti (`static/css/tokens.css`)

```css
:root {
  /* zemin ve metin */
  --paper:      #FAF9FF;   /* sayfa arka planı, hafif lila beyaz */
  --surface:    #FFFFFF;   /* kart yüzeyi */
  --ink:        #16143A;   /* ana metin, koyu mor-lacivert */
  --muted:      #6B6890;   /* ikincil metin */
  --line:       rgba(22, 20, 58, 0.10); /* kenarlık */

  /* canlı renkler — seçenek renkleri de bunlardan gelir */
  --violet:     #5B3DF5;   /* birincil aksiyon */
  --pink:       #FF3D8B;
  --mint:       #00D19A;
  --sun:        #FFC531;
  --sky:        #2BB3FF;

  /* seçenek sırasına göre sabit renkler */
  --opt-0: var(--violet);
  --opt-1: var(--pink);
  --opt-2: var(--mint);
  --opt-3: var(--sun);
  --opt-4: var(--sky);

  /* durum */
  --danger:     #E5484D;

  /* gölge: griye değil, mora çalar */
  --shadow-sm: 0 2px 8px rgba(91, 61, 245, 0.08);
  --shadow-md: 0 8px 24px rgba(91, 61, 245, 0.12);

  /* biçim */
  --radius-card: 20px;
  --radius-pill: 999px;
  --radius-input: 14px;

  /* aralık ölçeği */
  --sp-1: 4px; --sp-2: 8px; --sp-3: 12px; --sp-4: 16px;
  --sp-5: 24px; --sp-6: 32px; --sp-7: 48px; --sp-8: 64px;
}
```

**Kural:** Şablonlarda ve CSS'te ham hex kodu yazma, sadece bu değişkenleri kullan.

### Tipografi
- **Display:** `Bricolage Grotesque` (700/800) — başlıklar, logo, anket sorusu. Karakterli ama okunur; Türkçe karakterleri destekler.
- **Gövde:** `Inter` (400/500/600) — paragraf, buton, form.
- **Sayısal:** `JetBrains Mono` (500) — yüzdeler ve oy sayıları. Rakamlar sabit genişlikte olduğu için sonuçlar animasyon sırasında zıplamaz.
- Google Fonts'tan `latin,latin-ext` alt kümesiyle yüklenir (`ç ğ ı İ ş ö ü` için `latin-ext` **şart**).
- Tip ölçeği: 12 / 14 / 16 / 20 / 26 / 34 / 44 px.

### İmza öğesi: **Karar Çubuğu**
Her anket kartının üstünde, seçeneklerin oy paylarını gösteren tek parça, yatay, dilimli bir çubuk bulunur. Dilim renkleri seçenek sırasına göre `--opt-0..4`.

Çubuğun altında **kararsızlık rozeti** yer alır ve ilk iki seçenek arasındaki farka göre metni değişir:

| Fark | Rozet metni |
|---|---|
| ≤ %5 | "Kalabalık da kararsız" |
| %6–20 | "Az farkla önde" |
| > %20 | "Karar net" |
| 0 oy | "İlk oyu sen ver" |

Bu rozet, ürünün adıyla doğrudan konuşan tek dekoratif olmayan öğedir — ana ekranda ve detay sayfasında görünür.

### Bileşenler
- **Kart:** beyaz yüzey, `--radius-card`, 1px `--line` kenarlık, `--shadow-sm`; hover'da `--shadow-md` ve 2px yukarı kayma.
- **Seçenek satırı (oy öncesi):** tam genişlik, sol tarafında ilgili `--opt-N` renginde 6px dikey şerit, hover'da o rengin %8 opaklıkta zemini.
- **Seçenek satırı (oy sonrası):** aynı satırın içinde arka plandan yüzdeye kadar dolan renk dolgusu + sağda mono yazıyla `%42`. Kullanıcının kendi oyu kalın çerçeve ve ✓ ile işaretlenir.
- **Buton (birincil):** `--violet` zemin, beyaz metin, `--radius-pill`, 600 ağırlık.
- **Buton (ikincil):** şeffaf zemin, 1.5px `--ink` kenarlık.
- **Toast:** sağ altta, 3 saniye, `--ink` zemin, beyaz metin.
- **Boş durum:** "Henüz anket yok. İlk kararsızlığını sen paylaş." + oluştur butonu.

### Hareket
- Sonuç çubukları `width` üzerinden 450ms `cubic-bezier(.2,.8,.2,1)` ile dolar.
- Sadece bu ve buton hover'ları. Başka animasyon yok.
- `@media (prefers-reduced-motion: reduce)` altında tüm geçişler kapatılır.

### Erişilebilirlik (pazarlık konusu değil)
- Metin/zemin kontrastı en az 4.5:1. `--sun` üzerine **asla** beyaz metin yazma, `--ink` kullan.
- Görünür klavye odağı: `outline: 3px solid var(--sun); outline-offset: 2px;`
- Sonuç bölgesi `aria-live="polite"`.
- Renk tek başına bilgi taşımaz: her seçenekte yüzde metni de yazar.
- Mobil öncelikli; 360px genişlikte yatay kaydırma olmaz. Dokunma hedefleri en az 44px.

### Metin dili (arayüz kopyası)
- Arayüz **Türkçe**, samimi ve kısa. Kod içindeki değişken/fonksiyon isimleri **İngilizce**.
- Butonlar ne yaptığını söyler: "Anket oluştur", "Oy ver", "Sonuçları gör", "Anketi kapat".
- Hata mesajları özür dilemez, ne olduğunu ve ne yapılacağını söyler: "Bu ankete zaten oy verdin." / "En az 2 seçenek gerekli."

---

## 8. Fazlar

Her faz tek başına çalışır durumda bitmeli ve commit'lenmeli. Faz atlanmaz.

---

### Faz 0 — İskelet ve yerel çalışma
**Amaç:** `python manage.py runserver` ile açılan boş bir Django projesi.

Görevler:
1. Sanal ortam, `requirements.txt`, `.gitignore` (`.env`, `__pycache__`, `staticfiles/`, `db.sqlite3`).
2. `config` projesi + `accounts` ve `polls` uygulamaları.
3. `settings.py`: `python-dotenv` ile `.env` okuma, `dj-database-url`, `DEBUG` env'den, `ALLOWED_HOSTS` env'den, `TEMPLATES.DIRS = [BASE_DIR / "templates"]`, `STATICFILES_DIRS = [BASE_DIR / "static"]`, `TIME_ZONE = "Europe/Istanbul"`, `LANGUAGE_CODE = "tr"`.
4. Yerelde **SQLite** kullanılabilir (`DATABASE_URL` boşsa SQLite'a düş) — Supabase Faz 1'de bağlanır.
5. `templates/base.html` + `static/css/tokens.css` (Bölüm 7'deki değişkenler) + boş `/` sayfası "Kararsızım" yazsın.
6. `.env.example` doldur.

**Kabul kriterleri:**
- [ ] `runserver` hatasız açılıyor, `/` adresinde "Kararsızım" görünüyor.
- [ ] `tokens.css` yükleniyor, sayfa arka planı `--paper`.
- [ ] `.env` git'e girmiyor.

---

### Faz 1 — Veri modeli ve Supabase bağlantısı
**Amaç:** Tüm tablolar Supabase'de oluşmuş olsun.

Görevler:
1. `accounts.User` modeli (AbstractUser), `AUTH_USER_MODEL` ayarı. **Bu migration'dan önce ayarlanmalı.**
2. `polls.Poll`, `polls.Option`, `polls.Vote` modelleri (Bölüm 4).
3. `public_id` üreten yardımcı: `polls/utils.py::generate_public_id()`.
4. Supabase projesi oluştur, connection string'i `.env`'e koy (Bölüm 10 ve 11'deki uyarılara birebir uy).
5. `makemigrations` + `migrate` **yerelden** çalıştır (session pooler / direct bağlantı ile).
6. Django admin'e üç modeli de kaydet (`Option` için `TabularInline`).
7. Test verisi üreten yönetim komutu: `python manage.py seed_demo` → 3 kullanıcı, 12 anket, rastgele oylar.

**Kabul kriterleri:**
- [ ] Supabase Table Editor'de `accounts_user`, `polls_poll`, `polls_option`, `polls_vote` tabloları görünüyor.
- [ ] `seed_demo` çalışıyor, admin panelinde anketler ve seçenekleri listeleniyor.
- [ ] Aynı kullanıcıyla aynı ankete iki `Vote` eklenmeye çalışıldığında veritabanı `IntegrityError` veriyor (shell'de doğrula).

---

### Faz 2 — Kimlik doğrulama
**Amaç:** Kayıt / giriş / çıkış çalışsın.

Görevler:
1. `accounts/forms.py`: `RegisterForm` (username, email, password1, password2). Kullanıcı adı regex ve yasaklı liste kontrolü; e-posta benzersizliği için özel `clean_email`; büyük/küçük harf duyarsız username kontrolü.
2. Django'nun varsayılan parola doğrulayıcıları açık kalsın (min 8 karakter).
3. Kayıt başarılı → otomatik `login()` → `/` adresine yönlendir + "Hoş geldin, @kullaniciadi" toast'ı.
4. `LoginView` / `LogoutView` (çıkış sadece POST) ve `?next=` desteği.
5. `templates/accounts/register.html` ve `login.html`, tasarım sistemine uygun.
6. Header'da durum: giriş yapılmışsa `@kullaniciadi` + "Anket oluştur"; değilse "Giriş yap" + "Kayıt ol".
7. `LOGIN_URL = "/giris/"`.

**Kabul kriterleri:**
- [ ] Kayıt, giriş, çıkış uçtan uca çalışıyor.
- [ ] Kayıtlı bir e-posta ile tekrar kayıt olunamıyor; hata mesajı Türkçe ve alanın altında.
- [ ] `KullaniciAdi` ile `kullaniciadi` çakışması engelleniyor.
- [ ] Hiçbir sayfada e-posta adresi render edilmiyor (sayfa kaynağını ara).

---

### Faz 3 — Anket oluşturma ve listeleme
**Amaç:** Giriş yapan kullanıcı anket açabilsin, herkes akışta görsün.

Görevler:
1. `PollForm` + `OptionFormSet` (veya `option_1..option_5` alanlarıyla düz form — hangisi daha basitse). Sunucu tarafı 2–5 kontrolü zorunlu.
2. `create` view'ı `@login_required`. Günlük 10 anket sınırı.
3. `static/js/poll-form.js`: "Seçenek ekle" / "Kaldır" (5'te buton pasifleşir, 2'nin altına inilemez). **JS kapalıyken form yine de 2 seçenekle gönderilebilmeli.**
4. `polls/index.html`: kart ızgarası (mobilde tek sütun, ≥900px'te iki sütun), sekmeler Yeni/Popüler/Kapananlar, sayfalama.
5. `partials/poll_card.html`: soru, `@yazar`, göreli zaman ("3 saat önce"), toplam oy, karar çubuğu, kararsızlık rozeti.
6. Anket detay sayfası (henüz oylama yok, sadece görünüm).
7. `profile.html`: kullanıcının anketleri.
8. N+1 sorgu yok: `select_related("author")` + `prefetch_related("options")`.

**Kabul kriterleri:**
- [ ] Giriş yapmadan `/anket/olustur/` → `/giris/?next=...` yönlendirmesi.
- [ ] 1 seçenekle veya 6 seçenekle form gönderilemiyor (JS kapalıyken de).
- [ ] Akışta 20 anket listeleniyor, "Daha fazla göster" çalışıyor.
- [ ] Django Debug Toolbar veya `assertNumQueries` ile ana sayfa sorgu sayısı sabit (anket sayısıyla artmıyor).

---

### Faz 4 — Oylama ve sonuçlar
**Amaç:** Ürünün kalbi.

Görevler:
1. `polls/services.py::cast_vote(poll, option, user, voter_key)` — Bölüm 6'daki akış, `transaction.atomic()` ve `F()` ile.
2. `voter_key` üretimi ve session yönetimi (`polls/utils.py`).
3. `vote` view'ı: `Accept: application/json` veya `X-Requested-With` başlığı varsa JSON, yoksa `redirect` (progressive enhancement).
4. `results` view'ı: `{"total": n, "options": [{"id", "text", "count", "percent"}], "voted_option_id": null|id, "is_open": bool}`.
5. `static/js/vote.js`: tıklama → `fetch` POST (CSRF token header'ı ile) → sonuç çubuklarını animasyonla doldur. Hata durumunda toast.
6. Sonuç görünürlük kuralı (oy vermeden yüzde gizli).
7. Yuvarlama: yüzdeler `round()` sonrası toplamı 100 değilse en büyük seçenek üzerinden düzeltilir.
8. Kendi anketini kapatma ve silme (silmede onay adımı).
9. Yazar kendi anketine oy verebilir (yasak değil).

**Kabul kriterleri:**
- [ ] Anonim ziyaretçi oy verebiliyor; sayfayı yenileyince tekrar oy veremiyor, sonuçları görüyor.
- [ ] Aynı kullanıcı iki farklı sekmeden aynı anda oy vermeye çalıştığında ikincisi 409 alıyor, oy sayacı 1 artıyor.
- [ ] JS kapalıyken oy verme çalışıyor (form POST + redirect).
- [ ] Yüzdeler toplamı her zaman 100.
- [ ] Kapalı ankette oy butonları devre dışı.

---

### Faz 5 — Arayüz cilası
**Amaç:** Bölüm 7'nin tam uygulanması.

Görevler:
1. `base.css` ve `components.css` yazımı; tüm renk/aralık değerleri token'lardan.
2. Karar çubuğu ve kararsızlık rozeti bileşeni.
3. Fontların yüklenmesi (`preconnect`, `display=swap`, `latin-ext`).
4. Boş durumlar, yükleniyor durumları, 404 ve 500 sayfaları.
5. Mobil (360px) → tablet → masaüstü kontrolü.
6. Erişilebilirlik geçişi: odak halkaları, kontrast, `aria-live`, `prefers-reduced-motion`.
7. `logo.svg`, favicon, `og:title`/`og:description`/`og:image` meta etiketleri (paylaşımda anket sorusu görünsün).

**Kabul kriterleri:**
- [ ] 360px genişlikte yatay kaydırma yok.
- [ ] Sadece klavye ile anket oluşturup oy verilebiliyor, odak her adımda görünür.
- [ ] Lighthouse Accessibility ≥ 90.
- [ ] CSS'te ham hex kodu yok (token dosyası hariç).

---

### Faz 6 — Vercel'e deployment
**Amaç:** Canlıda çalışan bir URL.

Görevler:
1. `settings.py` içinde `WSGI_APPLICATION` ve `STATIC_ROOT` tanımlı olduğundan emin ol — Vercel gerisini kendi bulur. Sarmalayıcı dosya veya rewrite kuralı **yazma**.
2. Vercel proje ayarlarında environment variable'lar (Bölüm 10).
3. `ALLOWED_HOSTS` ve `CSRF_TRUSTED_ORIGINS` production değerleri.
4. `SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` (production'da).
5. Supabase **transaction pooler** bağlantısı + `CONN_MAX_AGE=0` + `DISABLE_SERVER_SIDE_CURSORS=True`.
6. `vercel dev` ile yerelde deploy ortamını dene, sonra `vc deploy`.
7. `docs/DEPLOY.md`: migration'lar yerelden nasıl çalıştırılır, env değişkenleri nasıl set edilir.

**Kabul kriterleri:**
- [ ] Canlı URL açılıyor, CSS ve JS Vercel CDN'den yükleniyor (404 yok).
- [ ] Canlıda kayıt olup anket açılabiliyor, oy verilebiliyor.
- [ ] `DEBUG=False` ve hata sayfaları özel şablonları gösteriyor.
- [ ] Soğuk başlangıçtan sonra ilk istek 500 vermiyor (bağlantı havuzu ayarları doğru).

---

### Faz 7 — Sertleştirme ve küçük eklemeler (opsiyonel)
Sıraya bağlı değil, prototip gösterildikten sonra:

1. Hız sınırı: anonim oy için IP hash + saatlik limit; kayıt için basit honeypot alanı.
2. Anket paylaş butonu (`navigator.share`, fallback: panoya kopyala).
3. Anasayfada arama (`icontains` ile soru araması).
4. "Kararsızlık kartı" — sonucu görsel olarak dışa aktarma (canvas).
5. Basit raporlama: kullanıcı bir anketi "uygunsuz" olarak işaretler, admin görür.
6. Test kapsamının genişletilmesi.
7. `closes_at` gelen anketlerin otomatik kapanması (view içinde tembel kontrol; cron yok).

---

## 9. Test

Django'nun kendi test runner'ı kullanılır (`python manage.py test`). Ayrı test framework'ü kurma.

Yazılması **zorunlu** testler:

**accounts**
- Aynı e-posta ile ikinci kayıt reddedilir.
- Büyük/küçük harf farkıyla aynı kullanıcı adı alınamaz.
- Geçersiz karakterli kullanıcı adı reddedilir.

**polls — oluşturma**
- Anonim kullanıcı `/anket/olustur/` → 302 giriş.
- 1 seçenekli gönderim → form hatası.
- 6 seçenekli gönderim → form hatası.
- Aynı metinli iki seçenek → form hatası.

**polls — oylama**
- Anonim oy başarılı, sayaçlar +1.
- Aynı session ikinci oy → 409, sayaç değişmez.
- Aynı kullanıcı ikinci oy → 409.
- Başka ankete ait `option_id` → 400.
- Kapalı ankete oy → 403.
- Yüzde toplamı = 100 (3 ve 7 gibi bölünmeyen sayılarla).

**gizlilik**
- Anket detayı ve profil sayfası HTML'inde yazarın e-postası geçmiyor.
- `/anket/<id>/sonuc/` JSON'unda hiçbir e-posta veya user id sızmıyor.

---

## 10. Ortam Değişkenleri

`.env.example`:

```bash
# Django
DJANGO_SECRET_KEY=degistir-bunu
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000

# Anonim oy anahtarı tuzu — production'da mutlaka farklı olsun
VOTER_KEY_SALT=degistir-bunu-da

# Supabase — uygulama çalışırken (Transaction pooler, port 6543)
DATABASE_URL=postgresql://postgres.<PROJE_REF>:<PAROLA>@aws-0-<BOLGE>.pooler.supabase.com:6543/postgres

# Supabase — sadece migration için (Session pooler, port 5432)
DATABASE_URL_DIRECT=postgresql://postgres.<PROJE_REF>:<PAROLA>@aws-0-<BOLGE>.pooler.supabase.com:5432/postgres
```

Production'da (Vercel dashboard) `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=.vercel.app`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://<proje>.vercel.app`.

---

## 11. Supabase + Vercel Tuzakları

Bu bölüm çok önemli, kısa yoldan geçilmeye çalışılırsa deployment saatler kaybettirir.

### 11.1 Supabase bağlantısı
- **Doğrudan bağlantı (`db.<ref>.supabase.co:5432`) kullanma.** Yalnızca IPv6 üzerinden erişilebilir; Vercel'den bağlanamazsın. Her zaman **pooler** adresini kullan.
- **Uygulama** için: **Transaction pooler, port 6543**. Serverless'ta doğru olan budur.
- **Migration** için: **Session pooler, port 5432**. Transaction modunda migration'lar patlar.
- Transaction pooler prepared statement'ları desteklemez. `settings.py`'de:

```python
DATABASES = {"default": dj_database_url.config(default=..., conn_max_age=0)}
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
DATABASES["default"].setdefault("OPTIONS", {})["prepare_threshold"] = None
```

- `CONN_MAX_AGE=0` şart. Serverless'ta kalıcı bağlantı tutmak havuzu tüketir.
- **Migration'lar Vercel build sırasında çalıştırılmaz.** Yerelden `DATABASE_URL=$DATABASE_URL_DIRECT python manage.py migrate` ile çalıştırılır. Bunu `docs/DEPLOY.md`'ye yaz.
- Supabase Auth, RLS, Storage, Edge Functions **kullanılmıyor**. Supabase burada sadece yönetilen bir Postgres.

### 11.2 Vercel yapılandırması

**Önemli:** Vercel, Nisan 2026'dan beri Django'yu sıfır konfigürasyonla destekliyor. İnternette bulacağın eski rehberlerin çoğu (`api/index.py` sarmalayıcısı, `builds` + `routes` içeren `vercel.json`) **artık gereksiz ve yanlış**. O yolu izleme.

Nasıl çalışıyor:
- Vercel repoda `manage.py` dosyasını bulur, çalıştırır, `DJANGO_SETTINGS_MODULE` değerini okur ve giriş noktasını `WSGI_APPLICATION` ayarından çıkarır. Yani `config/settings.py` içinde `WSGI_APPLICATION = "config.wsgi.application"` satırının olması yeterlidir.
- `STATIC_ROOT` tanımlıysa `collectstatic` build sırasında **otomatik** çalışır ve dosyalar Vercel CDN'den servis edilir. Build script'inde `collectstatic` çağırma.
- Uygulama tek bir Vercel Function olur ve varsayılan olarak Fluid compute üzerinde çalışır.

`settings.py`'de gereken tek şey:
```python
WSGI_APPLICATION = "config.wsgi.application"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"
```

WhiteNoise'u yine de tutuyoruz: production'da statikleri CDN servis eder, WhiteNoise sadece `vercel dev` ile yerelde devreye girer. `ManifestStaticFilesStorage` ve WhiteNoise'un `CompressedManifestStaticFilesStorage` sınıfı desteklenen backend'ler arasında.

`vercel.json` sadece fonksiyon ayarı gerekirse yazılır:
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "functions": {
    "config/wsgi.py": { "maxDuration": 30 }
  }
}
```

Diğer notlar:
- `requirements.txt` repo **kökünde** olmalı ve sadece runtime bağımlılıklarını içermeli (Python'da otomatik tree-shaking yok, bundle'a her şey girer).
- Yerelde deploy ortamını denemek için `vercel dev`; env değişkenlerini çekmek için `vercel pull` (`.env.local` üretir, `.gitignore`'a ekle).
- Dosya sistemi salt okunur ve geçicidir. Hiçbir şeyi diske yazma (v1'de zaten kullanıcı yüklemesi yok).
- Session backend veritabanıdır (`django.contrib.sessions.backends.db`) — bellek cache'i instance'lar arasında paylaşılmaz.
- Deploy'da beklenmedik bir hata alırsan önce Vercel'in güncel Django dokümanına bak (`vercel.com/docs/frameworks/full-stack/django`); tahmin ederek `vercel.json` doldurmaya çalışma.

---

## 12. Güvenlik ve Gizlilik Kontrol Listesi

- [ ] `SECRET_KEY` ve DB parolası sadece env'de; repoda asla.
- [ ] `DEBUG=False` production'da.
- [ ] Tüm POST'larda CSRF token; `fetch` isteklerinde `X-CSRFToken` header'ı.
- [ ] Kullanıcı içeriği template'te asla `|safe` ile render edilmiyor.
- [ ] E-posta hiçbir template, JSON veya log satırında geçmiyor.
- [ ] Ham IP adresi saklanmıyor.
- [ ] `public_id` tahmin edilemez (sıralı id URL'de yok).
- [ ] Yetki kontrolleri view seviyesinde: kapatma/silme sadece `poll.author == request.user`.
- [ ] Parola doğrulayıcıları aktif.
- [ ] `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT` production'da açık.
- [ ] Admin paneline production'da güçlü parolayla erişiliyor.

---

## 13. Claude Code için Çalışma Kuralları

1. **Fazları sırayla uygula.** "Faz 3'ü yap" dendiğinde Faz 4'ün işine başlama.
2. **Yeni bağımlılık ekleme.** Bölüm 2'deki liste dışında bir paket gerekiyorsa önce sor ve gerekçesini yaz.
3. **Framework ekleme.** React, Tailwind, Bootstrap, htmx, jQuery yok. Vanilla JS ve el yazımı CSS.
4. Kod içindeki isimler İngilizce, kullanıcıya görünen metinler Türkçe.
5. Yorum satırlarını az kullan; sadece "neden" açıklaması gerektiğinde.
6. Her fazın sonunda: değişiklikleri özetle, kabul kriterlerini tek tek işaretle, `git commit` öner (`feat: faz 3 — anket oluşturma ve akış`).
7. Bir şeyi çözemiyorsan tahmin ederek üst üste denemeler yapma; ne denediğini ve nerede takıldığını yaz.
8. Bir kararın bu dosyayla çeliştiğini düşünüyorsan uygulamadan önce söyle.
9. Migration dosyalarını elle düzenleme; model değiştirip `makemigrations` çalıştır.
10. Şablon içinde iş mantığı yazma (`services.py` / `selectors.py`).

---

## 14. Sonraki Sürüm Fikirleri (şimdi yapma)

Anket kategorileri, "benzer anketler", oy değiştirme hakkı, süreli anketler için geri sayım, kullanıcı istatistikleri ("verdiğin oyların %60'ı kazanan tarafta"), günün anketi, e-posta doğrulama, parola sıfırlama, PWA, gerçek zamanlı sonuç güncellemesi.
