# Đề Xuất Kiến Trúc: External Data Layer cho StillMe

> **Mục tiêu**: Xây dựng lớp truy cập dữ liệu real-time từ các Public APIs (weather, news, finance, maps...) để giảm hallucination, tăng tính ứng dụng thực tế, nhưng vẫn giữ đúng triết lý minh bạch & chống black-box của StillMe.

**Ngày phân tích**: 2025-11-25  
**Trạng thái**: Phân tích & Đề xuất (chưa implement)

---

## 📋 Mục Lục

1. [Overview & Alignment với Triết Lý StillMe](#1-overview--alignment-với-triết-lý-stillme)
2. [Đề Xuất External Data Layer & Use Cases](#2-đề-xuất-external-data-layer--use-cases)
3. [Mapping với Kiến Trúc Hiện Tại](#3-mapping-với-kiến-trúc-hiện-tại)
4. [Đánh Giá Độ Khó & Rủi Ro](#4-đánh-giá-độ-khó--rủi-ro)
5. [Kế Hoạch Hành Động (Roadmap)](#5-kế-hoạch-hành-động-roadmap)

---

## 1. Overview & Alignment với Triết Lý StillMe

### 1.1. StillMe Đang Giải Quyết Vấn Đề Gì?

**Vấn đề cốt lõi:**
- **Black box AI systems**: ChatGPT/Claude không cho phép verify sources, không hiểu decision-making process
- **Hallucination tự tin**: AI bịa đáp án nhưng không có cách catch errors
- **Frozen in time**: Không học được thông tin mới sau training cutoff
- **Thiếu transparency**: Hidden algorithms, hidden data sources, hidden decision-making

**StillMe's Solution:**
- ✅ **100% Transparent**: Mọi source được cite, mọi decision visible, mọi code public
- ✅ **Validated Responses**: Multi-layer validation chain giảm hallucination qua citation, evidence overlap, confidence scoring
- ✅ **Continuously Learning**: Update knowledge mỗi 4 giờ từ trusted sources (RSS, arXiv, CrossRef, Wikipedia)
- ✅ **Intellectual Humility**: StillMe biết khi nào nó không biết và có can đảm thừa nhận

### 1.2. Triết Lý Cốt Lõi & Cách Thể Hiện Trong Code

**Core Principles:**

1. **Intellectual Humility** (`backend/identity/core.py`)
   - "I don't build an AI that knows everything. I build an AI that KNOWS IT DOESN'T KNOW"
   - Code: Confidence scoring, uncertainty detection, "I don't know" responses khi không có context

2. **Transparency** (mọi module)
   - Mọi source được cite với `[1]`, `[2]`
   - RAG context luôn visible trong response
   - Learning sources tracked trong `data/learning_metrics.jsonl`
   - Code: `backend/validators/citation.py`, `backend/vector_db/rag_retrieval.py`

3. **Anti-Hallucination** (`backend/validators/`)
   - 11 validators trong ValidatorChain:
     - CitationRequired, CitationRelevance
     - EvidenceOverlap (n-gram overlap check)
     - ConfidenceValidator (force uncertainty khi không có context)
     - FactualHallucinationValidator
     - SourceConsensusValidator (detect contradictions)
   - Code: `backend/validators/chain.py`, các validator modules

4. **Evidence-over-Authority** (`docs/CONSTITUTION.md`)
   - Evidence và citations luôn ưu tiên hơn personal opinions
   - Code: RAG retrieval luôn được ưu tiên, base LLM knowledge chỉ dùng khi không có RAG context

5. **Anti-Black-Box System** (không phải anti-black-box model)
   - StillMe chống **black box SYSTEM** (closed, proprietary, hidden algorithms)
   - Vẫn dùng LLM APIs (DeepSeek, OpenAI) như "reasoning engines" nhưng build **transparent SYSTEM** xung quanh
   - Code: Mọi data flow visible, mọi learning decision logged, mọi validation step transparent

### 1.3. Các Luồng Chính Hiện Tại

**Chat Pipeline:**
```
User Query 
  → Intent Detection (philosophical/factual) 
  → RAG Retrieval (ChromaDB semantic search) 
  → LLM Generation (DeepSeek/OpenAI với RAG context) 
  → Validator Chain (11 validators) 
  → Post-Processing (quality eval + rewrite) 
  → Response (với citations, confidence score, validation info)
```

**Auto-Learning Pipeline:**
```
Scheduler (every 4 hours)
  → Source Integration (RSS, arXiv, CrossRef, Wikipedia)
  → Pre-Filter (length, keyword scoring - giảm 30-50% embedding cost)
  → Content Curator (prioritize based on knowledge gaps)
  → Embedding (sentence-transformers)
  → ChromaDB Storage
```

**Guardrails:**
- Identity Check Validator: Prevent anthropomorphism
- Ego Neutrality Validator: Catch "Hallucination of Experience"
- Philosophical Processor: Explicitly state StillMe is AI system
- Style Sanitizer: Remove emotional language

### 1.4. Đánh Giá: External APIs Có Phù Hợp Với Triết Lý StillMe?

#### ✅ **PHÙ HỢP - Điểm Mạnh:**

1. **Minh Bạch Nguồn Dữ Liệu**
   - External APIs có **source rõ ràng**: "Data from OpenWeatherMap API", "News from GNews API"
   - **Timestamp visible**: "Data retrieved at 2025-11-25 13:30 UTC"
   - **Raw data accessible**: Có thể log raw JSON response để audit
   - **Phù hợp với triết lý transparency**: Vẫn giữ được "every source is cited, every decision is visible"

2. **Giảm Hallucination**
   - Thay vì LLM "bịa" thời tiết/tỷ giá/tin tức → dùng **real-time data từ API**
   - **Có thể verify**: User có thể check API response trực tiếp
   - **Phù hợp với anti-hallucination principle**: Dữ liệu thực tế thay vì "confident but wrong"

3. **Evidence-Based**
   - External APIs cung cấp **structured data** (JSON) thay vì text tự do
   - **Có thể fact-check**: So sánh với multiple sources nếu cần
   - **Phù hợp với evidence-over-authority**: Data từ API là evidence, không phải "authority" của model

4. **Intellectual Humility**
   - Khi API fail → StillMe có thể nói "I cannot access real-time weather data right now" thay vì bịa
   - **Phù hợp với "knowing when we don't know"**: API failure là một form của "not knowing"

#### ⚠️ **RỦI RO / XUNG ĐỘT:**

1. **Phụ Thuộc Nguồn Ngoài**
   - **Risk**: API down → StillMe không thể trả lời câu hỏi real-time
   - **Mitigation**: Cần fallback mechanism, caching, error handling rõ ràng
   - **Conflict level**: THẤP - vẫn phù hợp vì StillMe đã có fallback mechanisms cho RAG failures

2. **Rate Limits & Costs**
   - **Risk**: Free tier APIs có rate limits, paid APIs có cost
   - **Mitigation**: Caching, rate limit handling, cost tracking
   - **Conflict level**: THẤP - StillMe đã có cost optimization (pre-filter giảm 30-50% embedding cost)

3. **Bias Từ Nguồn Dữ Liệu**
   - **Risk**: News APIs có thể có bias (political, cultural)
   - **Mitigation**: 
     - **Transparency**: Luôn hiện source, không "đóng gói" như tri thức nội tại
     - **Multiple sources**: Dùng nhiều APIs cho cùng topic (vd: GNews + NewsAPI)
     - **User awareness**: Vẫn giữ nguyên triết lý "evidence-over-authority" - user tự quyết định
   - **Conflict level**: TRUNG BÌNH - cần guardrails nhưng không vi phạm triết lý

4. **Nguy Cơ Drifting Khỏi Triết Lý Minh Bạch**
   - **Risk**: Nếu "đóng gói" API data như tri thức nội tại của model → mất transparency
   - **Mitigation**: 
     - **Luôn hiện source**: "According to OpenWeatherMap API (retrieved at 2025-11-25 13:30 UTC)..."
     - **Raw data accessible**: Log raw JSON responses
     - **Không cache quá lâu**: Real-time data nên có TTL ngắn
   - **Conflict level**: CAO - cần thiết kế cẩn thận để không vi phạm transparency

5. **API Cũng Là "Black Box" (Một Phần)**
   - **Risk**: User không thể verify algorithm của OpenWeatherMap/GNews
   - **Mitigation**:
     - **Khác với LLM black box**: API trả về **structured data** (JSON), không phải generated text
     - **Có thể verify**: User có thể call API trực tiếp để verify
     - **Transparency về process**: StillMe log request/response, hiện timestamp, source
   - **Conflict level**: THẤP - vẫn phù hợp vì StillMe chống **black box SYSTEM**, không phải black box data source

### 1.5. Kết Luận Alignment

**✅ PHÙ HỢP với điều kiện:**

1. **External APIs được implement như một "transparent data source"**:
   - Luôn hiện source, timestamp, raw data accessible
   - Không "đóng gói" như tri thức nội tại
   - Logging đầy đủ cho audit trail

2. **Giữ nguyên triết lý "evidence-over-authority"**:
   - API data là **evidence**, không phải **authority**
   - User vẫn tự quyết định tin hay không
   - StillMe không claim "I know" mà claim "According to [API source]..."

3. **Intellectual humility vẫn được giữ**:
   - Khi API fail → "I cannot access real-time data"
   - Khi data outdated → "This data is from [timestamp], may not reflect current state"

**⚠️ CẦN CẨN THẬN:**
- Không để External APIs trở thành "black box" mới
- Luôn maintain transparency về source, timestamp, raw data
- Không cache quá lâu (real-time data cần freshness)

---

## 2. Đề Xuất External Data Layer & Use Cases

### 2.1. Khái Niệm / Lớp

**Tên đề xuất**: `ExternalDataProvider` / `RealWorldDataLayer`

**Lý do:**
- `ExternalDataProvider`: Rõ ràng về nguồn (external), phù hợp với pattern hiện tại (có `LLMProvider`)
- `RealWorldDataLayer`: Nhấn mạnh "real-world" data vs "learned" data trong RAG

**Đề xuất dùng**: `ExternalDataProvider` (ngắn gọn, rõ ràng)

### 2.2. Phân Tích Loại API Hợp Với StillMe

#### **Tiêu Chí Ưu Tiên:**

1. **Dữ liệu rõ nguồn, có thể trích dẫn** ⭐⭐⭐⭐⭐
2. **Free / có free tier** ⭐⭐⭐⭐
3. **Dễ tích hợp (REST, JSON)** ⭐⭐⭐⭐
4. **Structured data (không phải generated text)** ⭐⭐⭐⭐
5. **Rate limit hợp lý** ⭐⭐⭐

#### **Loại API Đề Xuất:**

**Phase 1 (MVP) - Đơn giản, high value:**

1. **Weather APIs** ⭐⭐⭐⭐⭐
   - **Open-Meteo** (free, no API key, open data)
     - Pros: Free, no key, open data, good coverage
     - Cons: Rate limit (10,000 requests/day), có thể chậm
   - **OpenWeatherMap** (free tier: 60 calls/min)
     - Pros: Popular, reliable, good docs
     - Cons: Cần API key, rate limit
   - **Use case**: "Hôm nay thời tiết ở Hà Nội như thế nào?"

2. **News APIs** ⭐⭐⭐⭐
   - **GNews API** (free tier: 100 requests/day)
     - Pros: Free tier tốt, dễ dùng, coverage tốt
     - Cons: Rate limit thấp
   - **NewsAPI** (free tier: 100 requests/day)
     - Pros: Popular, nhiều sources
     - Cons: Rate limit thấp, cần API key
   - **Use case**: "Tin tức AI nổi bật 24h qua?"

**Phase 2 - Medium complexity:**

3. **Finance / FX Rate APIs** ⭐⭐⭐⭐
   - **ExchangeRate-API** (free tier: 1,500 requests/month)
     - Pros: Free, no key, simple
     - Cons: Rate limit thấp
   - **Fixer.io** (free tier: 100 requests/month)
     - Pros: Reliable, good data
     - Cons: Rate limit rất thấp
   - **Use case**: "Tỷ giá USD → VND hiện tại?"

4. **Sports APIs** ⭐⭐⭐
   - **API-Football** (free tier: 100 requests/day)
     - Pros: Coverage tốt
     - Cons: Cần API key, rate limit
   - **Use case**: "Lịch thi đấu của đội Y tuần này?"

**Phase 3 - Advanced:**

5. **Maps / Location APIs** ⭐⭐⭐
   - **OpenStreetMap Nominatim** (free, no key)
     - Pros: Free, open data
     - Cons: Rate limit (1 request/second), có thể chậm
   - **Use case**: "Khoảng cách từ A đến B?"

6. **Open Data APIs** ⭐⭐⭐
   - **World Bank API** (free, no key)
     - Pros: Official data, reliable
     - Cons: Data có thể outdated
   - **Use case**: "GDP của Việt Nam năm 2023?"

### 2.3. Use Cases Cụ Thể

#### **Use Case 1: Weather Queries**

**Câu hỏi**: "Hôm nay thời tiết ở Hà Nội như thế nào?"

**API**: Open-Meteo (free, no key) hoặc OpenWeatherMap

**Level tích hợp**: **Direct API call, bypass RAG**

**Lý do:**
- Weather là **real-time data**, không nên lưu vào RAG (outdated nhanh)
- Câu hỏi rõ ràng về weather → detect intent → call API trực tiếp
- Response format:
  ```
  According to Open-Meteo API (retrieved at 2025-11-25 13:30 UTC):
  - Temperature: 25°C
  - Condition: Partly cloudy
  - Humidity: 65%
  
  [Source: Open-Meteo API | Timestamp: 2025-11-25T13:30:00Z]
  ```

**Implementation:**
- Intent detection: "weather", "thời tiết", "temperature", "nhiệt độ"
- Route to `ExternalDataProvider.fetch_weather(location)`
- Format response với source + timestamp
- Log request/response cho audit

#### **Use Case 2: News Queries**

**Câu hỏi**: "Tin tức AI nổi bật 24h qua?"

**API**: GNews API hoặc NewsAPI

**Level tích hợp**: **Direct API call, có thể cache 1-2 giờ**

**Lý do:**
- News là **time-sensitive**, nhưng không cần real-time từng giây
- Có thể cache 1-2 giờ để giảm API calls
- Response format:
  ```
  According to GNews API (retrieved at 2025-11-25 13:30 UTC):
  
  1. [Title] - [Source] - [Published time]
     [Summary]
  
  2. [Title] - [Source] - [Published time]
     [Summary]
  
  [Source: GNews API | Timestamp: 2025-11-25T13:30:00Z | Cached: No]
  ```

**Implementation:**
- Intent detection: "news", "tin tức", "latest", "mới nhất"
- Route to `ExternalDataProvider.fetch_news(query, max_results=5)`
- Cache với TTL 1-2 giờ
- Format response với source + timestamp + cache status

#### **Use Case 3: Finance / FX Rate Queries**

**Câu hỏi**: "Tỷ giá USD → VND hiện tại?"

**API**: ExchangeRate-API hoặc Fixer.io

**Level tích hợp**: **Direct API call, cache 5-10 phút**

**Lý do:**
- FX rates thay đổi real-time nhưng không cần update từng giây
- Cache 5-10 phút hợp lý
- Response format:
  ```
  According to ExchangeRate-API (retrieved at 2025-11-25 13:30 UTC):
  - 1 USD = 24,500 VND
  
  [Source: ExchangeRate-API | Timestamp: 2025-11-25T13:30:00Z | Cached: No]
  ```

**Implementation:**
- Intent detection: "exchange rate", "tỷ giá", "currency", "USD", "VND"
- Route to `ExternalDataProvider.fetch_exchange_rate(from_currency, to_currency)`
- Cache với TTL 5-10 phút
- Format response với source + timestamp

#### **Use Case 4: Sports Scores / Schedules**

**Câu hỏi**: "Lịch thi đấu của đội Y tuần này?"

**API**: API-Football hoặc tương tự

**Level tích hợp**: **Direct API call, cache 1 giờ**

**Lý do:**
- Sports data thay đổi theo schedule, không cần real-time từng giây
- Cache 1 giờ hợp lý
- Response format:
  ```
  According to API-Football (retrieved at 2025-11-25 13:30 UTC):
  
  Upcoming matches for [Team Y]:
  - [Date] [Time]: [Team Y] vs [Opponent]
  - [Date] [Time]: [Team Y] vs [Opponent]
  
  [Source: API-Football | Timestamp: 2025-11-25T13:30:00Z]
  ```

**Implementation:**
- Intent detection: "sports", "football", "schedule", "lịch thi đấu"
- Route to `ExternalDataProvider.fetch_sports_schedule(team, sport_type)`
- Cache với TTL 1 giờ
- Format response với source + timestamp

#### **Use Case 5: Fact-Checking với External APIs**

**Câu hỏi**: "GDP của Việt Nam năm 2023 là bao nhiêu?"

**Level tích hợp**: **Kết hợp RAG + External API**

**Lý do:**
- RAG có thể có data cũ → dùng External API để verify/update
- Có thể dùng như **validator** trong Validation Chain
- Response format:
  ```
  Based on RAG knowledge [1] and verified with World Bank API [2]:
  - GDP of Vietnam in 2023: [value] USD
  
  [1] Source from RAG: [citation]
  [2] Source: World Bank API | Timestamp: 2025-11-25T13:30:00Z
  ```

**Implementation:**
- Trong Validation Chain: `ExternalDataValidator`
- Khi detect numeric/statistical claim → check với External API nếu có
- So sánh RAG data vs API data → flag nếu khác biệt lớn

---

## 3. Mapping với Kiến Trúc Hiện Tại

### 3.1. Nên Gắn External APIs Vào Đâu Trong Pipeline?

**Đề xuất: 2 điểm tích hợp chính:**

#### **A. Pre-RAG Intent Detection (Bypass RAG cho real-time queries)**

**Vị trí**: Trước RAG retrieval, sau intent detection

**Flow:**
```
User Query
  → Intent Detection (philosophical/factual/real-time)
  → [NEW] External Data Intent Detection
    → Nếu là weather/news/fx/sports → Route to ExternalDataProvider
    → Bypass RAG, call API trực tiếp
    → Format response với source + timestamp
    → Return (skip RAG, skip LLM generation cho simple queries)
  → Nếu không phải external data query → Continue với RAG pipeline
```

**File cần sửa:**
- `backend/api/routers/chat_router.py` - Thêm intent detection cho external data
- `backend/core/question_classifier.py` - Mở rộng để detect external data queries

**Lợi ích:**
- Low latency (không cần RAG + LLM)
- Giảm cost (không cần LLM call cho simple queries)
- Real-time data chính xác

#### **B. Validation Chain (Dùng API như validator)**

**Vị trí**: Trong Validator Chain, sau EvidenceOverlap

**Flow:**
```
Response từ LLM
  → Validator Chain
    → CitationRequired
    → EvidenceOverlap
    → [NEW] ExternalDataValidator
      → Nếu response có numeric/statistical claims
      → Check với External API nếu có (World Bank, FX rates...)
      → Flag nếu khác biệt lớn với API data
    → ConfidenceValidator
    → ...
```

**File cần sửa:**
- `backend/validators/chain.py` - Thêm ExternalDataValidator
- `backend/validators/external_data.py` - [NEW] Validator mới

**Lợi ích:**
- Fact-checking với real-time data
- Phát hiện outdated data trong RAG
- Giữ nguyên pipeline hiện tại

### 3.2. Cụ Thể Hơn: Routing Logic

**Với câu hỏi "thời tiết / tỷ giá / lịch thi đấu / tin tức mới nhất":**

1. **Intent Detection** (`backend/core/question_classifier.py`)
   ```python
   def detect_external_data_intent(query: str) -> Optional[ExternalDataIntent]:
       # Detect: weather, news, fx_rate, sports, etc.
       # Return: ExternalDataIntent(type="weather", location="Hanoi")
   ```

2. **Route to ExternalDataProvider** (bypass RAG)
   ```python
   if external_data_intent:
       result = external_data_provider.fetch(external_data_intent)
       return format_response_with_source(result)
   else:
       # Continue với RAG pipeline
   ```

3. **Logging & Transparency**
   - Log request: `{"type": "weather", "location": "Hanoi", "timestamp": "..."}`
   - Log response: Raw JSON từ API
   - Include trong response: Source, timestamp, cache status

**Với câu hỏi cần fact-checking:**

1. **RAG Pipeline chạy bình thường**
2. **Trong Validation Chain**: `ExternalDataValidator` check numeric/statistical claims
3. **Nếu có khác biệt**: Flag trong validation_info, có thể retry với API data

### 3.3. Interface Python (High-Level)

```python
from typing import Protocol, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExternalDataResult:
    """Result from external API"""
    data: Dict[str, Any]  # Raw API response
    source: str  # API name (e.g., "Open-Meteo")
    timestamp: datetime  # When data was retrieved
    cached: bool  # Whether data was from cache
    cache_ttl: Optional[int]  # Cache TTL in seconds
    raw_response: Optional[str]  # Raw JSON for audit

@dataclass
class ExternalDataIntent:
    """Detected intent for external data query"""
    type: str  # "weather", "news", "fx_rate", "sports", etc.
    params: Dict[str, Any]  # Query parameters (location, currency pair, etc.)
    confidence: float  # Confidence score (0.0-1.0)

class ExternalDataProvider(Protocol):
    """Protocol for external data providers"""
    
    def supports(self, intent: ExternalDataIntent) -> bool:
        """Check if this provider supports the intent"""
        ...
    
    def fetch(self, intent: ExternalDataIntent) -> ExternalDataResult:
        """Fetch data from external API"""
        ...
    
    def get_cache_key(self, intent: ExternalDataIntent) -> str:
        """Generate cache key for this intent"""
        ...

class WeatherProvider(ExternalDataProvider):
    """Weather data provider (Open-Meteo, OpenWeatherMap)"""
    ...

class NewsProvider(ExternalDataProvider):
    """News data provider (GNews, NewsAPI)"""
    ...

class FXRateProvider(ExternalDataProvider):
    """Foreign exchange rate provider"""
    ...

class ExternalDataOrchestrator:
    """Orchestrates multiple external data providers"""
    
    def __init__(self):
        self.providers: List[ExternalDataProvider] = []
        self.cache: Optional[Cache] = None  # Redis or in-memory
    
    def register_provider(self, provider: ExternalDataProvider):
        """Register a provider"""
        ...
    
    def route(self, intent: ExternalDataIntent) -> Optional[ExternalDataResult]:
        """Route intent to appropriate provider"""
        # 1. Check cache first
        # 2. Find provider that supports intent
        # 3. Fetch from provider
        # 4. Cache result
        # 5. Return result
        ...
    
    def format_response(self, result: ExternalDataResult, query: str) -> str:
        """Format API result into StillMe response format"""
        # Include: source, timestamp, data, cache status
        ...
```

### 3.4. Chỗ Nào Trong Code Hiện Tại Sẽ Gọi ExternalDataOrchestrator?

**Option 1: Trong `chat_router.py` - Pre-RAG (Đề xuất)**

**File**: `backend/api/routers/chat_router.py`

**Vị trí**: Trong `chat_with_rag()` function, sau intent detection, trước RAG retrieval

**Code structure:**
```python
async def chat_with_rag(...):
    # ... existing code ...
    
    # Detect language
    detected_lang = detect_language(chat_request.message)
    
    # [NEW] Detect external data intent
    from backend.external_data.orchestrator import ExternalDataOrchestrator
    from backend.core.question_classifier import detect_external_data_intent
    
    external_data_intent = detect_external_data_intent(chat_request.message)
    if external_data_intent and external_data_intent.confidence > 0.7:
        # Route to external data provider
        orchestrator = ExternalDataOrchestrator()
        result = orchestrator.route(external_data_intent)
        
        if result:
            # Format response with source + timestamp
            response_text = orchestrator.format_response(result, chat_request.message)
            
            # Log for audit
            logger.info(f"External data used: {result.source}, cached: {result.cached}")
            
            return ChatResponse(
                response=response_text,
                confidence_score=0.9,  # High confidence for API data
                has_citation=True,
                validation_info={
                    "passed": True,
                    "external_data_source": result.source,
                    "external_data_timestamp": result.timestamp.isoformat(),
                    "external_data_cached": result.cached
                },
                processing_steps=["🌐 Fetched from external API", f"Source: {result.source}"]
            )
    
    # Continue with RAG pipeline if not external data query
    # ... existing RAG code ...
```

**Option 2: Trong Validation Chain**

**File**: `backend/validators/external_data.py` (NEW)

**Code structure:**
```python
class ExternalDataValidator(BaseValidator):
    """Validator that checks claims against external APIs"""
    
    def validate(self, response: str, context: Dict) -> ValidationResult:
        # Detect numeric/statistical claims
        claims = self._extract_claims(response)
        
        for claim in claims:
            if self._should_verify(claim):
                # Check with external API
                api_result = self._check_with_api(claim)
                if api_result and self._is_different(claim, api_result):
                    return ValidationResult(
                        passed=False,
                        reason=f"Claim differs from {api_result.source}",
                        external_data_source=api_result.source
                    )
        
        return ValidationResult(passed=True)
```

### 3.5. Files/Folders Cần Tạo/Sửa

**Files cần tạo (NEW):**

1. `backend/external_data/__init__.py`
2. `backend/external_data/orchestrator.py` - ExternalDataOrchestrator
3. `backend/external_data/providers/__init__.py`
4. `backend/external_data/providers/base.py` - Base provider class
5. `backend/external_data/providers/weather.py` - WeatherProvider
6. `backend/external_data/providers/news.py` - NewsProvider
7. `backend/external_data/providers/fx_rate.py` - FXRateProvider
8. `backend/external_data/providers/sports.py` - SportsProvider
9. `backend/external_data/cache.py` - Caching logic (Redis or in-memory)
10. `backend/external_data/intent_detector.py` - Detect external data intents
11. `backend/validators/external_data.py` - ExternalDataValidator (nếu dùng trong Validation Chain)

**Files cần sửa:**

1. `backend/api/routers/chat_router.py`
   - Thêm external data intent detection
   - Route to ExternalDataOrchestrator nếu detect
   - Format response với source + timestamp

2. `backend/core/question_classifier.py`
   - Mở rộng để detect external data queries
   - Thêm `detect_external_data_intent()` function

3. `backend/validators/chain.py` (nếu dùng Option 2)
   - Thêm ExternalDataValidator vào chain

4. `backend/api/utils/chat_helpers.py` (có thể)
   - Helper functions để format external data responses

**Folders structure:**
```
backend/
  external_data/
    __init__.py
    orchestrator.py
    intent_detector.py
    cache.py
    providers/
      __init__.py
      base.py
      weather.py
      news.py
      fx_rate.py
      sports.py
```

---

## 4. Đánh Giá Độ Khó & Rủi Ro

### 4.1. Độ Khó Kỹ Thuật

#### **Backend Complexity: TRUNG BÌNH**

**Các component cần implement:**

1. **Routing & Intent Detection** ⭐⭐⭐
   - **Độ khó**: Trung bình
   - **Lý do**: Cần detect chính xác khi nào dùng external API vs RAG
   - **Edge cases**: 
     - "Thời tiết ở đâu?" (không có location) → cần extract từ context
     - "Tin tức về AI" (generic) → có thể dùng RAG hoặc API
   - **Giải pháp**: Confidence threshold (0.7), fallback to RAG nếu confidence thấp

2. **Async & Error Handling** ⭐⭐⭐⭐
   - **Độ khó**: Trung bình-cao
   - **Lý do**: 
     - API calls có thể timeout, fail
     - Cần retry logic
     - Cần fallback khi API down
   - **Giải pháp**: 
     - Async HTTP client (httpx)
     - Retry với exponential backoff
     - Fallback to RAG nếu API fail

3. **Rate Limit Handling** ⭐⭐⭐
   - **Độ khó**: Trung bình
   - **Lý do**: Free tier APIs có rate limits
   - **Giải pháp**: 
     - Caching (giảm API calls)
     - Rate limit tracking (in-memory hoặc Redis)
     - Queue requests nếu rate limit

4. **Caching** ⭐⭐⭐
   - **Độ khó**: Trung bình
   - **Lý do**: Cần cache để giảm API calls, nhưng real-time data cần freshness
   - **Giải pháp**: 
     - Redis cache (nếu có) hoặc in-memory cache
     - TTL khác nhau cho từng loại data:
       - Weather: 10-15 phút
       - News: 1-2 giờ
       - FX rates: 5-10 phút
       - Sports: 1 giờ

5. **Logging & Audit Trail** ⭐⭐
   - **Độ khó**: Thấp-trung bình
   - **Lý do**: Cần log request/response cho transparency
   - **Giải pháp**: 
     - Structured logging (đã có sẵn)
     - Log raw JSON responses
     - Log cache hits/misses

#### **Tác Động Đến Performance: THẤP-TRUNG BÌNH**

**Latency:**
- **External API call**: +200-500ms (tùy API)
- **Với caching**: +0-50ms (cache hit)
- **So với RAG pipeline**: RAG mất 2-5s → External API nhanh hơn nếu cache hit

**Cost:**
- **API costs**: Free tier có giới hạn, paid tier có cost
- **Mitigation**: Caching giảm API calls đáng kể
- **So với LLM costs**: External API rẻ hơn nhiều so với LLM calls

**Scalability:**
- **Rate limits**: Cần monitoring và queue nếu cần
- **Caching**: Giảm load lên APIs
- **Concurrent requests**: Cần connection pooling

#### **Tác Động Đến Validation Chain & Logging: THẤP**

- **Validation Chain**: Không ảnh hưởng (external data bypass validation hoặc dùng như validator)
- **Logging**: Cần thêm logs cho external API calls (không ảnh hưởng logging hiện tại)

### 4.2. Độ Phù Hợp Với Triết Lý StillMe

#### **Điểm Mạnh:**

1. **Transparency** ⭐⭐⭐⭐⭐
   - External APIs có source rõ ràng
   - Timestamp visible
   - Raw data accessible
   - **Phù hợp 100%** với triết lý transparency

2. **Anti-Hallucination** ⭐⭐⭐⭐⭐
   - Real-time data thay vì "bịa"
   - Có thể verify
   - **Phù hợp 100%** với anti-hallucination principle

3. **Evidence-Based** ⭐⭐⭐⭐⭐
   - Structured data (JSON) thay vì generated text
   - Có thể fact-check
   - **Phù hợp 100%** với evidence-over-authority

#### **Điểm Nguy Hiểm:**

1. **API Cũng Là "Black Box" (Một Phần)** ⚠️
   - **Risk**: User không thể verify algorithm của API provider
   - **Mitigation**: 
     - API trả về **structured data** (JSON), không phải generated text → có thể verify
     - User có thể call API trực tiếp để verify
     - StillMe log raw responses → transparent về data
   - **Conflict level**: THẤP - vẫn phù hợp vì StillMe chống **black box SYSTEM**, không phải black box data source

2. **Nguy Cơ Drifting Khỏi Triết Lý Minh Bạch** ⚠️⚠️
   - **Risk**: Nếu "đóng gói" API data như tri thức nội tại → mất transparency
   - **Mitigation**: 
     - **Luôn hiện source**: "According to [API]..."
     - **Luôn hiện timestamp**: "retrieved at [timestamp]"
     - **Raw data accessible**: Log raw JSON
     - **Không cache quá lâu**: Real-time data cần freshness
   - **Conflict level**: CAO - cần thiết kế cẩn thận

3. **Phụ Thuộc Nguồn Ngoài** ⚠️
   - **Risk**: API down → StillMe không thể trả lời
   - **Mitigation**: 
     - Fallback to RAG nếu API fail
     - Caching để giảm dependency
     - Error handling rõ ràng
   - **Conflict level**: THẤP - vẫn phù hợp vì StillMe đã có fallback mechanisms

#### **Cần Bổ Sung Guardrails:**

1. **Source Attribution (Bắt buộc)**
   - Mọi response từ external API PHẢI có: `[Source: API_NAME | Timestamp: ISO]`
   - Không được "đóng gói" như tri thức nội tại

2. **Cache Transparency**
   - Hiện cache status: "Cached: Yes/No"
   - Hiện cache age: "Data age: 5 minutes"

3. **Error Transparency**
   - Khi API fail → "I cannot access [API] right now. [Error details]. Falling back to RAG..."
   - Không được "bịa" data khi API fail

4. **Rate Limit Transparency**
   - Khi rate limit → "Rate limit reached for [API]. Using cached data (age: X minutes)..."

### 4.3. Đóng Góp Giá Trị Thực Tế

#### **Phase 1 (MVP) - High Value, Low Complexity:**

1. **Weather API** ⭐⭐⭐⭐⭐
   - **Value**: Rất cao (nhiều user hỏi thời tiết)
   - **Complexity**: Thấp (API đơn giản, response rõ ràng)
   - **ROI**: Cao

2. **News API** ⭐⭐⭐⭐
   - **Value**: Cao (real-time news quan trọng)
   - **Complexity**: Trung bình (cần parse, format)
   - **ROI**: Cao

#### **Phase 2 - Medium Value, Medium Complexity:**

3. **FX Rate API** ⭐⭐⭐
   - **Value**: Trung bình (ít user hỏi, nhưng quan trọng khi hỏi)
   - **Complexity**: Thấp (API đơn giản)
   - **ROI**: Trung bình

4. **Sports API** ⭐⭐
   - **Value**: Thấp-trung bình (niche use case)
   - **Complexity**: Trung bình (cần parse schedule)
   - **ROI**: Thấp-trung bình

#### **Phase 3 - Advanced:**

5. **Maps / Location API** ⭐⭐
   - **Value**: Thấp (ít use case)
   - **Complexity**: Trung bình-cao (geocoding, routing)
   - **ROI**: Thấp

6. **Open Data APIs (World Bank, etc.)** ⭐⭐⭐
   - **Value**: Trung bình (fact-checking)
   - **Complexity**: Trung bình (cần integrate vào Validation Chain)
   - **ROI**: Trung bình

---

## 5. Kế Hoạch Hành Động (Roadmap)

### Phase 1: MVP - Weather & News (2-3 tuần)

**Mục tiêu**: Implement 2 providers đơn giản nhất, hook vào chat pipeline

**Deliverables:**

1. **Module Structure**
   - Tạo `backend/external_data/` folder
   - Implement `ExternalDataOrchestrator`
   - Implement `WeatherProvider` (Open-Meteo)
   - Implement `NewsProvider` (GNews)

2. **Intent Detection**
   - Mở rộng `question_classifier.py` để detect weather/news queries
   - Confidence threshold: 0.7

3. **Integration vào Chat Pipeline**
   - Sửa `chat_router.py` để route external data queries
   - Format response với source + timestamp
   - Logging đầy đủ

4. **Caching (Basic)**
   - In-memory cache với TTL:
     - Weather: 15 phút
     - News: 2 giờ

5. **Error Handling**
   - Retry logic (2 retries)
   - Fallback to RAG nếu API fail
   - Error messages transparent

**Files cần tạo:**
- `backend/external_data/__init__.py`
- `backend/external_data/orchestrator.py`
- `backend/external_data/providers/__init__.py`
- `backend/external_data/providers/base.py`
- `backend/external_data/providers/weather.py`
- `backend/external_data/providers/news.py`
- `backend/external_data/intent_detector.py`
- `backend/external_data/cache.py` (in-memory)

**Files cần sửa:**
- `backend/api/routers/chat_router.py` - Thêm external data routing
- `backend/core/question_classifier.py` - Thêm intent detection

**Rủi ro lớn nhất:**
- Intent detection không chính xác → route sai query
- **Mitigation**: Confidence threshold cao (0.7), fallback to RAG

**Definition of Done:**
- ✅ Weather queries được route đúng và trả về data từ API
- ✅ News queries được route đúng và trả về data từ API
- ✅ Response có source + timestamp
- ✅ Caching hoạt động (giảm API calls)
- ✅ Error handling hoạt động (fallback to RAG)
- ✅ Logging đầy đủ cho audit

### Phase 2: Caching, Retry, Rate Limit (1-2 tuần)

**Mục tiêu**: Production-ready với caching, retry, rate limit handling

**Deliverables:**

1. **Advanced Caching**
   - Redis cache (nếu có) hoặc improved in-memory cache
   - Cache invalidation logic
   - Cache metrics (hit rate, miss rate)

2. **Retry & Rate Limit**
   - Exponential backoff retry
   - Rate limit tracking (in-memory hoặc Redis)
   - Queue requests nếu rate limit

3. **Monitoring & Metrics**
   - API call metrics (success rate, latency, cache hit rate)
   - Rate limit alerts
   - Error rate tracking

4. **Integration với Validation Chain (Optional)**
   - `ExternalDataValidator` để fact-check numeric claims
   - So sánh RAG data vs API data

**Files cần tạo/sửa:**
- `backend/external_data/cache.py` - Upgrade to Redis nếu có
- `backend/external_data/rate_limiter.py` - Rate limit tracking
- `backend/external_data/metrics.py` - Metrics tracking
- `backend/validators/external_data.py` - [NEW] ExternalDataValidator (nếu implement)

**Rủi ro lớn nhất:**
- Rate limit quá thấp → nhiều requests bị reject
- **Mitigation**: Aggressive caching, queue requests

**Definition of Done:**
- ✅ Caching giảm API calls ít nhất 50%
- ✅ Retry logic hoạt động (2 retries với backoff)
- ✅ Rate limit tracking hoạt động
- ✅ Metrics visible trong dashboard hoặc logs

### Phase 3: UI Support, Testing, Monitoring (1-2 tuần)

**Mục tiêu**: Production-ready với UI support, testing, monitoring

**Deliverables:**

1. **Dashboard Support**
   - Hiện external data usage trong dashboard
   - Hiện cache hit rate, API call metrics
   - Hiện source + timestamp trong UI

2. **Testing**
   - Unit tests cho providers
   - Integration tests cho orchestrator
   - E2E tests cho chat pipeline với external data

3. **Monitoring & Alerts**
   - Alert nếu API fail rate > threshold
   - Alert nếu rate limit gần đạt
   - Alert nếu cache hit rate thấp

4. **Documentation**
   - API documentation cho external data endpoints
   - User guide về external data features
   - Developer guide về adding new providers

**Files cần tạo/sửa:**
- `tests/test_external_data/` - Test suite
- `dashboard.py` - Thêm external data metrics
- `docs/EXTERNAL_DATA_GUIDE.md` - Documentation

**Rủi ro lớn nhất:**
- UI changes có thể break existing features
- **Mitigation**: Careful testing, backward compatibility

**Definition of Done:**
- ✅ Dashboard hiện external data metrics
- ✅ Test coverage > 80%
- ✅ Monitoring & alerts hoạt động
- ✅ Documentation đầy đủ

---

## Tổng Kết

### Alignment với Triết Lý StillMe: ✅ PHÙ HỢP

External Data Layer **phù hợp** với triết lý StillMe với điều kiện:
- Luôn hiện source, timestamp, raw data
- Không "đóng gói" như tri thức nội tại
- Giữ nguyên "evidence-over-authority"
- Intellectual humility khi API fail

### Độ Khó: TRUNG BÌNH

- Backend complexity: Trung bình (routing, caching, error handling)
- Performance impact: Thấp-trung bình (caching giảm latency)
- Risk level: Trung bình (cần guardrails cho transparency)

### Giá Trị: CAO (Phase 1)

- Weather & News APIs: High value, low complexity
- ROI cao cho Phase 1
- Phase 2/3 tùy vào nhu cầu

### Roadmap: 3 Phases (4-6 tuần tổng)

- **Phase 1**: MVP với Weather & News (2-3 tuần)
- **Phase 2**: Caching, retry, rate limit (1-2 tuần)
- **Phase 3**: UI, testing, monitoring (1-2 tuần)

---

**Kết luận**: External Data Layer là một bổ sung **có giá trị** cho StillMe, phù hợp với triết lý transparency và anti-hallucination. Nên bắt đầu với Phase 1 (Weather & News) để validate approach trước khi mở rộng.



