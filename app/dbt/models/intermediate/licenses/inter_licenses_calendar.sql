-- Generate a reusable date spine.
with recursive dates(date_day) as (

    select (
        select min(date)
        from {{ ref('inter_state_licenses') }}
    )

    union all

    select date(date_day, '+1 day')
    from dates
    where date_day < (
        select max(date)
        from {{ ref('inter_state_licenses') }}
    )

)

select date_day
from dates