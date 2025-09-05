from sqlalchemy import create_engine, text
import pandas as pd

CONN_STR = 'postgresql+psycopg://postgres:eiacg@localhost:5432/bank'

# küçük bir DataFrame
df = pd.DataFrame({"a":[1,2,3], "b":[10,20,30]})

engine = create_engine(CONN_STR)
with engine.begin() as conn:
    conn.exec_driver_sql("DROP TABLE IF EXISTS bank.test_dump;")
df.to_sql('test_dump', engine, schema='bank', if_exists='append', index=False)

# say
with engine.begin() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM bank.test_dump;")).scalar()
print("Inserted rows:", n)
