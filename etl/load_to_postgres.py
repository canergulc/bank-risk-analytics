import pandas as pd, numpy as np
from sqlalchemy import create_engine, text

CSV_PATH = r'data\raw\give_me_some_credit\cs-training.csv'
CONN_STR = 'postgresql+psycopg://postgres:eiacg@localhost:5432/bank'

rename_map = {
    'SeriousDlqin2yrs': 'serious_dlqin_2yrs',
    'RevolvingUtilizationOfUnsecuredLines': 'revolving_utilization',
    'age': 'age',
    'NumberOfTime30-59DaysPastDueNotWorse': 'num_30_59',
    'DebtRatio': 'debt_ratio',
    'MonthlyIncome': 'monthly_income',
    'NumberOfOpenCreditLinesAndLoans': 'num_open_credit_lines',
    'NumberOfTimes90DaysLate': 'num_90',
    'NumberRealEstateLoansOrLines': 'num_real_estate_loans',
    'NumberOfTime60-89DaysPastDueNotWorse': 'num_60_89',
    'NumberOfDependents': 'num_dependents'
}

print("Reading CSV:", CSV_PATH)
df = pd.read_csv(CSV_PATH)
print("Original shape:", df.shape)

# ID kolonu bazen farklı olabiliyor: 'Unnamed: 0' / 'Id'
id_col = None
for cand in ('Unnamed: 0','Id','id'):
    if cand in df.columns:
        id_col = cand
        break

if id_col:
    df = df.rename(columns={id_col: 'customer_id'})
else:
    # fallback: sırayla ver
    df.insert(0, 'customer_id', range(1, len(df) + 1))

df = df.rename(columns=rename_map)

missing = [c for c in rename_map.values() if c not in df.columns]
if missing:
    raise RuntimeError(f"Eksik kolon(lar): {missing}. CSV kolonlarını kontrol et.")

df['monthly_income'] = df['monthly_income'].replace(0, np.nan)

print("Transformed shape:", df.shape)
print("Head:")
print(df.head(3).to_string(index=False))

engine = create_engine(CONN_STR)

# 1) gmsc_raw
cols_raw = ['customer_id','serious_dlqin_2yrs','revolving_utilization','age','num_30_59',
            'debt_ratio','monthly_income','num_open_credit_lines','num_90',
            'num_real_estate_loans','num_60_89','num_dependents']

#df[cols_raw].to_sql('gmsc_raw', engine, schema='bank', if_exists='append', index=False)
#print("Inserted into bank.gmsc_raw:", len(df))

# 2) dim_customer (num_dependents -> dependents)
dim = df[['customer_id', 'num_dependents']].copy()
dim = dim.rename(columns={'num_dependents': 'dependents'})
dim['age_group'] = pd.cut(
    df['age'],
    bins=[0,25,35,45,60,120],
    labels=['18-25','26-35','36-45','46-60','60+']
)
dim = dim[['customer_id','age_group','dependents']]
dim.to_sql('dim_customer', engine, schema='bank', if_exists='append', index=False)
print("Inserted into bank.dim_customer:", len(dim))


# 3) fact
with engine.begin() as conn:
    conn.exec_driver_sql("""
        INSERT INTO bank.fact_credit_application (
            customer_sk, serious_dlqin_2yrs, revolving_utilization, debt_ratio,
            monthly_income, num_open_credit_lines, num_30_59, num_60_89, num_90,
            num_real_estate_loans
        )
        SELECT dc.customer_sk,
               gr.serious_dlqin_2yrs, gr.revolving_utilization, gr.debt_ratio,
               gr.monthly_income, gr.num_open_credit_lines, gr.num_30_59, gr.num_60_89,
               gr.num_90, gr.num_real_estate_loans
        FROM bank.gmsc_raw gr
        JOIN bank.dim_customer dc ON dc.customer_id = gr.customer_id
        WHERE NOT EXISTS (
            SELECT 1 FROM bank.fact_credit_application f
            WHERE f.customer_sk = dc.customer_sk
        );
    """)
print("Inserted into bank.fact_credit_application (via SELECT). Done.")
