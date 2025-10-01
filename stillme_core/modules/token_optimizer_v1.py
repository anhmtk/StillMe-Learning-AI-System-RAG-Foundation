#!/usr/bin/env python3
"""
TokenOptimizer_ - Phiên bản tối ưu kết hợp ưu điểm từ cả hai phiên bản
Chức năng chính:
- Semantic caching với hybrid exact/similar matching
- Tối ưu token thông minh với compression có ngữ nghĩa
- Quản lý rate limiting và chất lượng response
- Hỗ trợ đặc biệt cho tiếng Việt
"""

import hashlib
import logging
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import tiktoken
from pydantic import BaseModel, ConfigDict, Field
from stillme_core.embeddings import SentenceTransformerBackend

# ======================
# Cấu hình logging
# ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# ======================
# Model cấu hình
# ======================
class TokenOptimizerConfig(BaseModel):
    min_similarity_threshold: float = Field(0.82, ge=0.5, le=1.0)
    max_prompt_tokens: int = Field(3000, gt=0)
    cache_ttl: timedelta = Field(default=timedelta(minutes=30))
    max_cache_size: int = Field(500, gt=0)
    enable_compression: bool = True
    language: str = "vi"
    token_encoding: str = "cl100k_base"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"


# ======================
# Cache Item
# ======================
class CacheItem(BaseModel):
    query: str
    response: str
    embedding: np.ndarray
    created_at: datetime = Field(default_factory=datetime.now)
    ttl: Optional[timedelta] = None
    token_count: int
    usage_count: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ======================
