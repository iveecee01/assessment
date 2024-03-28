-- This query first finds tracts that have met condition
-- It then searchs for adjoining tracts by looking for tracts that intersect
-- There are 224 census tracts with coal generators retired after 2009
-- There are 1750 cesus tracts that meet the coal closure conditions in section III
WITH tracts_intersect AS (
    SELECT DISTINCT t.*
    FROM tracts t
    LEFT JOIN generators_spatial g ON ST_Intersects(t.geom, g.geom)
    WHERE g."Technology" = 'Conventional Steam Coal' 
    AND CAST(g."Retirement Year" AS int) >= 2009
)
SELECT count(DISTINCT t.*)
FROM tracts_intersect ti
JOIN tracts t ON ST_Intersects(ti.geom, t.geom);