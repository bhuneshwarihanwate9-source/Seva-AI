# Seva-AI

AI-powered government scheme assistant that helps citizens discover eligible schemes, understand benefits, and prepare required documents.

---

## Data Pipeline (MySQL)

The data pipeline loads scheme records from `Data/indian_government_schemes.csv`, cleans them, and imports them into a MySQL database for the eligibility engine.

### Folder structure

```
backend/
└── data_pipeline/
    ├── clean_data.py      # CSV cleaning and normalization
    ├── load_to_mysql.py   # MySQL database creation and import
    ├── config.py          # Environment-based configuration
    └── schema.sql         # MySQL table definition
```

### Prerequisites

1. **Python 3.10+** with project dependencies installed:

   ```bash
   pip install -r requirements.txt
   ```

2. **MySQL Server 8.x** (or compatible) running locally or remotely.

3. A MySQL user with permission to create databases and tables.

### Configure environment (`.env`)

Copy the example file and edit your credentials:

```bash
cp .env.example .env
```

Example `.env`:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=seva_ai
INSERT_BATCH_SIZE=500
```

| Variable | Description | Default |
|----------|-------------|---------|
| `MYSQL_HOST` | MySQL host | `localhost` |
| `MYSQL_PORT` | MySQL port | `3306` |
| `MYSQL_USER` | MySQL username | `root` |
| `MYSQL_PASSWORD` | MySQL password | *(empty)* |
| `MYSQL_DATABASE` | Target database name | `seva_ai` |
| `INSERT_BATCH_SIZE` | Rows per batch insert | `500` |

### Create the database

The import script creates the database automatically. You can also create it manually:

```sql
CREATE DATABASE IF NOT EXISTS seva_ai
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

### Run the pipeline

**Step 1 — Clean the raw CSV**

From the project root:

```bash
python backend/data_pipeline/clean_data.py
```

This produces `Data/cleaned_schemes.csv` with:

- Normalized gender, state, and category values
- Placeholder values removed (`benefit_value_numeric = 1` → NULL)
- Duplicate `scheme_id` rows removed
- A computed `confidence_score` (0–1) per scheme

**Step 2 — Import into MySQL**

```bash
python backend/data_pipeline/load_to_mysql.py
```

This will:

1. Connect to MySQL using `.env` credentials
2. Create database `seva_ai` (if missing)
3. Execute `schema.sql` (table + indexes)
4. Truncate and reload `schemes` from `Data/cleaned_schemes.csv`
5. Print progress logs and verification stats

### Expected output

After both commands succeed you should have:

| Artifact | Description |
|----------|-------------|
| `Data/cleaned_schemes.csv` | Cleaned, normalized scheme data |
| MySQL database `seva_ai` | Ready for queries |
| Table `schemes` | ~4,700 rows populated |
| Indexes | `state`, `category`, `confidence_score` |

Verify in MySQL:

```sql
USE seva_ai;
SELECT COUNT(*) FROM schemes;
SELECT scheme_id, scheme_name, state, category, confidence_score
FROM schemes
ORDER BY confidence_score DESC
LIMIT 10;
```

### Confidence score

Each scheme receives a `confidence_score` between **0.0000** and **1.0000**:

| Component | Weight | Source |
|-----------|--------|--------|
| Eligibility verified | 40% | `eligibility_verified` flag in raw CSV |
| Structured eligibility | 35% | Coverage of age, income, occupation, category, disability, gender |
| Benefit availability | 25% | Numeric benefit value or benefit summary text |

Higher scores indicate schemes more suitable for automated eligibility matching.

---

## Project structure (overview)

```
Seva-AI/
├── backend/data_pipeline/   # Data cleaning + MySQL import
├── Backend/                 # FastAPI application (API)
├── Frontend/                # Streamlit UI
├── AI/                      # Chatbot module
├── Translation/             # Translation module
└── Data/                    # Scheme datasets
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Access denied for user` | Check `MYSQL_USER` / `MYSQL_PASSWORD` in `.env` |
| `Can't connect to MySQL server` | Ensure MySQL is running; verify `MYSQL_HOST` and `MYSQL_PORT` |
| `Cleaned CSV not found` | Run `clean_data.py` before `load_to_mysql.py` |
| `Raw CSV not found` | Ensure `Data/indian_government_schemes.csv` exists |
