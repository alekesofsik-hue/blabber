from __future__ import annotations

import requests

from services import url_ingestion_service as url_svc


class _FakeResponse:
    def __init__(self, *, url: str, text: str, content_type: str = "text/html; charset=utf-8", status_code: int = 200):
        self.url = url
        self.text = text
        self.content = text.encode("utf-8")
        self.headers = {"content-type": content_type}
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


def test_fetch_url_document_success_html(monkeypatch):
    def _fake_get(url, timeout, allow_redirects):
        return _FakeResponse(
            url="https://example.com/final",
            text="""
                <html>
                  <head><title>Article title</title></head>
                  <body><h1>Hello</h1><p>Useful page content.</p></body>
                </html>
            """,
        )

    monkeypatch.setattr(url_svc._SESSION, "get", _fake_get)
    payload = url_svc.fetch_url_document("https://example.com/start")

    assert payload["url"] == "https://example.com/final"
    assert payload["title"] == "Article title"
    assert "Useful page content." in payload["text"]


def test_fetch_url_document_rejects_non_text(monkeypatch):
    def _fake_get(url, timeout, allow_redirects):
        return _FakeResponse(
            url=url,
            text="binary",
            content_type="application/pdf",
        )

    monkeypatch.setattr(url_svc._SESSION, "get", _fake_get)
    try:
        url_svc.fetch_url_document("https://example.com/file.pdf")
    except ValueError as exc:
        assert "Неподдерживаемый тип содержимого" in str(exc)
    else:
        raise AssertionError("Expected ValueError for non-text content")


def test_fetch_url_document_handles_timeout(monkeypatch):
    def _fake_get(url, timeout, allow_redirects):
        raise requests.Timeout()

    monkeypatch.setattr(url_svc._SESSION, "get", _fake_get)
    try:
        url_svc.fetch_url_document("https://example.com/slow")
    except ValueError as exc:
        assert "слишком долго" in str(exc)
    else:
        raise AssertionError("Expected ValueError for timeout")


def test_fetch_url_document_rejects_empty_page(monkeypatch):
    def _fake_get(url, timeout, allow_redirects):
        return _FakeResponse(
            url=url,
            text="<html><head><title>Empty</title></head><body><script>x=1</script></body></html>",
        )

    monkeypatch.setattr(url_svc._SESSION, "get", _fake_get)
    try:
        url_svc.fetch_url_document("https://example.com/empty")
    except ValueError as exc:
        assert "не содержит читаемого текста" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty page")
