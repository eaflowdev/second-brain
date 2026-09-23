from typing import Optional

from fastembed import TextEmbedding

# Multilingual (French included), 384 dimensions, no GPU/torch needed (ONNX runtime).
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class Embedder:
    """Wraps the embedding model. Loaded lazily so importing this module stays cheap."""

    _model: Optional[TextEmbedding] = None


    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self.model_name = model_name

    def _get_model(self) -> TextEmbedding:
        if Embedder._model is None:
            Embedder._model = TextEmbedding(model_name=self.model_name)
        return Embedder._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return [vector.tolist() for vector in self._get_model().embed(texts)]
