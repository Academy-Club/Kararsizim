# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Bu projenin tam şartnamesi [docs/PROJECT.md](docs/PROJECT.md) dosyasındadır. **Her görevden önce oku.** Fazlar (Bölüm 8) sırayla uygulanır, faz atlanmaz — "Faz 3'ü yap" dendiğinde Faz 4'ün işine başlanmaz.

**Sürüm notu (2026-08-15 itibarıyla onaylandı):** Şartnamedeki Python 3.12 / Django 5.1.* pinleri artık güncel değil (5.1 EOL, yerelde 3.12 kurulu değil). Kullanıcı onayıyla **Python 3.14** ve **Django 6.1.x** kullanılıyor. `docs/PROJECT.md` Bölüm 2 ve `requirements.txt` bu şekilde güncellendi; dokümanın başka yerlerinde geçen 3.12/5.1 referansları güncel araç zincirini yansıtmıyor.

## Commands

```bash
source .venv/bin/activate         # sanal ortamı etkinleştir (Python 3.14)
python manage.py runserver        # yerel sunucu — http://127.0.0.1:8000
python manage.py test             # tüm testler (Django'nun kendi test runner'ı — ayrı framework yok)
python manage.py test polls       # tek app'in testleri
python manage.py test polls.tests.PollVoteTests.test_anonymous_vote_succeeds  # tek test
python manage.py makemigrations   # model değişikliğinden sonra
python manage.py migrate          # yerelden çalıştırılır (bkz. Supabase bağlantı notları aşağıda)
python manage.py seed_demo        # demo veri (Faz 1'de eklenecek yönetim komutu)
python manage.py check            # sistem kontrolü, hızlı sağlık testi
```

Henüz ayrı bir lint/format aracı kurulu değil; şartname yeni bağımlılık eklenmeden önce sormayı zorunlu kılıyor (aşağıya bakın).

## Mimari

Tek bir Django süreci hem sunucu taraflı HTML render ediyor hem de küçük JSON uçları veriyor. DRF, Celery, Redis, Docker, React/Vue/Tailwind/Bootstrap/htmx/jQuery **kullanılmıyor** — vanilla JS ve el yazımı CSS.

- `config/` — Django project (settings, urls, wsgi). `AUTH_USER_MODEL` ilk migration'dan **önce** `accounts.User`'a ayarlanmalı (Faz 1).
- `accounts/` — kullanıcı modeli, kayıt/giriş/çıkış.
- `polls/` — anket, seçenek, oy. Katmanlar ayrık tutulur:
  - `views.py` — ince, sadece istek/cevap akışı.
  - `services.py` — yazma iş mantığı (ör. `cast_vote`), `transaction.atomic()` + `F()` kullanır.
  - `selectors.py` — okuma sorguları (`select_related`/`prefetch_related` ile N+1 önlenir).
  - Template içinde sorgu tetikleyen kod yazılmaz.
- `templates/` — `base.html` + `partials/` (tekrar kullanılan parçalar) + app'e özel klasörler.
- `static/css/tokens.css` — tüm renk/aralık/tipografi değişkenleri burada tanımlı (Bölüm 7); şablon ve CSS'te ham hex kodu yazılmaz, sadece bu token'lar kullanılır.

### Veri modeli ve iş kuralları (özet — ayrıntı için Bölüm 4 ve 6)

- `Poll.public_id`: tahmin edilemez, `secrets.token_urlsafe` tabanlı — sıralı ID URL'de yok.
- `Vote`: kullanıcı ve anonim ziyaretçi için ayrı `UniqueConstraint` (`user` doluysa kullanıcı bazlı, boşsa `voter_key` bazlı — anonim oy oturumdan türetilen hash ile tekilleştirilir).
- Oy sayaçları (`Option.vote_count`, `Poll.total_votes`) denormalize tutulur, `F()` ile atomik artırılır.
- Oy vermeden önce yüzdeler gizlidir, sadece toplam oy sayısı görünür.
- Anket oluşturma **giriş gerektirir**, oy verme gerektirmez (anonim de oy kullanabilir).
- E-posta hiçbir template, JSON cevabı veya log satırında görünmez — sadece kullanıcı adı gösterilir.

### Veritabanı

- Yerelde `DATABASE_URL` boşsa `config/settings.py` otomatik SQLite'a düşer.
- Supabase'e bağlanırken **doğrudan bağlantı asla kullanılmaz** (`db.<ref>.supabase.co:5432` sadece IPv6, Vercel'den erişilemez). Uygulama için **Transaction pooler (6543)**, migration için **Session pooler (5432)** — ayrıntı Bölüm 11.1.
- Migration'lar Vercel build'inde çalışmaz; her zaman yerelden `DATABASE_URL=$DATABASE_URL_DIRECT python manage.py migrate` ile.

### Deployment

Vercel'e Django için sıfır konfigürasyonla deploy edilir (Nisan 2026'dan beri) — `api/index.py` sarmalayıcısı veya `builds`/`routes` içeren eski tarz `vercel.json` **yazılmaz**. Ayrıntı Bölüm 11.2.

## Kurallar

1. Yeni bağımlılık gerekiyorsa önce sor, gerekçesini yaz.
2. Kod içindeki isimler İngilizce, kullanıcıya görünen metinler Türkçe.
3. Migration dosyalarını elle düzenleme; model değiştirip `makemigrations` çalıştır.
4. Bir kararın `docs/PROJECT.md` ile çeliştiğini düşünüyorsan uygulamadan önce söyle.
5. Her fazın sonunda: değişiklikleri özetle, Kabul Kriterleri listesini tek tek işaretle, commit öner.
