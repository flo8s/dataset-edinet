"""EDINET コードリスト（EDINETコード集約一覧）取得。

提出者（企業・ファンド等）のマスタ ``Edinetcode.zip`` をダウンロードし、
中の ``EdinetcodeDlInfo.csv`` を解析して 1 提出者 1 行の dict で返す。

書類一覧 API と異なり API キーは不要な静的ファイルのダウンロードで、
全件スナップショット（CSV は CP932・1 行目はメタ情報・2 行目がヘッダー）。

出典: https://disclosure2.edinet-fsa.go.jp/ （EDINETコードリスト）
"""

from __future__ import annotations

import csv
import io
import logging
import time
import urllib.error
import urllib.request
import zipfile

logger = logging.getLogger(__name__)

CODELIST_URL = (
    "https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip"
)
CSV_NAME = "EdinetcodeDlInfo.csv"
CSV_ENCODING = "cp932"

# CSV の列順（日本語ヘッダー）に対応する英語キー。全項目 VARCHAR で _source に
# 保持し、型付け・リネームは stg 層で行う（documents と同じ方針）。
COMPANY_FIELDS = [
    "edinet_code",  # ＥＤＩＮＥＴコード
    "submitter_type",  # 提出者種別
    "listing_status",  # 上場区分
    "consolidated",  # 連結の有無
    "capital",  # 資本金
    "fiscal_year_end",  # 決算日（"5月31日" 等の月日テキスト）
    "filer_name",  # 提出者名
    "filer_name_en",  # 提出者名（英字）
    "filer_name_kana",  # 提出者名（ヨミ）
    "address",  # 所在地
    "industry",  # 提出者業種
    "sec_code",  # 証券コード（末尾0付き5桁、非上場は空）
    "corporate_number",  # 提出者法人番号（13桁）
]


def fetch_company_master(
    *, max_retries: int = 5, timeout: int = 60, retry_wait: float = 4.0
) -> list[dict]:
    """EDINETコードリストを取得し、提出者ごとの行 dict のリストを返す。

    CSV は 1 行目がメタ情報（ダウンロード実行日・件数）、2 行目がヘッダー、
    3 行目以降がデータ。ヘッダー行は捨て、列順で COMPANY_FIELDS に対応づける。
    """
    text = _download_csv()
    reader = csv.reader(io.StringIO(text))
    rows: list[dict] = []
    for i, cols in enumerate(reader):
        if i < 2:  # 1行目=メタ情報, 2行目=ヘッダー
            continue
        if not cols:
            continue
        values = (cols + [""] * len(COMPANY_FIELDS))[: len(COMPANY_FIELDS)]
        rows.append({f: (v or None) for f, v in zip(COMPANY_FIELDS, values)})
    logger.info("fetched %d companies from code list", len(rows))
    return rows


def _download_csv() -> str:
    """ZIP をダウンロードし、中の CSV を CP932 デコードした文字列を返す。"""
    raw = _download(CODELIST_URL)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        with zf.open(CSV_NAME) as f:
            return f.read().decode(CSV_ENCODING)


def _download(
    url: str, *, max_retries: int = 5, timeout: int = 60, retry_wait: float = 4.0
) -> bytes:
    """一時的なエラーを指数バックオフでリトライしつつ URL の中身を取得する。"""
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "queria-dataset-edinet/1.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.URLError as e:
            if attempt < max_retries:
                wait = retry_wait * 2**attempt
                logger.warning(
                    "code list download failed (%s), retry %d/%d after %.1fs",
                    getattr(e, "reason", e),
                    attempt,
                    max_retries,
                    wait,
                )
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("failed to download EDINET code list")
