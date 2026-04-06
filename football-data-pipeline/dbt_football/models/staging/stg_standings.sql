with raw_data as (
    select * from {{ source('football_raw', 'standings') }}
),

flattened as (
    select
        raw_data:competition_code::string as league_code,
        raw_data:season_year::int as season_year,
        raw_data:ingestion_timestamp::timestamp_tz as ingested_at,
        table_element.value:team_id::int as team_id,
        table_element.value:team_name::string as team_name,
        table_element.value:position::int as position,
        table_element.value:playedGames::int as played,
        table_element.value:won::int as won,
        table_element.value:draw::int as draw,
        table_element.value:lost::int as lost,
        table_element.value:points::int as points,
        table_element.value:goalsFor::int as goals_for,
        table_element.value:goalsAgainst::int as goals_against,
        table_element.value:goalDifference::int as goal_diff
    from raw_data,
    -- THE FIX IS HERE: Changed from raw_data:raw_data:table to raw_data:table
    lateral flatten(input => raw_data:table) table_element
)

select * from flattened