import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import get_settings


class ResearchError(Exception):
    """Messages never contain keys or fetched content."""


class ResearchNotConfigured(ResearchError):
    pass


class ResearchRateLimited(ResearchError):
    def __init__(self, retry_after: int | None = None):
        super().__init__("The search provider rate limit was reached.")
        self.retry_after = retry_after


class ResearchUnavailable(ResearchError):
    pass


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    content: str


@dataclass(frozen=True)
class Page:
    url: str
    text: str


class ResearchProvider(Protocol):
    name: str

    def search(self, query: str, *, max_results: int = 5, include_domains: list[str] | None = None, exclude_domains: list[str] | None = None) -> list[SearchHit]: ...

    def extract(self, urls: list[str]) -> list[Page]: ...


class TavilyProvider:
    """Tavily REST API (https://docs.tavily.com). The request and response shapes follow its official OpenAPI description.
    NOT yet exercised against the real service (no API key was available during development)."""

    name = "tavily"

    def __init__(self, api_key: str, base_url: str, timeout: int):
        if not api_key:
            raise ResearchNotConfigured("TAVILY_API_KEY is not set.")
        self._key, self._url, self._timeout = api_key, base_url.rstrip("/"), timeout

    def _post(self, path: str, body: dict) -> dict:
        try:
            r = httpx.post(f"{self._url}{path}", json=body, headers={"Authorization": f"Bearer {self._key}"}, timeout=self._timeout)
        except httpx.HTTPError as e:
            raise ResearchUnavailable("Could not reach the search provider.") from e
        if r.status_code == 429:
            ra = r.headers.get("retry-after")
            raise ResearchRateLimited(int(ra) if ra and ra.isdigit() else None)
        if r.status_code in (401, 403):
            raise ResearchUnavailable("The search provider rejected the API key.")
        if r.status_code in (432, 433):
            raise ResearchUnavailable("The search provider plan or usage limit was reached.")
        if r.status_code >= 400:
            raise ResearchUnavailable(f"The search provider returned an error ({r.status_code}).")
        try:
            data = r.json()
        except ValueError as e:
            raise ResearchUnavailable("The search provider returned an unexpected response.") from e
        if not isinstance(data, dict):
            raise ResearchUnavailable("The search provider returned an unexpected response.")
        return data

    def search(self, query, *, max_results=5, include_domains=None, exclude_domains=None):
        body: dict = {"query": query, "search_depth": "basic", "max_results": max(1, min(max_results, 10))}
        if include_domains:
            body["include_domains"] = include_domains
        if exclude_domains:
            body["exclude_domains"] = exclude_domains
        out = []
        for item in self._post("/search", body).get("results") or []:
            if isinstance(item, dict) and isinstance(item.get("url"), str) and isinstance(item.get("content"), str):
                out.append(SearchHit(title=str(item.get("title") or "")[:300], url=item["url"], content=item["content"]))
        return out

    def extract(self, urls):
        if not urls:
            return []
        data = self._post("/extract", {"urls": urls[:20], "extract_depth": "basic", "format": "text"})
        return [
            Page(url=i["url"], text=i["raw_content"])
            for i in data.get("results") or []
            if isinstance(i, dict) and isinstance(i.get("url"), str) and isinstance(i.get("raw_content"), str)
        ]


class FakeResearchProvider:
    """Scripted provider for tests and offline development (RESEARCH_PROVIDER=fake). Never touches the network."""

    name = "fake"

    def __init__(self, search_fn: Callable[..., list[SearchHit]] | None = None, pages: dict[str, str] | None = None, error: Exception | None = None):
        self.search_fn, self.pages, self.error = search_fn, pages or {}, error
        self.searches: list[dict] = []
        self.extracted: list[list[str]] = []

    def search(self, query, *, max_results=5, include_domains=None, exclude_domains=None):
        self.searches.append({"query": query, "include": include_domains, "exclude": exclude_domains})
        if self.error:
            raise self.error
        return list(self.search_fn(query, include_domains, exclude_domains)) if self.search_fn else []

    def extract(self, urls):
        self.extracted.append(list(urls))
        if self.error:
            raise self.error
        return [Page(url=u, text=self.pages[u]) for u in urls if u in self.pages]


class BudgetedProvider:
    """Hard cap on credits spent per run, whatever the workflow tries to do."""

    def __init__(self, inner: ResearchProvider, max_searches: int, max_extract_urls: int):
        self.inner, self.name = inner, inner.name
        self.searches_left, self.extracts_left = max_searches, max_extract_urls
        self.searches_used = self.extracts_used = 0

    def search(self, query, **kw):
        if self.searches_left <= 0:
            return []
        self.searches_left -= 1
        self.searches_used += 1
        return self.inner.search(query, **kw)

    def extract(self, urls):
        urls = urls[: max(self.extracts_left, 0)]
        if not urls:
            return []
        self.extracts_left -= len(urls)
        self.extracts_used += len(urls)
        return self.inner.extract(urls)


def get_research_provider() -> ResearchProvider:
    s = get_settings()
    if s.research_provider == "fake":
        return FakeResearchProvider()
    return TavilyProvider(s.tavily_api_key, s.tavily_base_url, s.research_timeout_seconds)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()
