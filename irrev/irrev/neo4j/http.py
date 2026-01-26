"""Neo4j transactional HTTP client (small, dependency-free).

This module is intentionally minimal to avoid adding heavy dependencies.
It targets Neo4j's transactional HTTP endpoint:
  - Neo4j 4+/5: POST /db/{database}/tx/commit
  - Legacy:     POST /db/data/transaction/commit
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Neo4jHttpConfig:
    http_uri: str
    user: str
    password: str
    database: str
    timeout_s: float = 10.0
    allow_default_db_fallback: bool = False


class Neo4jHttpClient:
    """Minimal Neo4j transactional HTTP client."""

    def __init__(self, cfg: Neo4jHttpConfig) -> None:
        self._cfg = cfg
        base = cfg.http_uri.rstrip("/")

        self._commit_urls = [
            f"{base}/db/{cfg.database}/tx/commit",
        ]

        if cfg.allow_default_db_fallback and cfg.database != "neo4j":
            self._commit_urls.append(f"{base}/db/neo4j/tx/commit")

        # Neo4j 3.5 legacy endpoint (single-db).
        self._commit_urls.append(f"{base}/db/data/transaction/commit")

        self._resolved_commit_url: str | None = None

        token = base64.b64encode(f"{cfg.user}:{cfg.password}".encode("utf-8")).decode("ascii")
        self._auth_header = f"Basic {token}"

    @property
    def resolved_commit_url(self) -> str | None:
        return self._resolved_commit_url

    def commit(self, statements: list[dict[str, Any]]) -> dict[str, Any]:
        """Commit one or more statements and return the decoded JSON payload."""
        body = json.dumps({"statements": statements}).encode("utf-8")

        last_http_error: HTTPError | None = None
        last_url_error: URLError | None = None

        urls = [self._resolved_commit_url] if self._resolved_commit_url else []
        urls += [u for u in self._commit_urls if u not in urls]

        for commit_url in urls:
            req = Request(
                commit_url,
                data=body,
                method="POST",
                headers={
                    "Authorization": self._auth_header,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            try:
                with urlopen(req, timeout=self._cfg.timeout_s) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                self._resolved_commit_url = commit_url
                break
            except HTTPError as e:
                last_http_error = e
                if e.code == 404:
                    continue
                raise RuntimeError(f"Neo4j HTTP error {e.code}: {e.reason}") from e
            except URLError as e:
                last_url_error = e
                raise RuntimeError(f"Neo4j connection error: {e.reason}") from e
        else:
            if last_http_error is not None:
                raise RuntimeError(f"Neo4j HTTP error 404: Not Found (tried {len(urls)} endpoints)") from last_http_error
            if last_url_error is not None:
                raise RuntimeError(f"Neo4j connection error: {last_url_error.reason}") from last_url_error
            raise RuntimeError("Neo4j commit failed: no response payload")

        errors = payload.get("errors") or []
        if errors:
            first = errors[0]
            code = first.get("code", "Neo4jError")
            msg = first.get("message", "Unknown Neo4j error")
            raise RuntimeError(f"{code}: {msg}")

        return payload

    def query_rows(self, query: str, *, parameters: dict[str, Any] | None = None) -> tuple[list[str], list[list[Any]]]:
        payload = self.commit(
            [
                {
                    "statement": query,
                    "parameters": parameters or {},
                    "resultDataContents": ["row"],
                }
            ]
        )
        results = payload.get("results") or []
        if not results:
            return [], []
        first = results[0]
        columns = first.get("columns") or []
        data = first.get("data") or []
        rows = [d.get("row") for d in data if isinstance(d, dict)]
        return list(columns), rows  # type: ignore[return-value]

