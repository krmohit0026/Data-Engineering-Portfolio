with standings as (
    select * from {{ ref('stg_standings') }}
)

select 
    team_name,
    league_code,
    season_year,
    points,
    position,
    played,
    goal_diff,
    case 
        when position = 1 then 'League Leader'
        when position <= 4 then 'Champions League Spot'
        when position >= 18 then 'Relegation Zone'
        else 'Mid-Table'
    end as league_status
from standings
order by league_code, position