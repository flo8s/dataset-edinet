## データ出典

[金融庁 EDINET](https://disclosure2.edinet-fsa.go.jp/) の書類一覧 API（documents.json, Version 2）から取得した開示書類のメタデータです。
有価証券報告書・四半期報告書・半期報告書・臨時報告書・大量保有報告書・公開買付関連書類などの提出書類を、1行1書類で収録しています。

書類本文や財務数値（XBRL/CSV）は含みません。提出書類の一覧（インデックス）に絞っています。

閲覧可能期間は書類種別ごとに最長10年（縦覧期間＋延長期間）で、それを過ぎた書類は API から取得できなくなります。

## テーブル: mart_documents

提出書類のメタデータ。提出者法人番号（corporate_number）を持つため、houjin_bangou / gbizinfo と法人番号で結合できます。

主なカラム:

- doc_id: 書類管理番号（EDINET が書類ごとに採番する一意の番号）
- seq_number: ファイル日付ごとの連番
- edinet_code: 提出者 EDINET コード
- sec_code: 提出者証券コード（上場会社のみ）
- corporate_number: 提出者法人番号（13桁。houjin_bangou / gbizinfo と結合可能）
- filer_name: 提出者名
- fund_code: ファンドコード
- ordinance_code / form_code: 府令コード / 様式コード
- doc_type_code / doc_type_name: 書類種別コード / 書類種別名（有価証券報告書、四半期報告書、大量保有報告書 等）
- period_start / period_end: 対象期間（自 / 至）
- submit_datetime / submit_date: 提出日時 / 提出日
- doc_description: 提出書類概要
- issuer_edinet_code / subject_edinet_code / subsidiary_edinet_code: 発行会社 / 対象 / 子会社 EDINET コード
- current_report_reason: 臨時報告書の提出事由
- parent_doc_id: 親書類管理番号（訂正・変更報告書等の基となる書類）
- ope_datetime: 書類情報修正の操作日時
- withdrawal_status / is_withdrawn: 取下区分 / 取下げ書類か
- doc_info_edit_status: 書類情報修正区分
- disclosure_status: 開示不開示区分
- has_xbrl / has_pdf / has_attach_doc / has_english_doc / has_csv: 各ファイルの有無
- legal_status: 縦覧区分（1=縦覧中, 2=延長期間中, 0=閲覧期間満了）

## 更新

毎日 EDINET の書類一覧 API を日付単位で取得します。未取得日のみ取得し（進捗は `_source.fetch_progress` に永続化）、直近7日分は書類情報修正・取下げを取り込むため毎回再取得します。

1回の実行で取得する日数には上限（`EDINET_MAX_DATES_PER_RUN`、既定 1000）を設けています。全期間バックフィルを1回で走らせると CI のジョブ上限を超えるため、毎回 build + push まで完走させ、進捗を `fetch_progress` に残します。`fdl pull` が次回その進捗を取り込むので、日次実行で数日かけて履歴（新しい日付から順）が埋まります。

遡及取得の開始日は環境変数 `EDINET_BACKFILL_START`（既定 `2016-01-01`）で調整できます。ローカル検証では直近に絞ると初回ビルドが軽くなります。

## クレジット

このサービスは、金融庁 EDINET の書類一覧 API を使用していますが、提供情報の最新性、正確性、完全性等が保証されたものではありません。

## ライセンス

[金融庁 EDINET 利用規約](https://disclosure2.edinet-fsa.go.jp/)
