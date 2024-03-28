-- This query first finds tracts that are have met condition
-- It then searchs for adjoining tracts by looking for tracts that intersect
-- There are 224 census tracts with coal generators retired after 2009
-- There are 1750 cesus tracts that meet the coal closure conditions in section III
with tracts_intersect as (
    SELECT DISTINCT t.*
    FROM tracts t
    JOIN generators_spatial g ON ST_Intersects(t.geom, g.geom)
    WHERE g."Technology" = 'Conventional Steam Coal' 
    AND CAST("Retirement Year" AS int) >= 2009
)
SELECT distinct t.*
FROM tracts_intersect ti, tracts t
WHERE ST_Intersects(ti.geom, t.geom);