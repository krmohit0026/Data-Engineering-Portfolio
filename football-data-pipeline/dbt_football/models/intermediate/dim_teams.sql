with teams as (
    select distinct 
        team_id, 
        team_name, 
        league_code
    from {{ ref('stg_standings') }}
)

select 
    {{ dbt_utils.generate_surrogate_key(['team_id', 'league_code']) }} as team_pk,
    * from teams