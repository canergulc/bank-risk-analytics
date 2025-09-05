import os, pandas as pd
p = r"data\raw\give_me_some_credit\cs-training.csv"
print("Exists:", os.path.exists(p))
df = pd.read_csv(p)
print("Shape:", df.shape)
print("Columns (first 6):", list(df.columns)[:6])
print(df.head(2).to_string(index=False))
