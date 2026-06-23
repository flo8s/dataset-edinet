{{ config(materialized='view') }}

select
    r.fund_code,
    r.sec_code,
    r.fund_name,
    r.fund_name_kana,
    r.security_type,
    r.specified_period_1,
    r.specified_period_2,
    r.edinet_code,
    r.issuer_name
from {{ ref('raw_funds') }} as r
