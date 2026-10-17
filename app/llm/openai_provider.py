import json
import logging

from openai import AsyncOpenAI, APIConnectionError, APIStatusError, RateLimitError, AuthenticationError
from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import LlmAuthenticationError, LlmInvalidResponseError, LlmProviderError, LlmRateLimitError
from .base import (
    ILlmProvider,
    CategoryItem,
    CategorizationResult,
    PriorityResult,
    SimilarityCandidate,
    SimilarityResult,
)
from .observability import observe_llm_call, set_token_usage
from .retry import wait_before_retry

logger = logging.getLogger(__name__)

CATEGORIZATION_SYSTEM_PROMPT = (
    "Sen bir kentsel sorun yönetim platformu için çalışan bir AI asistanısın. "
    "Görevin, vatandaşların bildirdiği sorunları verilen kategoriler arasından en uygun olanına atamak. "
    "Yanıtını her zaman geçerli JSON formatında ver."
)

PRIORITY_SYSTEM_PROMPT = (
    "Sen bir kentsel sorun yönetim platformu için önceliklendirme yapan bir AI asistanısın. "
    "Görevin, vatandaşların bildirdiği sorunların öncelik skorunu belirlemek. "
    "Yanıtını her zaman geçerli JSON formatında ver."
)

SIMILARITY_SYSTEM_PROMPT = (
    "Sen kentsel sorun raporlarinda anlamsal benzerlik tespiti yapan bir AI asistanisin. "
    "Yalnizca verilen aday raporlari degerlendir ve yanitini gecerli JSON olarak ver."
)

PRIORITY_SCALE = """
Öncelik belirleme kriterleri (en belirleyiciden az belirleyiciye):

1. KATEGORİ ACİLİYETİ (en belirleyici faktör):
   - Urgent başlangıç: su kesintisi, gaz sızıntısı, elektrik arızası, altyapı çöküşü, sel/taşkın
   - High başlangıç: trafik ışığı arızası, köprü/yol hasarı, yangın riski
   - Medium başlangıç: aydınlatma sorunu, park hasarı, kaldırım bozukluğu
   - Low başlangıç: estetik sorun, gürültü şikayeti, çevre kirliliği

2. BENZER RAPOR SAYISI (yaygınlık):
   - 5+ benzer → skoru 0.10 artır
   - 2-4 benzer → skoru 0.05 artır

3. AÇIK KALMA SÜRESİ (gecikme cezası):
   - 14+ gün → skoru 0.10 artır
   - 7-13 gün → skoru 0.05 artır

Öncelik seviyeleri:
- Urgent (0.76-1.0): Anında müdahale gerektirir, can/mal güvenliği tehlikede
- High (0.51-0.75): Hızlı çözüm gerekli, çok sayıda vatandaş etkileniyor
- Medium (0.26-0.50): Planlı çözüm yeterli, günlük yaşamı etkiliyor
- Low (0.0-0.25): Aciliyeti yok, estetik veya küçük konfor sorunu
"""


