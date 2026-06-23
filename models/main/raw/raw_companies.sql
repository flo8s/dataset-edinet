{{ config(materialized='view') }}

select *
from {{ source('edinet_source', 'companies') }}
