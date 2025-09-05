# Kredi Riski Analitiği (PD Modeli)

**Uçtan uca** kredi riski çalışması: Python **ETL** → **PostgreSQL** veri ambarı → PD **model eğitimi** → **kalibrasyon** → **Power BI** dashboard.

## İçerik
- **Veri**: Give Me Some Credit (150.000 başvuru)
- **DWH**: `bank` şeması — `gmsc_raw`, `dim_customer`, `fact_credit_application`, `vw_pd_deciles`
- **Model**: Logistic Regression & XGBoost (AUC ≈ 0.863), skorlar `predicted_pd` kolonu olarak yazılır
- **Dashboard**: KPI’lar, Risk Band dağılımı, kalibrasyon tablosu, **Top 50** yüksek risk listesi

---

## Proje Yapısı
```
dashboard/                      # Power BI dosyaları (PBIX/PDF)
data/raw/give_me_some_credit/   # cs-training.csv (repo dışında tutulması önerilir)
etl/                             # ETL scriptleri (pandas, SQLAlchemy)
notebooks/                       # Model eğitimi (scikit-learn, xgboost)
sql/                             # Şema, index ve view DDL’leri
requirements.txt
```

## Hızlı Başlangıç

> Önkoşullar: Python 3.8+, PostgreSQL 15+, Power BI Desktop (Windows).

### 1) Sanal ortam ve paketler
```bash
py -m venv .venv
.\.venv\Scriptsctivate
pip install -r requirements.txt
```

### 2) Veritabanı ve şema
```bash
"C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres -c "CREATE DATABASE bank;"
"C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres -d bank -f sql\ddl_create_schema.sql
"C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres -d bank -f sql\ddl_indexes.sql
"C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres -d bank -f sql\views.sql
```

### 3) Veri dosyası
`cs-training.csv` dosyasını `data/raw/give_me_some_credit/` klasörüne koyun.

### 4) ETL
```bash
python etl\load_to_postgres.py
```

### 5) Model eğitimi
```bash
python notebooks\train_model.py
```
> Tamamlandığında `fact_credit_application.predicted_pd` doldurulur ve kalibrasyon çıktıları `vw_pd_deciles` üzerinden doğrulanabilir.

### 6) Power BI
- **Veri Al → PostgreSQL** (Sunucu: `localhost`, Veritabanı: `bank`)
- Yükle: `fact_credit_application`, `dim_customer`, `vw_pd_deciles`
- İlişki: `Dim_Customer[customer_sk] 1 → * Fact_Applications[customer_sk]`

#### Önerilen Ölçüler (DAX)
```DAX
Başvuru Sayısı    = COUNTROWS(Fact_Applications)
Temerrüt Oranı    = DIVIDE(SUM(Fact_Applications[serious_dlqin_2yrs]), [Başvuru Sayısı])
Ortalama PD       = AVERAGE(Fact_Applications[predicted_pd])
Yüksek Risk Sayısı= CALCULATE([Başvuru Sayısı], Fact_Applications[predicted_pd] >= 0.70)
Yüksek Risk Oranı = DIVIDE([Yüksek Risk Sayısı], [Başvuru Sayısı])
Kalibrasyon Farkı = [Ortalama PD] - [Temerrüt Oranı]
```

#### Risk bandı sütunu
```DAX
Risk Band TR =
VAR p = Fact_Applications[predicted_pd]
RETURN IF(ISBLANK(p),"Bilinmiyor", IF(p>=0.70,"Yüksek", IF(p>=0.30,"Orta","Düşük")))
```
Sıralama için:
```DAX
Risk Band Sıra =
VAR p = Fact_Applications[predicted_pd]
RETURN SWITCH(TRUE(), ISBLANK(p),4, p>=0.70,3, p>=0.30,2, 1)
```
`Risk Band TR` → **Sütuna göre sırala** = `Risk Band Sıra`.

---

## Faydalı SQL
```sql
SELECT COUNT(*) FROM bank.fact_credit_application;
SELECT * FROM bank.vw_pd_deciles ORDER BY decile;
```

## Notlar
- `data/` klasörü büyük dosyalar içerebilir; repo dışında tutmanız önerilir (bkz. `.gitignore`).
- Veritabanı kimlik bilgilerini kodla paylaşmayın; yerel ortamda girin.
- Bu proje eğitim/demonstrasyon amaçlıdır; gerçek müşteri verisi içermez.
