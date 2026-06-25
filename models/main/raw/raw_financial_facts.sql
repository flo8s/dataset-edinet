{{ config(materialized='view') }}

select *
from {{ source('edinet_source', 'financial_facts') }}
