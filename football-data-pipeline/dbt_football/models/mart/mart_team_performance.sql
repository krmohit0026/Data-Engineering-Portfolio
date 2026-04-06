with match_facts as (
    select * from {{ ref('fct_matches') }}
)

select 
    home_team as team,
    count(*) as total_matches,
    avg(total_goals) as avg_goals_per_game,
    sum(case when match_result = 'HOME_WIN' then 1 else 0 end) as total_home_wins
from match_facts
group by 1
order by avg_goals_per_game desc