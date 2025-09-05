# notebooks/train_model.py
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score, f1_score

CONN_STR = "postgresql+psycopg://postgres:eiacg@localhost:5432/bank"

print("⏳ pulling features from DB...")
engine = create_engine(CONN_STR)
df = pd.read_sql("""
    SELECT app_sk, serious_dlqin_2yrs, revolving_utilization, debt_ratio, monthly_income,
           num_open_credit_lines, num_30_59, num_60_89, num_90, num_real_estate_loans
    FROM bank.fact_credit_application
""", engine)

# features / target
X = df[['revolving_utilization','debt_ratio','monthly_income','num_open_credit_lines',
        'num_30_59','num_60_89','num_90','num_real_estate_loans']].copy()
X = X.fillna(0.0)
y = df['serious_dlqin_2yrs'].astype(int).values

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Logistic Regression (scaled)
scaler = StandardScaler()
X_tr_s = scaler.fit_transform(X_tr)
X_te_s = scaler.transform(X_te)

lr = LogisticRegression(max_iter=300, n_jobs=None)
lr.fit(X_tr_s, y_tr)
proba_lr = lr.predict_proba(X_te_s)[:,1]
auc_lr = roc_auc_score(y_te, proba_lr)
f1_lr = f1_score(y_te, (proba_lr>=0.5).astype(int))

# XGBoost (tabular strong baseline)
xgb = XGBClassifier(
    n_estimators=400,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric='auc',
    n_jobs=4,
    random_state=42
)
xgb.fit(X_tr, y_tr)
proba_xgb = xgb.predict_proba(X_te)[:,1]
auc_xgb = roc_auc_score(y_te, proba_xgb)
f1_xgb = f1_score(y_te, (proba_xgb>=0.5).astype(int))

print({"AUC_LR": round(auc_lr,4), "F1_LR": round(f1_lr,4),
       "AUC_XGB": round(auc_xgb,4), "F1_XGB": round(f1_xgb,4)})

# seçilen model: XGB (genelde daha güçlü)
print("✅ training done, scoring full table...")
proba_full = xgb.predict_proba(X)[:,1]

# kolonu ekle (varsa dokunma)
with engine.begin() as conn:
    conn.exec_driver_sql("""
        ALTER TABLE bank.fact_credit_application
        ADD COLUMN IF NOT EXISTS predicted_pd NUMERIC;
    """)
# hızlı toplu UPDATE: geçici tablo + join ile
print("⬆️ writing predicted_pd back to DB (via temp table)...")
chunk_size = 50000
for i in range(0, len(df), chunk_size):
    sl = slice(i, min(i + chunk_size, len(df)))
    # iloc kullan: pozisyon bazlı dilimleme
    app_chunk = df.iloc[sl]['app_sk'].astype(int).to_numpy()
    pd_chunk = proba_full[sl].astype(float)

    # güvenlik: uzunluklar eşit olmalı
    assert len(app_chunk) == len(pd_chunk), (len(app_chunk), len(pd_chunk))

    chunk_df = pd.DataFrame({"app_sk": app_chunk, "pd": pd_chunk})

    with engine.begin() as conn:
        conn.exec_driver_sql("""
            DROP TABLE IF EXISTS temp_pred_pd;
            CREATE TEMP TABLE temp_pred_pd (
                app_sk INT,
                pd NUMERIC
            ) ON COMMIT DROP;
        """)
        chunk_df.to_sql("temp_pred_pd", conn, if_exists="append", index=False)
        conn.exec_driver_sql("""
            UPDATE bank.fact_credit_application AS f
            SET predicted_pd = t.pd
            FROM temp_pred_pd AS t
            WHERE f.app_sk = t.app_sk;
        """)
print("✅ predicted_pd written.")
