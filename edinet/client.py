"""EDINET API v2 書類一覧 API クライアント。

書類一覧 API (documents.json) を日付指定で叩き、提出書類のメタデータ一覧を返す。
レート制限（リクエスト間 3〜5 秒）の遵守と、一時的なエラーへのリトライを担う。

API 仕様: https://disclosure2.edinet-fsa.go.jp/ （EDINET API 仕様書 Version 2）
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

DOCUMENTS_URL = "https://api.edinet-fsa.go.jp/api/v2/documents.json"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class EdinetClient:
    """書類一覧 API の薄いクライアント。"""

    def __init__(
        self,
        api_key: str,
        *,
        rate_limit_seconds: float = 4.0,
        max_retries: int = 5,
        timeout: int = 60,
    ) -> None:
        self._api_key = api_key
        self._rate_limit_seconds = rate_limit_seconds
        self._max_retries = max_retries
        self._timeout = timeout
        self._last_request = 0.0

    def get_documents(self, target_date: str) -> list[dict]:
        """指定日 (YYYY-MM-DD) の提出書類一覧を返す。

        type=2 はメタデータと提出書類一覧の両方を取得する。提出が無い日
        （土日・祝日等）は status 200 で空の results が返る。
        """
        params = urllib.parse.urlencode(
            {"date": target_date, "type": "2", "Subscription-Key": self._api_key}
        )
        body = self._request(f"{DOCUMENTS_URL}?{params}", target_date)
        metadata = body.get("metadata") or {}
        status = str(metadata.get("status") or "")
        if status not in ("200", ""):
            logger.warning(
                "date=%s status=%s message=%s",
                target_date,
                status,
                metadata.get("message"),
            )
        return body.get("results") or []

    def _request(self, url: str, target_date: str) -> dict:
        for attempt in range(1, self._max_retries + 1):
            self._throttle()
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "queria-dataset-edinet/1.0"}
                )
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                if e.code in RETRYABLE_STATUS and attempt < self._max_retries:
                    wait = self._rate_limit_seconds * 2**attempt
                    logger.warning(
                        "date=%s HTTP %d, retry %d/%d after %.1fs",
                        target_date,
                        e.code,
                        attempt,
                        self._max_retries,
                        wait,
                    )
                    time.sleep(wait)
                    continue
                raise
            except urllib.error.URLError as e:
                if attempt < self._max_retries:
                    wait = self._rate_limit_seconds * 2**attempt
                    logger.warning(
                        "date=%s URLError %s, retry %d/%d after %.1fs",
                        target_date,
                        e.reason,
                        attempt,
                        self._max_retries,
                        wait,
                    )
                    time.sleep(wait)
                    continue
                raise
        raise RuntimeError(f"failed to fetch EDINET documents for {target_date}")

    def _throttle(self) -> None:
        """前回リクエストからの経過がレート制限未満なら待機する。"""
        elapsed = time.monotonic() - self._last_request
        if elapsed < self._rate_limit_seconds:
            time.sleep(self._rate_limit_seconds - elapsed)
        self._last_request = time.monotonic()
