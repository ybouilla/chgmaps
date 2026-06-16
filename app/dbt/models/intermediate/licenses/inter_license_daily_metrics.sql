--Aggregate counts and revenue.

select
    date,
    type,

    sum(case when renewable = 1 then 1 else 0 end)
        as active_license_count,

    sum(case when renewable = 0 then 1 else 0 end)
        as inactive_license_count,

    sum(case when renewable = 1 then price else 0 end)
        as active_license_price

from {{ ref('inter_licenses_daily_states') }}

group by date, type