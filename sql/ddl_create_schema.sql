-- bank şeması ve temel tablolar
CREATE SCHEMA IF NOT EXISTS bank;

-- Ham veri (Give Me Some Credit kolon adları normalize)
CREATE TABLE IF NOT EXISTS bank.gmsc_raw (
    customer_id            BIGINT PRIMARY KEY,
    serious_dlqin_2yrs     INTEGER,     -- hedef: default (1) / non-default (0)
    revolving_utilization  NUMERIC,
    age                    INTEGER,
    num_30_59              INTEGER,
    debt_ratio             NUMERIC,
    monthly_income         NUMERIC,
    num_open_credit_lines  INTEGER,
    num_90                 INTEGER,
    num_real_estate_loans  INTEGER,
    num_60_89              INTEGER,
    num_dependents         INTEGER
);

-- Basit star şeması: müşteri boyutu
CREATE TABLE IF NOT EXISTS bank.dim_customer (
    customer_sk   BIGSERIAL PRIMARY KEY,
    customer_id   BIGINT UNIQUE NOT NULL,
    age_group     TEXT,
    dependents    INTEGER
);

-- Kredi başvurusu fakt tablosu
CREATE TABLE IF NOT EXISTS bank.fact_credit_application (
    app_sk                 BIGSERIAL PRIMARY KEY,
    customer_sk            BIGINT REFERENCES bank.dim_customer(customer_sk),
    serious_dlqin_2yrs     INTEGER,
    revolving_utilization  NUMERIC,
    debt_ratio             NUMERIC,
    monthly_income         NUMERIC,
    num_open_credit_lines  INTEGER,
    num_30_59              INTEGER,
    num_60_89              INTEGER,
    num_90                 INTEGER,
    num_real_estate_loans  INTEGER,
    created_at             TIMESTAMP DEFAULT now(),
    predicted_pd           NUMERIC    -- model çıktısını burada tutacağız
);
