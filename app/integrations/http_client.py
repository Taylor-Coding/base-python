import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)


class HttpClient:
    """외부 API 호출용 HTTP 클라이언트.

    사용 예시:
        client = HttpClient(base_url="https://api.example.com", headers={"X-Api-Key": "..."})
        data = client.get("/users/1")
        result = client.post("/orders", json={"item": "book"})
    """

    def __init__(
        self,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers=headers or {},
            timeout=timeout,
        )

    # ── 요청 ────────────────────────────────────────────────

    def get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        response = self._client.get(url, params=params)
        return self._handle(response)

    def post(self, url: str, json: Any = None, data: Any = None) -> Any:
        response = self._client.post(url, json=json, data=data)
        return self._handle(response)

    def put(self, url: str, json: Any = None) -> Any:
        response = self._client.put(url, json=json)
        return self._handle(response)

    def patch(self, url: str, json: Any = None) -> Any:
        response = self._client.patch(url, json=json)
        return self._handle(response)

    def delete(self, url: str) -> Any:
        response = self._client.delete(url)
        return self._handle(response)

    # ── 응답 처리 ────────────────────────────────────────────

    def _handle(self, response: httpx.Response) -> Any:
        logger.debug("%s %s → %s", response.request.method, response.request.url, response.status_code)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("External API error: %s %s", e.response.status_code, e.response.text)
            raise ExternalApiError(
                status_code=e.response.status_code,
                message=e.response.text,
            ) from e
        except httpx.TimeoutException as e:
            logger.error("External API timeout: %s", e.request.url)
            raise ExternalApiError(status_code=504, message="External API timeout") from e
        except httpx.RequestError as e:
            logger.error("External API request failed: %s", e)
            raise ExternalApiError(status_code=502, message="External API unreachable") from e

        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class ExternalApiError(Exception):
    """외부 API 호출 실패 시 발생하는 예외."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")
