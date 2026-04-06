with matches as (
    select * from {{ ref('stg_matches') }}
)

select 
    *,
    (home_score + away_score) as total_goals,
    case 
        when home_score > away_score then 'HOME_WIN'
        when home_score < away_score then 'AWAY_WIN'
        else 'DRAW'
    end as match_result,
    case 
        when home_score > away_score then 3
        when home_score = away_score then 1
        else 0
    end as home_points_earned
from matches