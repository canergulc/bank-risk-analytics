-- Performans için temel indeksler
CREATE INDEX IF NOT EXISTS idx_fact_customer_sk
  ON bank.fact_credit_application(customer_sk);

CREATE INDEX IF NOT EXISTS idx_fact_default
  ON bank.fact_credit_application(serious_dlqin_2yrs);

CREATE INDEX IF NOT EXISTS idx_fact_income
  ON bank.fact_credit_application(monthly_income);
