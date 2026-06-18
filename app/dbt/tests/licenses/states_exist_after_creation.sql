--validates the forward-fill.
with gaps as (

    select
        license_id,
        date,

        lag(date) over (
            partition by license_id
            order by date
        ) as previous_date

    from {{ ref('inter_licenses_daily_states') }}

)

select *
from gaps
where datediff(day, previous_date, date) > 1