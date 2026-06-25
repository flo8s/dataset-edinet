{{ config(materialized='view') }}

-- 書類取得 API type=5 CSV の縦持ち財務ファクト（生に忠実）。
-- 全 csv_type・全行・全列を保持し、型付けと結合キー付与のみ行う。
-- value は生のまま残し、利便のため numeric_value を追加で併記する。
with docs as (
    -- documents は同一 doc_id が複数の取得日に現れることがある（一覧の再掲）。
    -- 結合でファクトが増殖しないよう doc_id 単位に 1 行へ畳む。
    select *
    from {{ ref('stg_documents') }}
    qualify row_number() over (partition by doc_id order by submit_datetime desc) = 1
)

select
    f.doc_id,
    d.edinet_code,
    d.sec_code,
    d.corporate_number,
    d.filer_name,
    d.doc_type_code,
    d.period_end,
    d.submit_date,
    d.doc_description,
    f.element_id,
    f.item_name,
    f.context_id,
    f.relative_year,
    f.consolidated_individual,
    f.period_instant,
    f.unit_id,
    f.unit,
    f.value,
    try_cast(f.value as decimal(38, 4)) as numeric_value,
    f._csv_type as csv_type,
    f._row_seq as row_seq
from {{ ref('raw_financial_facts') }} as f
left join docs as d
    on f.doc_id = d.doc_id
