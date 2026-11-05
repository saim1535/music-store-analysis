from sqlalchemy import create_engine
import pandas as pd 

#credentials
DB_USER="postgres"
DB_PASSWORD="admin123"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="music_store"


engine= create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

def run_query(query):
    return pd.read_sql(query,engine)