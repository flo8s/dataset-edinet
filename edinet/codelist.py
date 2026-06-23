"""EDINET コードリスト（提出者マスタ）・ファンドコードリスト（ファンドマスタ）取得。

EDINET が公開する 2 つのコードリスト ZIP をダウンロードし、中の CSV を
解析して 1 行 1 dict のリストで返す。

- EDINETコードリスト ``Edinetcode.zip`` → ``EdinetcodeDlInfo.csv``（提出者）
- ファンドコードリスト ``Fundcode.zip`` → ``FundcodeDlInfo.csv``（ファンド）

書類一覧 API と異なり API キーは不要な静的ファイルのダウンロードで、
全件スナップショット（CSV は CP932・1 行目はメタ情報・2 行目がヘッダー）。

出典: https://disclosure2.edinet-fsa.go.jp/ （EDINETコードリスト・ファンドコードリスト）
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
COMPANY_CSV_NAME = "EdinetcodeDlInfo.csv"
FUNDLIST_URL = (
    "https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Fundcode.zip"
)
FUND_CSV_NAME = "FundcodeDlInfo.csv"
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

FUND_FIELDS = [
    "fund_code",  # ファンドコード（G+5桁）
    "sec_code",  # 証券コード（ファンドは多くが空）
    "fund_name",  # ファンド名
    "fund_name_kana",  # ファンド名（ヨミ）
    "security_type",  # 特定有価証券区分名（内国投資信託受益証券 等）
    "specified_period_1",  # 特定期1（決算期の月日テキスト）
    "specified_period_2",  # 特定期2（月日テキスト。多くが空）
    "edinet_code",  # ＥＤＩＮＥＴコード（発行者＝運用会社。mart_companies と結合）
    "issuer_name",  # 発行者名
]


def fetch_company_master() -> list[dict]:
    """EDINETコードリストを取得し、提出者ごとの行 dict のリストを返す。"""
    rows = _fetch_codelist(CODELIST_URL, COMPANY_CSV_NAME, COMPANY_FIELDS)
    logger.info("fetched %d companies from code list", len(rows))
    return rows


def fetch_fund_master() -> list[dict]:
    """ファンドコードリストを取得し、ファンドごとの行 dict のリストを返す。"""
    rows = _fetch_codelist(FUNDLIST_URL, FUND_CSV_NAME, FUND_FIELDS)
    logger.info("fetched %d funds from fund code list", len(rows))
    return rows


def _fetch_codelist(url: str, csv_name: str, fields: list[str]) -> list[dict]:
    """コードリスト ZIP を取得し、列順で fields に対応づけた行 dict を返す。

    CSV は 1 行目がメタ情報（ダウンロード実行日・件数）、2 行目がヘッダー、
    3 行目以降がデータ。ヘッダー行は捨て、列順で fields に対応づける。
    """
    text = _download_csv(url, csv_name)
    rows: list[dict] = []
    for i, cols in enumerate(csv.reader(io.StringIO(text))):
        if i < 2:  # 1行目=メタ情報, 2行目=ヘッダー
            continue
        if not cols:
            continue
        values = (cols + [""] * len(fields))[: len(fields)]
        rows.append({f: (v or None) for f, v in zip(fields, values)})
    return rows


def _download_csv(url: str, csv_name: str) -> str:
    """ZIP をダウンロードし、中の CSV を CP932 デコードした文字列を返す。"""
    raw = _download(url)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        with zf.open(csv_name) as f:
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
