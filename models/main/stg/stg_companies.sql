{{ config(materialized='view') }}

select
    r.edinet_code,
    r.submitter_type,
    r.listing_status,
    (r.consolidated = '有') as is_consolidated,
    try_cast(r.capital as bigint) as capital,
    r.fiscal_year_end,
    r.filer_name,
    r.filer_name_en,
    r.filer_name_kana,
    r.address,
    r.industry,
    r.sec_code,
    r.corporate_number
from {{ ref('raw_companies') }} as r
