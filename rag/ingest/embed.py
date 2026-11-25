"""Step 4 - embeddings with a small multilingual ONNX model (no GPU, no API)."""
from functools import lru_cache

import numpy as np
from fastembed import TextEmbedding
from fastembed.common.model_description import ModelSource, PoolingType

from ..config import EMBED_DIM, EMBED_FILE, EMBED_REPO, MODEL_CACHE


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    if EMBED_REPO not in {m["model"] for m in TextEmbedding.list_supported_models()}:
        TextEmbedding.add_custom_model(model=EMBED_REPO, pooling=PoolingType.MEAN, normalization=True,
                                       sources=ModelSource(hf=EMBED_REPO), dim=EMBED_DIM, model_file=EMBED_FILE)
    MODEL_CACHE.mkdir(parents=True, exist_ok=True)
    return TextEmbedding(EMBED_REPO, cache_dir=str(MODEL_CACHE))


def embed_passages(texts: list[str]) -> np.ndarray:
    # e5 models are trained with "passage:" / "query:" prefixes.
    return np.array(list(_model().embed([f"passage: {t}" for t in texts], batch_size=16)))


@lru_cache(maxsize=512)
def embed_query(text: str) -> tuple[float, ...]:
    return tuple(next(iter(_model().embed([f"query: {text}"]))).tolist())
