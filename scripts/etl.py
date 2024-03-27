import subprocess
from getpass import getpass

from pathlib import Path
import requests

import pandas as pd
import zipfile
import py7zr
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import psycopg2


PASSWD = getpass('Type password: ')
HOME = Path.cwd().parent.joinpath("data")
HOME.mkdir(parents=True, exist_ok=True)

def run_query(dbname, query):
    """Runs query in a database

    Parameters
    ----------
    dbname : str
        name of the database
    query : str | list
        query to run
    """
    connection = psycopg2.connect(
        database = dbname,
        user = 'postgres',
        password = PASSWD,
        host = 'localhost',
        port = '5432'
    )

    cursor = connection.cursor()
    if isinstance(query, list):
        for q in query:
            cursor.execute(q)
    else:
        cursor.execute(query)
    connection.commit()


def download_file(url, local_path):
    """Download file from url and save to path

    Parameters
    ----------
    url : str
        url to request data from
    local_path : str
        path to save data to
    """

    with requests.get(url, stream=True) as r:
        with open(str(local_path), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def extract_7z(local_path):
    """Extract 7z zip files

    Parameters
    ----------
    local_path : str
        Path to .7z file
    """
    folder = local_path.stem
    with py7zr.SevenZipFile(str(local_path), mode='r') as z:
        z.extractall(str(local_path.parent.joinpath(folder)))

def extract_zip(local_path):
    """Extract zip files

    Parameters
    ----------
    local_path : str
        path to zip file
    """
    folder = local_path.stem
    with zipfile.ZipFile(str(local_path), "r") as z:
            z.extractall(str(local_path.parent.joinpath(folder)))


def initialize_db(dbname):
    """Create database and enable postgis extension

    Parameters
    ----------
    dbname : str
        name of database
    """
    subprocess.call(f'psql -U postgres -w -c "DROP DATABASE {dbname}"', shell=True)
    subprocess.call(f'psql -U postgres -w -c "CREATE DATABASE {dbname}"', shell=True)
    subprocess.call(f'psql -U postgres -w -d {dbname} -c \
        "CREATE EXTENSION IF NOT EXISTS postgis;"', shell=True)


def create_db_from_gdb(dbname, path, layer_name, nlt):
    """Write table to database from geodatabase source

    Parameters
    ----------
    dbname : str
        name of database
    path : str
        path to geodatabase
    layer_name : str
        name of the geodatabase layer
    nlt : str
        layer type (e.g. MULTIPOLYGON)
    """
    command = ['ogr2ogr', "-f", "PostgreSQL", 
               f"PG:dbname={dbname} user=postgres password={PASSWD} host=localhost port=5432",
               path, "-nln", layer_name, '-nlt', nlt, "-lco",  "GEOMETRY_NAME=geom"]
    subprocess.run(command)


def create_db_from_df(df, dbname, table_name, if_exists):
    """Write table to database from pandas dataframe

    Parameters
    ----------
    df : pandas.DataFrame
        pandas dataframe
    dbname : str
        name of database
    table_name : str
        name of table being created in database
    if_exists : str
        handling existing table (e.g. 'replace')
    """
    encoded_pass = quote_plus(PASSWD)
    engine = create_engine(f"postgresql://postgres:{encoded_pass}@localhost:5432/{dbname}")
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)
    engine.dispose()


def add_census_db(dbname):
    """Downloads census data from source extracts the 7z data and loads in database

    Parameters
    ----------
    dbname : str
        name of database
    """
    census_url = "https://www.arcgis.com/sharing/rest/content/items/ca1316dba1b442d99cb76bc2436b9fdb/data"
    local_path = HOME.joinpath("USA_Census_Tract_Boundaries.lpk")
    download_file(census_url, local_path)
    extract_7z(local_path)
    gdb_path = HOME.joinpath("USA_Census_Tract_Boundaries/v10/tracts.gdb")
    create_db_from_gdb(dbname, str(gdb_path), 'tracts', 'MULTIPOLYGON')


def add_eia_db(dbname):
    """Downloads eia data from source extracts the zip data and loads in database

    Parameters
    ----------
    dbname : str
        name of database
    """
    local_path = HOME.joinpath("eia8602022.zip")
    eia_url = "https://www.eia.gov/electricity/data/eia860/xls/eia8602022.zip"
    download_file(eia_url, local_path)
    extract_zip(local_path)
    
    generator_path = HOME.joinpath("eia8602022/3_1_Generator_Y2022.xlsx")
    df_retired = pd.read_excel(generator_path, sheet_name="Retired and Canceled", skiprows=1)
    create_db_from_df(df_retired, dbname, 'generators', 'replace')

    plant_path = HOME.joinpath("eia8602022/2___Plant_Y2022.xlsx")
    df_plants =  pd.read_excel(plant_path, sheet_name="Plant", skiprows=1)
    create_db_from_df(df_plants, dbname, 'plants', 'replace')
    
    #add geom to generators
    null_ry = """UPDATE generators set "Retirement Year" = null WHERE "Retirement Year" = ' ' """
    null_long = """UPDATE plants set "Longitude" = null WHERE "Longitude" = ' ' """
    null_lat = """UPDATE plants set "Latitude" = null WHERE "Latitude" = ' ' """
    add_geom = """CREATE TABLE generators_spatial AS
	                SELECT g.*, ST_SetSRID(ST_Point(CAST(p."Longitude" AS double precision) , 
                        CAST(p."Latitude" AS double precision)), 4326) As geom 
	                FROM generators g
	                LEFT JOIN plants p ON CAST(g."Plant Code" AS INT) = 
                                        CAST(p."Plant Code" AS INT)"""
    run_query(dbname, [null_ry, null_long, null_lat, add_geom])


def main():
    """Extracts and loads census and eia data into database
    """
    dbname = 'data_store'
    initialize_db(dbname)
    add_census_db(dbname)
    add_eia_db(dbname)
    
if __name__ == "__main__":
    main()




