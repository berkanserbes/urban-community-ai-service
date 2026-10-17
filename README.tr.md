# Urban Community — Yapay Zekâ Servisi

![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[English](README.md) | **Türkçe**

Kentsel sorunların bildirilmesi ve çözülmesi için yapay zekâ destekli bir platform olan Urban
Community'de rapor kategorilendirme, öncelik puanlama ve benzer rapor tespiti yapan FastAPI servisi.
LLM sağlayıcısı olarak OpenAI, Gemini ve DeepSeek desteklenir.

## Repolar

| Repo | Açıklama |
| --- | --- |
| [urban-community-backend](https://github.com/berkanserbes/urban-community-backend) | ASP.NET Core API, RabbitMQ consumer'ları, PostgreSQL/PostGIS |
| **[urban-community-ai-service](https://github.com/berkanserbes/urban-community-ai-service)** | Kategorilendirme, önceliklendirme ve benzer rapor tespiti için FastAPI servisi (bu repo) |
| [urban-community-management-web](https://github.com/berkanserbes/urban-community-management-web) | React admin ve yetkili paneli |
| [urban-community-mobile](https://github.com/berkanserbes/urban-community-mobile) | Expo / React Native vatandaş uygulaması |

Genel mimari için [backend README](https://github.com/berkanserbes/urban-community-backend/blob/main/README.tr.md)
dosyasına bakın.

## Lokal Çalıştırma

Python 3.12 gerekir. Bir sanal ortam oluşturun ve production bağımlılıklarını kurun:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

`.env.example` dosyasını `.env` (veya `.env.development`) olarak kopyalayın, sağlayıcıyı seçin,
`AI_API_KEY` değerini ve seçilen sağlayıcının API anahtarını girin. Lokal ortam dosyaları gizli bilgi
içerir ve commit edilmemelidir.

Ardından çalıştırın:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Seçilen sağlayıcının API anahtarı zorunludur. Eksikse servis açılışta hemen hata verir.

## Docker ile Çalıştırma

Yapay zekâ servisi `backend/src/docker/docker-compose.yaml` içinde yer alır. Gizli bilgileri Docker
Compose'un kullandığı ortamda tanımlayın:

```text
AI_API_KEY=<backend-ile-ai-arasındaki-dahili-anahtar>
OPENAI_API_KEY=<sağlayıcı-anahtarı>
GEMINI_API_KEY=<seçildiyse-sağlayıcı-anahtarı>
DEEPSEEK_API_KEY=<seçildiyse-sağlayıcı-anahtarı>
```

Bu repoyu backend reposunun yanına (`ai/` ve `backend/` olarak) klonlayın ve servisleri ikisinin üst
klasöründen başlatın:

```bash
docker compose -f backend/src/docker/docker-compose.yaml --env-file backend/src/UrbanCommunity.Api/.env.development up --build
```

Container root olmayan bir kullanıcıyla çalışır. Docker Compose `GET /health/ready` adresini kontrol
eder ve açılış tamamlanmadıysa servisi sağlıksız (unhealthy) olarak işaretler.

## Yapılandırma

| Değişken | Amaç | Varsayılan |
|---|---|---|
| `LLM_PROVIDER` | Seçilen sağlayıcı: `openai`, `gemini` veya `deepseek` | `openai` |
| `AI_API_KEY` | Zorunlu dahili API kimlik doğrulama anahtarı | Yok |
| `OPENAI_API_KEY` | OpenAI sağlayıcı anahtarı | Boş |
| `OPENAI_MODEL` | OpenAI modeli | `gpt-4o-mini` |
| `GEMINI_API_KEY` | Gemini sağlayıcı anahtarı | Boş |
| `GEMINI_MODEL` | Gemini modeli | `gemini-1.5-flash` |
| `DEEPSEEK_API_KEY` | DeepSeek sağlayıcı anahtarı | Boş |
| `DEEPSEEK_MODEL` | DeepSeek modeli | `deepseek-v4-flash` |
| `DEEPSEEK_BASE_URL` | DeepSeek'in OpenAI uyumlu API adresi | `https://api.deepseek.com` |
| `LLM_REQUEST_TIMEOUT_SECONDS` | Sağlayıcı isteği zaman aşımı | `30` |
| `LLM_MAX_OUTPUT_TOKENS` | Üretilecek en fazla token sayısı | `500` |
| `LLM_MAX_RETRIES` | Sağlayıcı düzeyinde geçici hata yeniden deneme sayısı | `2` |
| `LLM_RETRY_BASE_DELAY_SECONDS` | İlk yeniden deneme gecikmesi | `0.5` |

DeepSeek yapılandırması:

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=<api-anahtarınız>
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

Bu kısa, yapılandırılmış JSON görevlerinde gecikmeyi ve token kullanımını azaltmak için DeepSeek
"thinking" kapalı modda çalışır.

Production yapılandırması için şablon olarak `.env.production.example` dosyasını kullanın. Gizli
bilgiler dağıtım ortamı tarafından sağlanmalı ve commit edilmemelidir.

## API Kimlik Doğrulama

Tüm `/api/*` endpoint'leri dahili API anahtarını ister:

```http
X-Api-Key: <AI_API_KEY>
```

Health endpoint'leri kimlik doğrulama gerektirmez:

- `GET /health/live`: sürecin ayakta olup olmadığı
- `GET /health/ready`: sağlayıcının ve özellik servislerinin hazır olup olmadığı

## Endpoint Örnekleri

Kategorilendirme:

```http
POST /api/categorization/suggest
X-Api-Key: <AI_API_KEY>
Content-Type: application/json
```

```json
{
  "title": "Mahalle girişinde sokak lambası çalışmıyor",
  "description": "Üç gündür yol tamamen karanlık ve yayalar için tehlike oluşturuyor.",
  "categories": [
    {
      "id": "018f6f64-5f47-7e37-b7dc-2f9bc8f69d42",
      "name": "Aydınlatma ve Elektrik",
      "description": "Sokak lambaları ve elektrik altyapısı sorunları"
    }
  ]
}
```

Öncelik puanlama:

```http
POST /api/priority/score
X-Api-Key: <AI_API_KEY>
Content-Type: application/json
```

```json
{
  "title": "Ana caddede büyük su kaçağı",
  "description": "Yola yoğun miktarda su akıyor ve trafik güvenliğini etkiliyor.",
  "category_name": "Su ve Kanalizasyon",
  "similar_report_count": 0,
  "days_open": 0
}
```

Benzer rapor tespiti:

```http
POST /api/similarity/find
X-Api-Key: <AI_API_KEY>
Content-Type: application/json
```

İstek bir yeni rapor ve önceden filtrelenmiş en fazla 20 aday rapor içerir. Yanıt yalnızca bu aday
listesindeki id'leri `0.0` ile `1.0` arasında puanlayarak sıralar.

## Testler

Bir sanal ortam oluşturup etkinleştirin, geliştirme bağımlılıklarını kurun ve çalıştırın:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Testler sahte (mock) sağlayıcılar kullanır; OpenAI, Gemini veya DeepSeek'e istek atmaz.

## Backend ile Entegrasyon Akışı

1. Backend yeni veya güncellenen raporu `AiReview` durumu ve `Medium` önceliğiyle kaydeder.
2. Backend, RabbitMQ üzerinden `ReportAiReviewRequestedEvent` yayınlar.
3. `ReportAiReviewRequestedConsumer`, yapay zekâ servisinden kategori önerisi ister.
4. Consumer aynı mahalleden, son 30 güne ait en fazla 20 açık raporu seçer.
5. Birebir aynı içerikler yerelde hash ile eşleştirilir; kalan adaylar benzerlik endpoint'iyle sıralanır.
6. En az `0.75` puan alan eşleşmeler kaydedilir; rapor başına en fazla beş eşleşme tutulur.
7. Kabul edilen eşleşme sayısı öncelik puanlamasına dahil edilir.
8. Geçerli bir yapay zekâ önceliği `Low`, `Medium`, `High` veya `Urgent` değerine eşlenir.
9. Kategori, benzer rapor eşleşmeleri, öncelik ve `PendingReview` durumu birlikte kaydedilir.
10. Rapor `AiReview` durumundan çıktıktan sonra tekrar teslim edilen mesajlar yok sayılır; böylece aynı
    rapor iki kez işlenmez.

Raporu oluşturan veya güncelleyen API isteği yapay zekâ işlemlerini beklemez.

## Güvenilirlik

- Seçilen OpenAI, Gemini veya DeepSeek sağlayıcısı FastAPI açılışında bir kez oluşturulur.
- Seçilen sağlayıcının API anahtarı eksikse açılış hemen başarısız olur.
- Sağlayıcı çağrılarının açık bir zaman aşımı ve en fazla çıktı token sınırı vardır.
- Rate limit, bağlantı hatası, zaman aşımı ve sağlayıcı tarafı sunucu hatalarında sınırlı, rastgele
  sapmalı (jitter) üstel geri çekilmeyle yeniden denenir.
- Kimlik doğrulama hataları ve geçersiz LLM yanıtları yeniden denenmez.
- Düşük güvenli kategorilendirme geçerli bir yanıttır. Backend bunu servis hatası saymaz; kullanıcının
  seçtiği veya varsayılan kategoriyi korur.
- Backend geçici yapay zekâ hatalarını MassTransit ile 2, 5 ve 10 saniye sonra yeniden dener.
- Denemeler tükenince MassTransit başarısız mesajı consumer'ın `_error` kuyruğunda tutar.
- Bir fault consumer raporların `AiReview` durumunda kalmasını önler; raporu mevcut kategori, `Medium`
  öncelik ve `PendingReview` durumuyla tamamlar.

## Gözlemlenebilirlik

Servis standart çıktıya JSON formatında log yazar.

Her HTTP isteği şunları içerir:

- Korelasyon id'si
- Metot ve yol
- Durum kodu
- Süre

Her LLM çağrısı şunları içerir:

- Sağlayıcı ve model
- İşlem adı
- Sonuç ve süre
- Sağlayıcı bildiriyorsa girdi, çıktı ve toplam token kullanımı

Backend her yapay zekâ isteğinde `X-Correlation-ID` başlığını gönderir; servis aynı başlığı geri
döner. Prompt'lar, rapor metinleri, API anahtarları ve üretilen gerekçeler loglara yazılmaz.

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