class OpenAIProvider(ILlmProvider):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        provider_name: str = "openai",
        request_options: dict | None = None,
    ) -> None:
        self.client = AsyncOpenAI(
            api_key=api_key or settings.OPENAI_API_KEY,
            base_url=base_url,
            timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS,
            max_retries=0,
        )
        self.model = model or settings.OPENAI_MODEL
        self.provider_name = provider_name
        self.request_options = request_options or {}

    @observe_llm_call(None, "categorization")
    async def categorize_report(
        self,
        title: str,
        description: str,
        categories: list[CategoryItem],
    ) -> CategorizationResult:
        categories_text = "\n".join(
            f"- ID: {c.id}, Ad: {c.name}"
            + (f", Açıklama: {c.description}" if c.description else "")
            for c in categories
        )

        user_prompt = (
            "Aşağıdaki şikayeti en uygun kategoriye ata.\n\n"
            f"Şikayet Başlığı: {title}\n"
            f"Şikayet Açıklaması: {description}\n\n"
            f"Mevcut kategoriler:\n{categories_text}\n\n"
            "Yanıtını şu JSON formatında ver (suggested_category_id verilen kategorilerden birinin ID'si olmalı):\n"
            "{\n"
            '  "suggested_category_id": "<kategori id>",\n'
            '  "suggested_category_name": "<kategori adı>",\n'
            '  "confidence": <0.0 ile 1.0 arası güven skoru>,\n'
            '  "reasoning": "<Türkçe, neden bu kategori seçildi, 1 cümle>"\n'
            "}"
        )

        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": CATEGORIZATION_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                    **self.request_options,
                )
                if response.usage is not None:
                    set_token_usage(
                        response.usage.prompt_tokens,
                        response.usage.completion_tokens,
                        response.usage.total_tokens,
                    )
                data = json.loads(response.choices[0].message.content)
                return CategorizationResult(**data)
            except (json.JSONDecodeError, ValidationError, KeyError, TypeError, IndexError) as e:
                raise LlmInvalidResponseError(
                    f"{self.provider_name} geçerli JSON döndüremedi"
                ) from e
            except RateLimitError as e:
                if attempt == settings.LLM_MAX_RETRIES:
                    raise LlmRateLimitError(
                        f"{self.provider_name} rate limit aşıldı"
                    ) from e
                await wait_before_retry(attempt)
            except AuthenticationError as e:
                raise LlmAuthenticationError(
                    f"{self.provider_name} API anahtarı geçersiz"
                ) from e
            except APIConnectionError as e:
                if attempt == settings.LLM_MAX_RETRIES:
                    raise LlmProviderError(
                        f"{self.provider_name} servisine bağlanılamadı"
                    ) from e
                await wait_before_retry(attempt)
            except APIStatusError as e:
                if e.status_code < 500 or attempt == settings.LLM_MAX_RETRIES:
                    raise LlmProviderError(
                        f"{self.provider_name} API hatası: HTTP {e.status_code}"
                    ) from e
                await wait_before_retry(attempt)

    @observe_llm_call(None, "similarity_detection")
    async def find_similar_reports(
        self,
        title: str,
        description: str,
        existing_reports: list[SimilarityCandidate],
    ) -> SimilarityResult:
        candidates = "\n".join(
            f"- ID: {report.id}\n  Baslik: {report.title}\n"
            f"  Aciklama: {report.description}\n  Tarih: {report.created_at.isoformat()}"
            for report in existing_reports
        )
        user_prompt = (
            f"Yeni rapor basligi: {title}\n"
            f"Yeni rapor aciklamasi: {description}\n\n"
            f"Aday raporlar:\n{candidates}\n\n"
            "Ayni fiziksel sorunu veya ayni olayi anlatan adaylari bul. "
            "Konu benzerligi tek basina yeterli degildir. "
            "Yalnizca verilen ID'leri kullan ve en fazla 10 sonuc dondur.\n"
            '{"similar_reports":[{"report_id":"<aday id>",'
            '"similarity_score":<0.0-1.0>,"reasoning":"<kisa Turkce gerekce>"}]}'
        )

        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SIMILARITY_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                    **self.request_options,
                )
                if response.usage is not None:
                    set_token_usage(
                        response.usage.prompt_tokens,
                        response.usage.completion_tokens,
                        response.usage.total_tokens,
                    )
                return SimilarityResult(
                    **json.loads(response.choices[0].message.content)
                )
            except (json.JSONDecodeError, ValidationError, KeyError, TypeError, IndexError) as e:
                raise LlmInvalidResponseError(
                    f"{self.provider_name} geçerli benzerlik JSON'u döndüremedi"
                ) from e
            except RateLimitError as e:
                if attempt == settings.LLM_MAX_RETRIES:
                    raise LlmRateLimitError(
                        f"{self.provider_name} rate limit aşıldı"
                    ) from e
                await wait_before_retry(attempt)
            except AuthenticationError as e:
                raise LlmAuthenticationError(
                    f"{self.provider_name} API anahtarı geçersiz"
                ) from e
            except APIConnectionError as e:
                if attempt == settings.LLM_MAX_RETRIES:
                    raise LlmProviderError(
                        f"{self.provider_name} servisine bağlanılamadı"
                    ) from e
                await wait_before_retry(attempt)
            except APIStatusError as e:
                if e.status_code < 500 or attempt == settings.LLM_MAX_RETRIES:
                    raise LlmProviderError(
                        f"{self.provider_name} API hatası: HTTP {e.status_code}"
                    ) from e
                await wait_before_retry(attempt)

    @observe_llm_call(None, "priority_scoring")
    async def score_priority(
        self,
        title: str,
        description: str,
        category_name: str,
        similar_report_count: int,
        days_open: int,
    ) -> PriorityResult:
        user_prompt = (
            f"Şikayet Başlığı: {title}\n"
            f"Şikayet Açıklaması: {description}\n"
            f"Kategori: {category_name}\n"
            f"Benzer Rapor Sayısı: {similar_report_count}\n"
            f"Açık Kaldığı Gün: {days_open}\n\n"
            f"{PRIORITY_SCALE}\n"
            "Yukarıdaki kriterlere göre bu şikayetin öncelik skorunu hesapla.\n"
            "Yanıtını şu JSON formatında ver (suggested_priority tam olarak Low, Medium, High veya Urgent olmalı):\n"
            "{\n"
            '  "priority_score": <0.0 ile 1.0 arası ondalıklı sayı>,\n'
            '  "suggested_priority": "<Low|Medium|High|Urgent>",\n'
            '  "reasoning": "<Türkçe, 1-2 cümle, hangi faktörlerin skoru nasıl etkilediğini açıkla>"\n'
            "}"
        )

        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": PRIORITY_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                    **self.request_options,
                )
                if response.usage is not None:
                    set_token_usage(
                        response.usage.prompt_tokens,
                        response.usage.completion_tokens,
                        response.usage.total_tokens,
                    )
                data = json.loads(response.choices[0].message.content)
                return PriorityResult(**data)
            except (json.JSONDecodeError, ValidationError, KeyError, TypeError, IndexError) as e:
                raise LlmInvalidResponseError(
                    f"{self.provider_name} geçerli JSON döndüremedi"
                ) from e
            except RateLimitError as e:
                if attempt == settings.LLM_MAX_RETRIES:
                    raise LlmRateLimitError(
                        f"{self.provider_name} rate limit aşıldı"
                    ) from e
                await wait_before_retry(attempt)
            except AuthenticationError as e:
                raise LlmAuthenticationError(
                    f"{self.provider_name} API anahtarı geçersiz"
                ) from e
            except APIConnectionError as e:
                if attempt == settings.LLM_MAX_RETRIES:
                    raise LlmProviderError(
                        f"{self.provider_name} servisine bağlanılamadı"
                    ) from e
                await wait_before_retry(attempt)
            except APIStatusError as e:
                if e.status_code < 500 or attempt == settings.LLM_MAX_RETRIES:
                    raise LlmProviderError(
                        f"{self.provider_name} API hatası: HTTP {e.status_code}"
                    ) from e
                await wait_before_retry(attempt)
