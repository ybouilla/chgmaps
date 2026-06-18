-- test: No dates before license creation
select
    d.license_id,
    d.date,
    l.creation_date

from {{ ref('inter_licenses_daily_states') }} d

join {{ ref('stg_initial_licenses') }} l
    on d.license_id = l.license_id

where d.date < l.creation_date