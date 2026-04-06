with raw_matches as (
    select * from {{ source('football_raw', 'matches') }}
)

select
    raw_data:id::int as match_id,
    raw_data:competition_code::string as league_code,
    raw_data:season_year::int as season_year,
    raw_data:utcDate::timestamp_tz as match_date,
    raw_data:status::string as match_status,
    raw_data:home_team::string as home_team,
    raw_data:away_team::string as away_team,
    raw_data:home_score::int as home_score,
    raw_data:away_score::int as away_score
from raw_matches