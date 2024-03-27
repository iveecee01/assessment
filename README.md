#### Sample scripts showing etl for adding census tracts and EIA retired generator data

Scripts assumes postgresql is already installed

analysis.sql writes a sample script to highlight census tracts(based only on retired generators) 
that qualify for tax credit bonus as defined in [section 3](https://energycommunities.gov/energy-community-tax-credit-bonus/) of the energy communities definition.

Results of the analysis show that:
1. 224 census tracts directly contain retired generators
2. 1526 cenus tracts are adjoining tracts
3. A total of 1750 census tracts qualify for the tax credit bonus based on these assumptions
