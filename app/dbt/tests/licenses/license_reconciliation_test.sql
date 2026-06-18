with latest_day as (

    select max(date) as max_date
    from {{ ref('inter_licenses_daily_states') }}

),

snapshot_count as (

    select count(*) cnt

    from {{ ref('inter_licenses_daily_states') }}
    where date = (select max_date from latest_day)

),

license_count as (

    select count(*) cnt
    from {{ ref('stg_initial_licenses') }}

)

select *
from snapshot_count s
cross join license_count l
where s.cnt <> l.cnt