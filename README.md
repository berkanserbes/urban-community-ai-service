# Urban Community — AI Service

![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**English** | [Türkçe](README.tr.md)

FastAPI service for report categorization, priority scoring, and duplicate detection in Urban
Community, an AI-assisted platform for reporting and resolving urban issues. It supports OpenAI,
Gemini, and DeepSeek as LLM providers.

## Repositories

| Repository | Description |
| --- | --- |
| [urban-community-backend](https://github.com/berkanserbes/urban-community-backend) | ASP.NET Core API, RabbitMQ consumers, PostgreSQL/PostGIS |
| **[urban-community-ai-service](https://github.com/berkanserbes/urban-community-ai-service)** | FastAPI service for categorization, priority scoring and duplicate detection (this repository) |
| [urban-community-management-web](https://github.com/berkanserbes/urban-community-management-web) | React admin and official panel |
| [urban-community-mobile](https://github.com/berkanserbes/urban-community-mobile) | Expo / React Native citizen app |

See the [backend README](https://github.com/berkanserbes/urban-community-backend#readme) for the overall
architecture.

## Local Startup

Requires Python 3.12. Create a virtual environment and install production dependencies:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` (or `.env.development`), select the provider,
set `AI_API_KEY`, and set the selected provider API key. Local environment
files contain secrets and must not be committed.

Then run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The selected provider API key is mandatory. Startup fails immediately when it
is missing.

## Docker Startup

The AI service is included in
`backend/src/docker/docker-compose.yaml`. Define secrets in the environment
used by Docker Compose:

```text
AI_API_KEY=<internal-backend-to-ai-key>
OPENAI_API_KEY=<provider-key>
GEMINI_API_KEY=<provider-key-if-selected>
DEEPSEEK_API_KEY=<provider-key-if-selected>
```

Clone this repository next to the backend repository (as `ai/` and `backend/`) and start the stack
from their parent folder:

```bash
docker compose -f backend/src/docker/docker-compose.yaml --env-file backend/src/UrbanCommunity.Api/.env.development up --build
```

The container runs as a non-root user. Docker Compose checks
`GET /health/ready` and marks the service unhealthy when startup has not
completed.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `LLM_PROVIDER` | Selected provider: `openai`, `gemini`, or `deepseek` | `openai` |
| `AI_API_KEY` | Required internal API authentication key | No default |
| `OPENAI_API_KEY` | OpenAI provider key | Empty |
| `OPENAI_MODEL` | OpenAI model | `gpt-4o-mini` |
| `GEMINI_API_KEY` | Gemini provider key | Empty |
| `GEMINI_MODEL` | Gemini model | `gemini-1.5-flash` |
| `DEEPSEEK_API_KEY` | DeepSeek provider key | Empty |
| `DEEPSEEK_MODEL` | DeepSeek model | `deepseek-v4-flash` |
| `DEEPSEEK_BASE_URL` | DeepSeek OpenAI-compatible API URL | `https://api.deepseek.com` |
| `LLM_REQUEST_TIMEOUT_SECONDS` | Provider request timeout | `30` |
| `LLM_MAX_OUTPUT_TOKENS` | Maximum generated tokens | `500` |
| `LLM_MAX_RETRIES` | Provider-level transient retries | `2` |
| `LLM_RETRY_BASE_DELAY_SECONDS` | Initial retry delay | `0.5` |

DeepSeek configuration:

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=<your-api-key>
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

DeepSeek runs in non-thinking mode for these short structured JSON tasks to
reduce latency and token usage.

Use `.env.production.example` as the production configuration template.
Secrets must be supplied by the deployment environment and must not be
committed.

## API Authentication

All `/api/*` endpoints require the internal API key:

```http
X-Api-Key: <AI_API_KEY>
```

Health endpoints do not require authentication:

- `GET /health/live`: process liveness
- `GET /health/ready`: provider and feature-service initialization

## Endpoint Examples

Categorization:

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

Priority scoring:

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

Similarity detection:

```http
POST /api/similarity/find
X-Api-Key: <AI_API_KEY>
Content-Type: application/json
```

The request contains one new report and at most 20 prefiltered candidate reports.
The response ranks only IDs from that candidate list with scores from `0.0` to `1.0`.

## Tests

Create and activate a virtual environment, install development dependencies, and run:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

The test suite uses mocked providers and does not call OpenAI, Gemini, or DeepSeek.

## Backend Integration Flow

1. The backend saves a new or updated report with `AiReview` status and `Medium` priority.
2. The backend publishes `ReportAiReviewRequestedEvent` through RabbitMQ.
3. `ReportAiReviewRequestedConsumer` requests category assignment from the AI service.
4. The consumer selects at most 20 open reports from the same neighborhood and the last 30 days.
5. Exact content hashes are matched locally; remaining candidates are ranked by the similarity endpoint.
6. Matches scoring at least `0.75` are persisted, with at most five matches per report.
7. The accepted match count is included in priority scoring.
8. A valid AI priority is mapped to `Low`, `Medium`, `High`, or `Urgent`.
9. Category, duplicate matches, priority, and `PendingReview` status are persisted together.
10. The consumer ignores redelivered messages after the report leaves `AiReview`, preventing duplicate processing.

The API request that creates or updates a report does not wait for either AI operation.

## Reliability

- The selected OpenAI, Gemini, or DeepSeek provider is created once during FastAPI startup.
- Startup fails immediately when the selected provider API key is missing.
- Provider calls have an explicit timeout and maximum output token limit.
- Rate limits, connection failures, timeouts, and server-side provider failures use bounded exponential backoff with jitter.
- Authentication failures and invalid LLM responses are not retried.
- Low-confidence categorization is a valid response. The backend keeps the user-selected or default category without treating it as a service failure.
- The backend retries transient AI failures through MassTransit after 2, 5, and 10 seconds.
- After retry exhaustion, MassTransit retains the failed message in the consumer `_error` queue.
- A fault consumer prevents reports from remaining in `AiReview`; it completes them with the current category, `Medium` priority, and `PendingReview` status.

## Observability

The service writes JSON logs to standard output.

Each HTTP request includes:

- Correlation ID
- Method and path
- Status code
- Duration

Each LLM call includes:

- Provider and model
- Operation name
- Outcome and duration
- Input, output, and total token usage when supplied by the provider

The backend sends `X-Correlation-ID` with every AI request. The AI service
returns the same header. Prompts, report text, API keys, and generated
reasoning are not written to logs.

## License

This project is licensed under the [MIT License](LICENSE).
