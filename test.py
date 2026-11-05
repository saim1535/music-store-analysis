from db_config import run_query

df= run_query(
    "SELECT table_name FROM information_schema.tables where table_schema ='public';"
)

print(df)