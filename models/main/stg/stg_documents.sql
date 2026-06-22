{{ config(materialized='view') }}

select
    r."docID" as doc_id,
    try_cast(r."seqNumber" as integer) as seq_number,
    r."edinetCode" as edinet_code,
    r."secCode" as sec_code,
    r."JCN" as corporate_number,
    r."filerName" as filer_name,
    r."fundCode" as fund_code,
    r."ordinanceCode" as ordinance_code,
    r."formCode" as form_code,
    r."docTypeCode" as doc_type_code,
    t.doc_type_name,
    try_cast(r."periodStart" as date) as period_start,
    try_cast(r."periodEnd" as date) as period_end,
    try_strptime(r."submitDateTime", '%Y-%m-%d %H:%M') as submit_datetime,
    cast(try_strptime(r."submitDateTime", '%Y-%m-%d %H:%M') as date) as submit_date,
    r."docDescription" as doc_description,
    r."issuerEdinetCode" as issuer_edinet_code,
    r."subjectEdinetCode" as subject_edinet_code,
    r."subsidiaryEdinetCode" as subsidiary_edinet_code,
    r."currentReportReason" as current_report_reason,
    r."parentDocID" as parent_doc_id,
    try_strptime(r."opeDateTime", '%Y-%m-%d %H:%M') as ope_datetime,
    r."withdrawalStatus" as withdrawal_status,
    (r."withdrawalStatus" <> '0') as is_withdrawn,
    r."docInfoEditStatus" as doc_info_edit_status,
    r."disclosureStatus" as disclosure_status,
    (r."xbrlFlag" = '1') as has_xbrl,
    (r."pdfFlag" = '1') as has_pdf,
    (r."attachDocFlag" = '1') as has_attach_doc,
    (r."englishDocFlag" = '1') as has_english_doc,
    (r."csvFlag" = '1') as has_csv,
    r."legalStatus" as legal_status
from {{ ref('raw_documents') }} as r
left join {{ ref('doc_types') }} as t
    on r."docTypeCode" = t.doc_type_code
