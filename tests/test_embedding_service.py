from __future__ import annotations

from services import embedding_service


def test_embed_texts_batches_large_requests(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    calls: list[list[str]] = []

    class _RespItem:
        def __init__(self, idx: int):
            self.embedding = [float(idx)] * embedding_service.EMBEDDING_DIM

    class _EmbeddingsApi:
        def create(self, *, model, input):
            calls.append(list(input))
            base = sum(len(batch) for batch in calls[:-1])
            return type(
                "Resp",
                (),
                {"data": [_RespItem(base + i) for i, _ in enumerate(input)]},
            )()

    class _Client:
        def __init__(self):
            self.embeddings = _EmbeddingsApi()

    monkeypatch.setattr(embedding_service, "_get_client", lambda: _Client())

    texts = [f"text {i}" for i in range(130)]
    vectors = embedding_service.embed_texts(texts)

    assert vectors is not None
    assert len(vectors) == 130
    assert [len(batch) for batch in calls] == [64, 64, 2]

