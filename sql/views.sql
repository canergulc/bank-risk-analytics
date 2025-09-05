-- Gelir aralığına göre default oranı
CREATE OR REPLACE VIEW bank.vw_default_rate_by_income_bucket AS
WITH buckets AS (
  SELECT app_sk,
         CASE
           WHEN monthly_income IS NULL THEN 'Unknown'
           WHEN monthly_income < 2500 THEN '0-2.5k'
           WHEN monthly_income < 5000 THEN '2.5k-5k'
           WHEN monthly_income < 10000 THEN '5k-10k'
           ELSE '10k+'
         END AS income_bucket,
         serious_dlqin_2yrs
  FROM bank.fact_credit_application
)
SELECT income_bucket,
       COUNT(*) AS n,
       AVG(serious_dlqin_2yrs::NUMERIC) AS default_rate
FROM buckets
GROUP BY income_bucket
ORDER BY n DESC;

-- PD decile kalibrasyon görünümü (model sonrası predicted_pd kolonu ile çalışır)
CREATE OR REPLACE VIEW bank.vw_pd_deciles AS
SELECT decile,
       COUNT(*) AS n,
       AVG(serious_dlqin_2yrs::NUMERIC) AS observed_default_rate,
       AVG(predicted_pd) AS avg_predicted_pd
FROM (
  SELECT app_sk, serious_dlqin_2yrs, predicted_pd,
         NTILE(10) OVER (ORDER BY predicted_pd) AS decile
  FROM bank.fact_credit_application
  WHERE predicted_pd IS NOT NULL
) t
GROUP BY decile
ORDER BY decile;
