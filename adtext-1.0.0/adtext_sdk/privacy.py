import hashlib
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger("adtext_sdk")
IAB_SIGNALS: Dict[str, List[str]] = {
    "IAB1": ["entertainment", "celebrity", "movie", "music", "television"],
    "IAB2": ["car", "vehicle", "auto", "driving", "motorcycle"],
    "IAB3": ["business", "market", "economy", "invest", "stock"],
    "IAB4": ["career", "job", "resume", "hiring", "salary"],
    "IAB5": ["education", "school", "university", "learning", "course"],
    "IAB6": ["family", "parenting", "children", "baby", "pregnancy"],
    "IAB7": ["health", "medical", "fitness", "nutrition", "wellness"],
    "IAB8": ["food", "recipe", "cooking", "restaurant", "cuisine"],
    "IAB12": ["news", "breaking", "headline", "journalism", "report"],
    "IAB13": ["finance", "investment", "banking", "insurance", "tax"],
    "IAB15": ["science", "research", "biology", "chemistry", "physics"],
    "IAB17": ["sport", "football", "basketball", "soccer", "tennis"],
    "IAB18": ["fashion", "style", "clothing", "beauty", "luxury"],
    "IAB19": ["technology", "software", "hardware", "internet", "programming"],
    "IAB20": ["travel", "tourism", "hotel", "flight", "vacation"],
    "IAB22": ["shopping", "ecommerce", "deals", "discount", "product"],
}
STOP_WORDS = frozenset([
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "is",
    "was",
    "are",
    "were",
    "be",
    "been",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "we",
    "you",
    "he",
    "she",
    "they",
    "what",
    "which",
    "who",
    "when",
    "how",
])


class StandardPlugin:
    tier = "STANDARD"

    async def build_context(self, text: Optional[str] = None, url: Optional[str] = None) -> Dict:
        return {"type": "standard", "text": text, "url": url}


class EnhancedPrivacyPlugin:
    tier = "ENHANCED"

    async def build_context(self, text: Optional[str] = None, url: Optional[str] = None) -> Dict:
        if not text:
            return {"type": "enhanced", "url": url}
        return {
            "type": "enhanced",
            "iabCategory": self._classify_iab(text),
            "keywords": self._extract_keywords(text),
            "contentHash": self._hash_content(text),
            "sentiment": self._sentiment_signal(text),
            "url": url,
        }

    def _extract_keywords(self, text: str, n: int = 10) -> List[str]:
        words = re.sub(r"[^a-z\s]", " ", text.lower()).split()
        words = [w for w in words if len(w) > 3 and w not in STOP_WORDS]
        freq: Dict[str, int] = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:n]]

    def _classify_iab(self, text: str) -> str:
        lower = text.lower()
        best_cat, best_score = "IAB12", 0
        for cat, signals in IAB_SIGNALS.items():
            score = sum(lower.count(s) for s in signals)
            if score > best_score:
                best_cat, best_score = cat, score
        return best_cat

    def _hash_content(self, text: str) -> str:
        normalized = re.sub(r"\s+", " ", text.lower()).strip()[:500]
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _sentiment_signal(self, text: str) -> str:
        pos_words = ["great", "best", "amazing", "love", "excellent", "good", "happy", "wonderful"]
        neg_words = ["bad", "terrible", "awful", "hate", "horrible", "worst", "poor", "disappointing"]
        lower = text.lower()
        pos = sum(1 for w in pos_words if w in lower)
        neg = sum(1 for w in neg_words if w in lower)
        if pos > neg + 2:
            return "positive"
        if neg > pos + 2:
            return "negative"
        return "neutral"


class ServerEmbeddingPlugin:
    tier = "SERVER_EMBEDDING"

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,
        batch_size: int = 32,
    ):
        self._model_name = model_name
        self._device = device
        self._batch_size = batch_size
        self._model = None
        self._executor = None

    async def init(self) -> "ServerEmbeddingPlugin":
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RuntimeError(
                "sentence-transformers is required for ServerEmbeddingPlugin.\n"
                "Install it with: pip install sentence-transformers"
            )
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="adtext-embed")

        def _load():
            model = SentenceTransformer(self._model_name, device=self._device)
            model.eval()
            return model

        loop = asyncio.get_event_loop()
        self._model = await loop.run_in_executor(self._executor, _load)
        logger.info(
            "ServerEmbeddingPlugin: loaded %s on %s",
            self._model_name,
            self._model.device,
        )
        return self

    async def build_context(self, text: Optional[str] = None, url: Optional[str] = None) -> Dict:
        if not text or self._model is None:
            logger.warning(
                "ServerEmbeddingPlugin not ready — falling back to ENHANCED tier. Did you call await plugin.init()?"
            )
            fallback = EnhancedPrivacyPlugin()
            return await fallback.build_context(text, url)
        import asyncio

        loop = asyncio.get_event_loop()

        def _embed():
            return self._model.encode(
                text,
                normalize_embeddings=True,
                show_progress_bar=False,
            ).tolist()

        embedding = await loop.run_in_executor(self._executor, _embed)
        return {
            "type": "server_embedding",
            "embedding": embedding,
            "url": url,
        }

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    def destroy(self) -> None:
        if self._executor:
            self._executor.shutdown(wait=False)
        self._model = None
