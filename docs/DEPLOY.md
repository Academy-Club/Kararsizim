# Deployment (Vercel + Supabase)

Bu proje Vercel'e sıfır konfigürasyonla deploy edilir (bkz. `docs/PROJECT.md` Bölüm 11.2). `api/index.py` sarmalayıcısı veya `builds`/`routes` içeren eski tarz `vercel.json` yazılmaz.

## İlk kurulum

1. Vercel projesi GitHub reposuna (`Academy-Club/Kararsizim`, branch `main`) bağlanır.
2. Vercel proje ayarlarında (Settings → Environment Variables) aşağıdaki değişkenler **Production** ortamı için girilir. Değerleri yerel `.env` dosyandan kopyala:

   | Değişken | Not |
   |---|---|
   | `DJANGO_SECRET_KEY` | Production için ayrı, rastgele bir değer kullan — yereldekiyle aynı olmasın. |
   | `DJANGO_DEBUG` | `False` |
   | `DJANGO_ALLOWED_HOSTS` | `.vercel.app` (proje kendi custom domain'ini alırsa o da eklenir) |
   | `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://<proje>.vercel.app` |
   | `VOTER_KEY_SALT` | Production için ayrı, rastgele bir değer kullan — yereldekiyle aynı olmasın. |
   | `DATABASE_URL` | Supabase **Transaction pooler**, port **6543** |

   `DATABASE_URL_DIRECT` Vercel'e girilmez — sadece migration'lar için yerelden kullanılır (aşağıya bakın).

3. İlk production deploy tetiklenir.

## Migration'lar

Migration'lar Vercel build'inde **çalışmaz** (Transaction pooler migration'ı desteklemez, dosya sistemi salt okunur). Her zaman yerelden, **Session pooler (5432)** ile:

```bash
source .venv/bin/activate
DATABASE_URL=$DATABASE_URL_DIRECT python manage.py migrate
```

Model değiştiren her deploy öncesi bu komut çalıştırılmalı.

## Ortam değişkeni değişikliği sonrası

Vercel dashboard'da bir environment variable değiştirildiğinde önceki deployment'lar eski değeri kullanmaya devam eder — yeni değerin etkili olması için **redeploy** gerekir.

## Sorun giderme

- **Soğuk başlangıçta 500:** `DATABASE_URL` yanlış pooler'a (doğrudan bağlantı `db.<ref>.supabase.co:5432`) işaret ediyor olabilir — bu adres IPv6 üzerinden erişilir, Vercel'den bağlanılamaz. Transaction pooler'a çevir.
- **CSRF hatası:** `DJANGO_CSRF_TRUSTED_ORIGINS` gerçek deployment URL'iyle birebir eşleşmeli (şema dahil, `https://`).
- **Statik dosyalar 404:** `STATIC_ROOT` tanımlı olduğu sürece Vercel `collectstatic`'i otomatik çalıştırır; build loglarını kontrol et.
- Beklenmedik bir hata: Vercel'in güncel Django dokümanına bak (`vercel.com/docs/frameworks/full-stack/django`), tahmin ederek `vercel.json` doldurmaya çalışma.