# Semantic Hybrid Cache
# ======================
class SemanticHybridCache:
    def __init__(self, config: TokenOptimizerConfig) -> None:
        self.cache: OrderedDict[str, CacheItem] = OrderedDict()
        self.max_size = config.max_cache_size
        self.embedding_model = SentenceTransformerBackend(config.embedding_model)

    def _generate_key(self, text: str) -> str:
        normalized = self._normalize_text(text)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _normalize_text(self, text: str) -> str:
        text = text.lower().strip()
        replacements = {
            " ko ": " không ",
            " k ": " không ",
            " dc ": " được ",
            " ntn ": " như thế nào ",
            # Also handle without spaces
            "ko": "không",
            "dc": "được", 
            "ntn": "như thế nào",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return " ".join(text.split())

    def _get_embedding(self, text: str) -> np.ndarray:
        try:
            embedding = self.embedding_model.embed([text])[0]
            return np.array(embedding)
        except Exception as e:
            # Log the error but don't crash
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Embedding failed for text '{text[:50]}...': {e}")
            
            # Return a deterministic fallback embedding based on text hash
            import hashlib
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            # Convert hash to deterministic vector
            hash_int = int(text_hash[:8], 16)
            fallback_embedding = np.array([(hash_int >> i) & 1 for i in range(384)], dtype=np.float32)
            # Normalize to unit vector
            fallback_embedding = fallback_embedding / (np.linalg.norm(fallback_embedding) + 1e-8)
            return fallback_embedding

    def get_exact_match(self, query: str) -> Optional[CacheItem]:
        key = self._generate_key(query)
        if key in self.cache:
            item = self.cache[key]
            if item.ttl is None or (datetime.now() - item.created_at) <= item.ttl:
                item.usage_count += 1
                self.cache.move_to_end(key)
                return item
        return None

    def get_semantic_match(
        self, query: str, threshold: float
    ) -> Optional[Tuple[CacheItem, float]]:
        query_embedding = self._get_embedding(self._normalize_text(query))
        best_match = None
        best_score = 0.0

        for key, item in self.cache.items():
            if item.ttl and (datetime.now() - item.created_at) > item.ttl:
                continue

            similarity = np.dot(query_embedding, item.embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(item.embedding)
            )

            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = item

        if best_match:
            best_match.usage_count += 1
            return best_match, best_score
        return None

    def add_item(
        self,
        query: str,
        response: str,
        token_count: int,
        ttl: Optional[timedelta] = None,
    ) -> None:
        key = self._generate_key(query)
        item = CacheItem(
            query=query,
            response=response,
            embedding=self._get_embedding(self._normalize_text(query)),
            ttl=ttl,
            token_count=token_count,
        )
        self.cache[key] = item
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def clear_expired(self) -> int:
        now = datetime.now()
        expired_keys = [
            k for k, v in self.cache.items() if v.ttl and (now - v.created_at) > v.ttl
        ]
        for k in expired_keys:
            del self.cache[k]
        return len(expired_keys)


# ======================
# Token Optimizer Core
# ======================
class TokenOptimizer:
    def __init__(self, config: TokenOptimizerConfig) -> None:
        self.config = config
        self.cache = SemanticHybridCache(config)
        self.tokenizer = tiktoken.get_encoding(config.token_encoding)
        self.token_saved = 0
        self.total_requests = 0
        self.rate_limiter = TokenRateLimiter(max_tokens_per_minute=90000)
        self.quality_monitor = QualityMonitor()

    def process_request(
        self, query: str, context: List[str], api_callback: Callable[[str], str]
    ) -> Tuple[str, bool]:
        self.total_requests += 1

        try:
            self.rate_limiter.check_limit(self._count_tokens(query))

            cached_item = self.cache.get_exact_match(query)
            if cached_item:
                logger.info(f"Exact cache hit for query: {query[:50]}...")
                return cached_item.response, True

            semantic_match = self.cache.get_semantic_match(
                query, self.config.min_similarity_threshold
            )
            if semantic_match:
                item, similarity = semantic_match
                logger.info(
                    f"Semantic cache hit (similarity: {similarity:.2f}) for query: {query[:50]}..."
                )
                return item.response, True

            optimized_prompt = self._optimize_prompt(query, context)
            response = api_callback(optimized_prompt)
            response_tokens = self._count_tokens(response)

            self.cache.add_item(
                query=query,
                response=response,
                token_count=response_tokens,
                ttl=self.config.cache_ttl,
            )

            self.quality_monitor.log_quality(
                original_query=query, optimized_response=response
            )
            return response, False

        except Exception as e:
            logger.error(f"Optimization failed, using fallback: {e!s}")
            return api_callback(query), False

    def _optimize_prompt(self, query: str, context: List[str]) -> str:
        optimized = self._normalize_query(query)

        if context:
            context_str = self._compress_context(context)
            combined = f"{context_str}\n\n{optimized}"
            if self._count_tokens(combined) <= self.config.max_prompt_tokens:
                return combined

        if (
            self._count_tokens(optimized) > self.config.max_prompt_tokens
            and self.config.enable_compression
        ):
            optimized = self._smart_compress(optimized)

        return optimized

    def _normalize_query(self, query: str) -> str:
        return self.cache._normalize_text(query)

    def _compress_context(self, context: List[str]) -> str:
        important_messages = context[-3:] if len(context) > 3 else context
        return "\n".join(important_messages)

    def _smart_compress(self, text: str) -> str:
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        if len(sentences) > 3:
            important = [sentences[0], max(sentences[1:-1], key=len), sentences[-1]]
            compressed = ". ".join(important) + "."
            saved = self._count_tokens(text) - self._count_tokens(compressed)
            logger.info(f"Compressed prompt, saved {saved} tokens")
            return compressed
        return text

    def _count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def warmup_cache(self, qa_pairs: List[Dict[str, str]]) -> None:
        for pair in qa_pairs:
            self.cache.add_item(
                query=pair["question"],
                response=pair["answer"],
                token_count=self._count_tokens(pair["answer"]),
                ttl=timedelta(hours=24),
            )


# ======================
# Supporting Classes
# ======================
class TokenRateLimiter:
    def __init__(self, max_tokens_per_minute: int) -> None:
        self.max_tokens = max_tokens_per_minute
        self.token_count = 0
        self.last_reset = time.time()
        self.used_tokens = 0  # Thêm thuộc tính này

    def check_limit(self, tokens: int) -> None:
        if time.time() - self.last_reset > 60:
            self.token_count = 0
            self.used_tokens = 0
            self.last_reset = time.time()

        if self.token_count + tokens > self.max_tokens:
            raise TokenLimitExceededError(
                f"Token limit exceeded: {self.token_count + tokens}/{self.max_tokens}"
            )
        self.token_count += tokens
        self.used_tokens += tokens


class QualityMonitor:
    def __init__(self) -> None:
        self.comparisons: List[Dict[str, Any]] = []

    def log_quality(self, original_query: str, optimized_response: str) -> None:
        diff = len(original_query) - len(optimized_response)
        self.comparisons.append(
            {
                "timestamp": datetime.now(),
                "original": original_query,
                "optimized": optimized_response,
                "length_diff": abs(diff),  # Luôn là số dương
            }
        )


class TokenLimitExceededError(Exception):
    pass
