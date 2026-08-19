# Seva-AI — Project Audit Report

**Date:** 19 August 2026  
**Auditor:** Lead Backend Engineer  
**Scope:** Complete inspection of the Seva-AI repository — no code was modified, no schema was altered, no migrations were created.

---

## 1. Project Structure

### Complete Folder Tree

```
Seva-AI/
├── .env.example              (245 bytes)   — MySQL env-var template
├── .gitignore                (4,846 bytes) — Standard Python gitignore
├── README.md                 (4,343 bytes) — Data-pipeline README
├── analysis_report.md        (19,945 bytes)— Dataset analysis (design doc)
├── architecture_plan.md      (22,827 bytes)— Full architecture & product plan
├── cleaning_plan.md          (13,340 bytes)— Data cleaning plan (design doc)
├── inspect_data.py           (8,271 bytes) — Temporary inspection script (not part of project)
├── requirements.txt          (2,172 bytes) — Full pip freeze lockfile
├── AI/
│   └── chatbot.py            (0 bytes)     — Empty stub
├── Backend/
│   ├── __init__.py           (32 bytes)    — Package docstring only
│   ├── main.py               (137 bytes)   — FastAPI app + single health route
│   ├── routes.py             (0 bytes)     — Empty stub
│   └── data_pipeline/
│       ├── __init__.py       (73 bytes)    — Package docstring only
│       ├── clean_data.py     (10,448 bytes)— CSV cleaning & normalization
│       ├── config.py         (1,948 bytes) — Environment-based config
│       ├── load_to_mysql.py  (7,311 bytes) — MySQL database creation & import
│       └── schema.sql        (1,372 bytes) — MySQL table definition
├── Data/
│   └── indian_government_schemes.csv (5,871,301 bytes) — 4,702 schemes, 29 columns
├── Feature/                  — Empty directory
├── Frontend/
│   └── app.py                (93 bytes)    — Streamlit title + tagline only
├── Translation/
│   └── translator.py         (0 bytes)     — Empty stub
└── Voice/                    — Empty directory
```

### Purpose of Each Folder

| Folder | Purpose |
|--------|---------|
| `Backend/` | FastAPI application — API routes, models, services, database layer |
| `Backend/data_pipeline/` | Data ingestion pipeline — CSV cleaning, MySQL import, schema |
| `Frontend/` | Streamlit citizen-facing UI |
| `AI/` | Conversational AI / chatbot layer |
| `Translation/` | Multilingual translation support |
| `Voice/` | Voice I/O (speech-to-text, text-to-speech) |
| `Feature/` | Reserved for feature modules (empty) |
| `Data/` | Scheme datasets (CSV) |

### Purpose of Important Files

| File | Purpose |
|------|---------|
| `Backend/main.py` | FastAPI application entry point |
| `Backend/routes.py` | API route definitions (empty) |
| `Backend/data_pipeline/config.py` | Loads MySQL credentials from `.env`, defines paths |
| `Backend/data_pipeline/clean_data.py` | Cleans raw CSV → `Data/cleaned_schemes.csv` |
| `Backend/data_pipeline/load_to_mysql.py` | Creates MySQL DB, applies schema, imports cleaned CSV |
| `Backend/data_pipeline/schema.sql` | MySQL `schemes` table DDL |
| `Data/indian_government_schemes.csv` | Raw government scheme dataset (4,702 rows) |
| `Frontend/app.py` | Streamlit UI entry point (stub) |
| `requirements.txt` | Full pip freeze (includes Windows-only packages) |
| `architecture_plan.md` | Design document — full product architecture |
| `analysis_report.md` | Design document — dataset analysis |
| `cleaning_plan.md` | Design document — data cleaning strategy |

---

## 2. Backend Analysis

### `Backend/main.py` (137 bytes)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | FastAPI application entry point |
| **Status** | Minimal — single health-check route |
| **Implementation** | Creates `FastAPI()` instance, defines `GET /` returning `{"message": "Seva-AI Backend Running properly!"}` |
| **Missing** | No route inclusion, no database startup, no middleware, no CORS, no dependency injection, no error handlers |

### `Backend/routes.py` (0 bytes)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | API route definitions |
| **Status** | Empty — no routes defined |
| **Missing** | All business endpoints (profile, eligibility, schemes, benefits, documents, readiness, opportunities) |

### `Backend/__init__.py` (32 bytes)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Package marker |
| **Status** | Docstring only |
| **Missing** | No exports, no shared utilities |

### `Backend/data_pipeline/config.py` (1,948 bytes)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Central configuration — loads `.env`, defines MySQL connection params and file paths |
| **Status** | Working — uses `python-dotenv` to load env vars |
| **Implementation** | `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` from env; `RAW_CSV_PATH`, `CLEANED_CSV_PATH`, `SCHEMA_SQL_PATH` as `Path` objects; `mysql_url()` builds SQLAlchemy URL |
| **Missing** | No connection pooling config, no retry logic, no validation of required env vars |

### `Backend/data_pipeline/clean_data.py` (10,448 bytes)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Clean and normalize raw CSV for MySQL ingestion |
| **Status** | Working — produces `Data/cleaned_schemes.csv` |
| **Implementation** | Loads raw CSV, removes duplicates, normalizes gender/state/category, coalesces age/income, computes confidence score, validates mandatory fields, writes cleaned CSV |
| **Missing** | Does not populate `bpl_required`, `marital_status_required`, `is_national_scheme`, `issuing_authority`, `benefit_currency`, `required_documents`, `last_verified_date`, `eligibility_verified`, `data_quality_score` into the cleaned output (these are dropped or not included in `OUTPUT_COLUMNS`) |

### `Backend/data_pipeline/load_to_mysql.py` (7,311 bytes)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Load cleaned CSV into MySQL |
| **Status** | Working — creates DB, applies schema, batch-inserts |
| **Implementation** | Uses SQLAlchemy + pymysql; `create_database_if_not_exists()`, `execute_schema()`, `load_cleaned_csv()`, `dataframe_to_records()`, `truncate_table()`, `batch_insert()`, `verify_import()` |
| **Missing** | No upsert logic (only truncate + reload), no incremental updates, no error recovery beyond rollback |

### `Backend/data_pipeline/schema.sql` (1,372 bytes)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | MySQL table DDL for `schemes` |
| **Status** | Working — single table definition |
| **Implementation** | `CREATE TABLE IF NOT EXISTS schemes (...)` with 17 columns, 3 indexes |
| **Missing** | No foreign keys, no additional tables (rules, documents, user_profiles, eligibility_results), no `bpl_required`, `marital_status_required`, `is_national_scheme` columns |

### `Backend/data_pipeline/__init__.py` (73 bytes)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Package marker |
| **Status** | Docstring only |

---

## 3. FastAPI Analysis

### Existing Routes

| Method | Path | Response | Description |
|--------|------|----------|-------------|
| GET | `/` | `{"message": "Seva-AI Backend Running properly!"}` | Health check only |

### Request Models

**None.** No Pydantic models exist anywhere in the codebase.

### Response Models

**None.** No Pydantic response models exist.

### Missing APIs

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/check-eligibility` | Evaluate user profile against all schemes |
| GET | `/scheme/{id}` | Return scheme details + eligibility rules |
| GET | `/health` | Health check (more descriptive than `/`) |
| GET | `/schemes` | List/filter schemes |
| POST | `/api/profile` | Create/update user profile |
| GET | `/api/profile/{id}` | Get user profile |
| POST | `/api/analyze` | Full pipeline run |
| GET | `/api/schemes/eligible` | Eligible schemes list |
| GET | `/api/benefits/wallet` | Benefit wallet aggregation |
| GET | `/api/documents/missing` | Missing documents |
| GET | `/api/readiness` | Readiness scores |
| GET | `/api/opportunities/future` | Future opportunities |
| POST | `/api/chat` | Chatbot turn |

---

## 4. Database Analysis

### MySQL Schema

**Database:** `seva_ai`  
**Table:** `schemes` (single table, no relationships)

### Current Schema Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  schemes                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  scheme_id                 VARCHAR(128)   PK  NOT NULL                      │
│  scheme_name               VARCHAR(512)      NOT NULL                      │
│  state                     VARCHAR(128)      NOT NULL                      │
│  category                  VARCHAR(64)       NOT NULL                      │
│  benefit_summary           TEXT              NOT NULL                      │
│  eligibility_text_clean    TEXT              NOT NULL                      │
│  gender                    VARCHAR(16)       NOT NULL  DEFAULT 'any'       │
│  min_age                   DECIMAL(5,1)      NULL                          │
│  max_age                   DECIMAL(5,1)      NULL                          │
│  max_annual_income         DECIMAL(15,2)     NULL                          │
│  occupation_tokens         VARCHAR(256)      NULL                          │
│  allowed_social_categories VARCHAR(128)      NULL                          │
│  required_disability_status VARCHAR(256)     NULL                          │
│  benefit_value_numeric     DECIMAL(18,2)     NULL                          │
│  confidence_score          DECIMAL(5,4)      NOT NULL  DEFAULT 0.0000      │
│  application_url           TEXT              NOT NULL                      │
│  official_source_url       TEXT              NOT NULL                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  INDEXES:                                                                   │
│    idx_schemes_state (state)                                                │
│    idx_schemes_category (category)                                          │
│    idx_schemes_confidence_score (confidence_score)                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Columns (17 total)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| scheme_id | VARCHAR(128) | NO | — | Primary key |
| scheme_name | VARCHAR(512) | NO | — | Display name |
| state | VARCHAR(128) | NO | — | State restriction (e.g., "All India", "Maharashtra") |
| category | VARCHAR(64) | NO | — | Scheme category (agriculture, health, etc.) |
| benefit_summary | TEXT | NO | — | Human-readable benefit description |
| eligibility_text_clean | TEXT | NO | — | Full eligibility rules (free text) |
| gender | VARCHAR(16) | NO | 'any' | Gender restriction (any/female/male) |
| min_age | DECIMAL(5,1) | YES | NULL | Minimum age |
| max_age | DECIMAL(5,1) | YES | NULL | Maximum age |
| max_annual_income | DECIMAL(15,2) | YES | NULL | Maximum annual income (INR) |
| occupation_tokens | VARCHAR(256) | YES | NULL | Semicolon-separated allowed occupations |
| allowed_social_categories | VARCHAR(128) | YES | NULL | Semicolon-separated allowed social categories |
| required_disability_status | VARCHAR(256) | YES | NULL | Semicolon-separated required disability types |
| benefit_value_numeric | DECIMAL(18,2) | YES | NULL | Numeric benefit amount |
| confidence_score | DECIMAL(5,4) | NO | 0.0000 | Data quality confidence (0–1) |
| application_url | TEXT | NO | — | Application link |
| official_source_url | TEXT | NO | — | Official source link |

### Indexes

| Index Name | Column | Type |
|------------|--------|------|
| PRIMARY | scheme_id | B-tree |
| idx_schemes_state | state | B-tree |
| idx_schemes_category | category | B-tree |
| idx_schemes_confidence_score | confidence_score | B-tree |

### Relationships

**None.** Single table, no foreign keys, no related tables.

### Missing Fields (from CSV but not in MySQL schema)

| CSV Column | MySQL Column | Reason Missing |
|------------|--------------|----------------|
| `scheme_category` (raw) | — | Only `category` (cleaned) is stored |
| `issuing_authority` | — | Not in schema |
| `issuing_authority_normalized` | — | Not in schema |
| `min_age_inferred` | — | Not in schema |
| `max_age_inferred` | — | Not in schema |
| `income_inferred` | — | Not in schema |
| `is_national_scheme` | — | Not in schema (but derivable from `state = 'All India'`) |
| `benefit_value_estimate` | — | Not in schema |
| `benefit_currency` | — | Not in schema |
| `required_documents` | — | Not in schema |
| `last_verified_date` | — | Not in schema |
| `eligibility_verified` | — | Not in schema |
| `data_quality_score` | — | Not in schema |

### Missing Fields (from architecture plan but not in CSV or schema)

| Field | Type | Purpose |
|-------|------|---------|
| `bpl_required` | BOOLEAN | Whether scheme requires BPL status |
| `marital_status_required` | VARCHAR(64) | Required marital status (widow, divorced, etc.) |
| `land_required` | BOOLEAN | Whether scheme requires land ownership |
| `eligibility_rules_json` | JSON | Structured rules for engine |
| `benefit_type` | ENUM | Monetary vs non-monetary |
| `benefit_frequency` | ENUM | Payment cadence |
| `benefit_is_institutional` | BOOLEAN | Exclude from individual totals |
| `data_tier` | ENUM | verified/high/medium/low |
| `applicant_type` | ENUM | citizen/institution/enterprise |

### Potential Improvements

1. **Add `bpl_required` column** — 251 schemes mention BPL in eligibility text; a structured boolean would enable rule-based matching.
2. **Add `marital_status_required` column** — 184 schemes mention "widow", 46 mention "divorce", 85 mention "unmarried", 225 mention "married" in text.
3. **Add `is_national_scheme` column** — Currently derivable from `state = 'All India'` but a dedicated boolean is cleaner.
4. **Add `issuing_authority` column** — 436 unique authorities; useful for trust display.
5. **Add `required_documents` column** — 100% populated in CSV; useful for document checker.
6. **Add `eligibility_verified` column** — Only 20 schemes verified; useful for confidence scoring.
7. **Add `data_quality_score` column** — Available in CSV; useful for tiering.
8. **Add `benefit_type` and `benefit_frequency` columns** — Needed for benefit wallet.
9. **Create related tables** — `scheme_eligibility_rules`, `scheme_documents`, `user_profiles`, `eligibility_results` (as per architecture plan).
10. **Add foreign key constraints** — For referential integrity.

---

## 5. Dataset Analysis

### `Data/indian_government_schemes.csv`

| Metric | Value |
|--------|-------|
| **Total rows** | 4,702 |
| **Total columns** | 29 |
| **Duplicate rows** | 0 |
| **Duplicate scheme_id** | 0 |
| **Duplicate scheme_name** | 0 |
| **File size** | 5,871,301 bytes (~5.6 MB) |

### Column Descriptions

| Column | Type | Non-Null | Missing % | Description |
|--------|------|----------|-----------|-------------|
| `scheme_id` | string | 4,702 | 0% | Unique identifier (slug format) |
| `scheme_name` | string | 4,702 | 0% | Display name |
| `scheme_category` | string | 4,702 | 0% | Raw category (e.g., `women_child`) |
| `scheme_category_clean` | string | 4,702 | 0% | Normalized category (e.g., `women_and_child`) |
| `issuing_authority` | string | 4,702 | 0% | Raw issuing authority |
| `issuing_authority_normalized` | string | 4,702 | 0% | Normalized authority (436 unique) |
| `min_age` | float | 1,066 | 77.3% | Minimum age (primary) |
| `max_age` | float | 791 | 83.2% | Maximum age (primary) |
| `max_annual_income` | float | 793 | 83.1% | Max annual income (primary, INR) |
| `min_age_inferred` | float | 641 | 86.4% | Minimum age (inferred from text) |
| `max_age_inferred` | float | 641 | 86.4% | Maximum age (inferred from text) |
| `income_inferred` | float | 141 | 97.0% | Income (inferred from text) |
| `allowed_occupations` | string | 2,750 | 41.5% | Semicolon-separated occupations |
| `allowed_social_categories` | string | 785 | 83.3% | Semicolon-separated social categories |
| `required_disability_status` | string | 309 | 93.4% | Semicolon-separated disability types |
| `state_restricted_to_normalized` | string | 4,702 | 0% | State restriction (37 unique values) |
| `gender_restricted_to` | string | 4,702 | 0% | Gender restriction (any/female/male) |
| `is_national_scheme` | boolean | 4,702 | 0% | National vs state scheme |
| `eligibility_text_clean` | string | 4,702 | 0% | Full eligibility rules (free text, avg 634 chars) |
| `benefit_summary` | string | 4,702 | 0% | Human-readable benefit description |
| `benefit_value_estimate` | string | 4,701 | 0.02% | Human-readable benefit amount |
| `benefit_value_numeric` | float | 3,838 | 18.4% | Numeric benefit amount |
| `benefit_currency` | string | 4,702 | 0% | Currency (all ₹) |
| `required_documents` | string | 4,702 | 0% | Semicolon-separated document types |
| `application_url` | string | 4,702 | 0% | Application link |
| `official_source_url` | string | 4,702 | 0% | Official source link |
| `last_verified_date` | string | 4,702 | 0% | Last verified date (all 2026-07-10) |
| `eligibility_verified` | boolean | 4,702 | 0% | Manual verification flag (20 True) |
| `data_quality_score` | float | 4,702 | 0% | Quality score (58.8–100, mean 72.3) |

### Missing Values Summary

| Field | Missing Count | Missing % |
|-------|---------------|-----------|
| `min_age` | 3,636 | 77.3% |
| `max_age` | 3,911 | 83.2% |
| `max_annual_income` | 3,909 | 83.1% |
| `min_age_inferred` | 4,061 | 86.4% |
| `max_age_inferred` | 4,061 | 86.4% |
| `income_inferred` | 4,561 | 97.0% |
| `allowed_occupations` | 1,952 | 41.5% |
| `allowed_social_categories` | 3,917 | 83.3% |
| `required_disability_status` | 4,393 | 93.4% |
| `benefit_value_numeric` | 864 | 18.4% |
| `benefit_value_estimate` | 1 | 0.02% |

### Duplicate Values

- **No duplicate rows** detected.
- **No duplicate `scheme_id`** values.
- **No duplicate `scheme_name`** values.
- Dataset integrity at the scheme level is good.

### Important Eligibility Fields

| Field | Populated | % | Notes |
|-------|-----------|---|-------|
| `state_restricted_to_normalized` | 4,702 | 100% | 37 unique values; 697 "All India" |
| `gender_restricted_to` | 4,702 | 100% | `any` (4,238), `female` (448), `male` (16) |
| `is_national_scheme` | 4,702 | 100% | True (697), False (4,005) |
| `min_age` | 1,066 | 22.7% | Range 0–66; 13 rows with `min_age=0` |
| `max_age` | 791 | 16.8% | Range 0–80; 2 rows with `max_age=0` |
| `max_annual_income` | 793 | 16.9% | Range ₹3,600–₹20,00,000 |
| `allowed_occupations` | 2,750 | 58.5% | Tokens: farmer, student, daily_wage, self_employed, unemployed, salaried |
| `allowed_social_categories` | 785 | 16.7% | Tokens: sc, st, obc, ews, general |
| `required_disability_status` | 309 | 6.6% | Tokens: physical, visual, hearing, intellectual, multiple |
| `eligibility_text_clean` | 4,702 | 100% | Free text, avg 634 chars, max 9,240 |
| `eligibility_verified` | 4,702 | 100% | Only 20 True (0.4%) |

### BPL References in Text

- **251 schemes** mention BPL (Below Poverty Line) in `eligibility_text_clean`.
- Examples: Aam Aadmi Bima Yojana, AASRA Scheme, Accident Relief Scheme, Andaman & Nicobar Islands Scheme for Health Insurance.
- **No structured `bpl_required` field** exists in the CSV or MySQL schema.

### Marital Status References in Text

| Pattern | Schemes Mentioning |
|---------|-------------------|
| "widow" / "widowed" | 184 |
| "divorce" / "divorced" / "separated" | 46 |
| "unmarried" / "spinsters" / "single woman" | 85 |
| "married" / "marriage" | 225 |
| **Total (any marital reference)** | ~318+ (overlapping) |

- **No structured `marital_status_required` field** exists in the CSV or MySQL schema.

### Land References in Text

- **468 schemes** mention land/landholding/landowner/landless in `eligibility_text_clean`.
- **No structured `land_required` field** exists in the CSV or MySQL schema.

### Data Quality Issues

| Issue | Count | Impact |
|-------|-------|--------|
| `benefit_value_numeric = 1` (placeholder) | 227 | Benefit wallet math wrong |
| `benefit_value_numeric` missing | 864 | 18.4% of schemes lack numeric benefit |
| `min_age = 0` | 13 | May cause false age matches |
| `max_age = 0` | 2 | May cause false age matches |
| `max_age_inferred > 120` | present | Invalid inferred age |
| `income_inferred = 1` (placeholder) | 73 | Invalid inferred income |
| `income_inferred` outlier (₹5B) | 1 | Extreme outlier |
| `benefit_value_numeric` outliers (>₹1 crore) | 74 | Distort aggregate totals |
| `data_quality_score < 70` | 1,173 (24.9%) | Lower confidence tiers |
| Only 20 schemes `eligibility_verified=True` | 20 (0.4%) | Low trust for automated matching |
| 946 schemes with zero structured eligibility fields | 946 (20.1%) | Must rely on text-only matching |
| 77–83% missing age/income fields | — | Rule-based eligibility fails for most schemes |
| `benefit_summary` contains markdown | — | May need sanitization for display |
| `eligibility_text_clean` uses inconsistent list formats | — | NLP parsing complexity |

---

## 6. Eligibility Engine Readiness

### What Exists

- **Nothing.** There is no eligibility engine code in the repository.
- The `Backend/` directory contains only `main.py` (health check) and an empty `routes.py`.
- No `models/`, `services/`, or `database/` directories exist.
- No Pydantic models, no service classes, no database abstraction layer.

### What Is Missing

| Component | Description |
|-----------|-------------|
| **User Profile Model** | Pydantic model for age, gender, state, income, social_category, occupation, disability_status, marital_status, is_bpl |
| **Scheme Model** | Pydantic model representing a scheme with its eligibility rules |
| **Eligibility Result Model** | Pydantic model for condition results (PASS/FAIL/UNKNOWN/NOT_APPLICABLE) and overall result (ELIGIBLE/PARTIAL/INELIGIBLE) |
| **Database Layer** | Reusable MySQL connection management, scheme repository |
| **Eligibility Engine** | Core service that evaluates user profile against scheme rules |
| **API Routes** | POST `/check-eligibility`, GET `/scheme/{id}` |
| **Tests** | Unit tests for engine and API |

### Required Services

| Service | Purpose |
|---------|---------|
| `data_loader.py` | Load schemes from MySQL into memory |
| `eligibility_engine.py` | Evaluate user profile against scheme rules |
| `benefit_wallet.py` | Aggregate benefits per scheme and total |
| `document_checker.py` | Compare required vs held documents |
| `readiness_scorer.py` | Compute 0–100 readiness score |
| `future_opportunities.py` | Near-miss analysis for ineligible schemes |

### Required Models

| Model | Fields |
|-------|--------|
| `UserProfile` | age, gender, state, income, social_category, occupation, disability_status, marital_status, is_bpl |
| `Scheme` | scheme_id, scheme_name, state, category, gender, min_age, max_age, max_annual_income, occupation_tokens, allowed_social_categories, required_disability_status, benefit_summary, confidence_score, application_url, official_source_url |
| `ConditionResult` | condition_name, status, user_value, required_value, explanation |
| `EligibilityResult` | scheme_id, scheme_name, overall_result, confidence_score, confidence_explanation, condition_results, explanation |

---

## 7. Frontend Analysis

### `Frontend/app.py` (93 bytes)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Streamlit UI entry point |
| **Status** | Stub — title and tagline only |
| **Implementation** | `st.title("Seva-AI")` + `st.write("AI Government Benefits Assistant")` |
| **Missing** | All UI components: profile form, results display, benefit wallet, document checker, readiness score, future opportunities |

### Existing Pages

- **None.** Single page with title only.

### Existing Components

- **None.** No forms, no data display, no API integration.

### Missing Pages

| Page | Purpose |
|------|---------|
| Profile Form | Collect age, gender, state, income, social_category, occupation, disability_status, marital_status, is_bpl |
| Eligible Schemes | Display eligible/partial schemes with explanations |
| Benefit Wallet | Show per-scheme and total benefits |
| Missing Documents | Show required vs held documents |
| Readiness Score | Show 0–100 readiness gauge |
| Future Opportunities | Show near-miss schemes |
| Chatbot | Conversational interface |

---

## 8. Feature Status

| Feature | Status | Notes |
|---------|--------|-------|
| **AI Chatbot** | NOT STARTED | `AI/chatbot.py` is 0 bytes |
| **Eligible Schemes** | NOT STARTED | No eligibility engine, no API routes |
| **Benefit Wallet** | NOT STARTED | No benefit aggregation service |
| **Readiness Score** | NOT STARTED | No readiness scorer |
| **Missing Documents** | NOT STARTED | No document checker; `required_documents` not in MySQL schema |
| **Future Opportunities** | NOT STARTED | No near-miss analyzer |
| **Translation** | NOT STARTED | `Translation/translator.py` is 0 bytes |
| **Voice Support** | NOT STARTED | `Voice/` directory is empty |
| **Data Pipeline** | PARTIAL | CSV cleaning and MySQL import work; missing inferred field coalescing, benefit classification, document validation |
| **User Profile** | NOT STARTED | No profile model or persistence |
| **API Routes** | NOT STARTED | Only health check exists |

---

## 9. Security Review

### Secrets & Environment Variables

| Item | Status | Notes |
|------|--------|-------|
| `.env.example` | Present | Contains MySQL connection template with placeholder password |
| `.env` | Not present | Correctly gitignored; no actual secrets in repo |
| `MYSQL_PASSWORD` | In env var | Loaded via `python-dotenv` in `config.py` — good practice |
| API keys | None in code | No API keys found in any source file |
| Database credentials | In env var | `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` — all from environment |

### Issues Found

| Issue | Severity | Description |
|-------|----------|-------------|
| **No `.env` validation** | Medium | `config.py` does not validate that required env vars are set; will silently use defaults (e.g., empty password) |
| **No CORS configuration** | Medium | FastAPI app has no CORS middleware; frontend cannot call backend |
| **No authentication/authorization** | High | No auth on any endpoint; all APIs would be publicly accessible |
| **No HTTPS enforcement** | Medium | No TLS configuration in code |
| **No rate limiting** | Medium | No rate limiting on API endpoints |
| **No input sanitization** | Medium | No validation of user input beyond what Pydantic would provide (which doesn't exist yet) |
| **No security headers** | Low | No security headers (CSP, X-Frame-Options, etc.) |
| **No audit logging** | Low | No logging of API requests or eligibility decisions |
| **Windows-only packages in requirements** | Low | `pywin32`, `pypiwin32` in requirements.txt — not portable |

### Positive Findings

- Database credentials are NOT hard-coded in source code.
- `.env` is correctly listed in `.gitignore`.
- No API keys or secrets are committed to the repository.

---

## 10. Technical Debt

### Bugs

| Bug | Location | Description |
|-----|----------|-------------|
| **No bugs found** | — | The existing code (health check, data pipeline) appears functional |

### Architecture Issues

| Issue | Description |
|-------|-------------|
| **No package structure** | `Backend/` has no `models/`, `services/`, or `database/` directories; no shared Pydantic models |
| **Empty stubs** | `routes.py`, `chatbot.py`, `translator.py` are 0-byte files — create false impression of progress |
| **No separation of concerns** | No separation between API routes, business logic, and data access |
| **No dependency injection** | FastAPI app has no DI for database sessions or services |
| **No startup/shutdown events** | No database connection lifecycle management |
| **No error handling** | No global exception handlers, no graceful database error handling in API |
| **No logging** | No structured logging in backend |
| **No testing** | No test files, no test framework configured |
| **No CI/CD** | No CI/CD pipeline, no linting, no type checking |
| **No OpenAPI schema customization** | No endpoint descriptions, no response models |
| **requirements.txt is a pip freeze** | Includes Windows-only packages (`pywin32`, `pypiwin32`), transitive dependencies, and unrelated packages |
| **No virtual environment management** | No `pyproject.toml` or `setup.py`; dependencies managed via raw `requirements.txt` |
| **No type checking** | No `mypy` or `pyright` configuration |
| **No code formatting** | No `black` or `ruff` configuration |

### Code Smells

| Smell | Location | Description |
|-------|----------|-------------|
| **Empty files** | `Backend/routes.py`, `AI/chatbot.py`, `Translation/translator.py` | 0-byte files that serve no purpose |
| **Magic strings** | `clean_data.py` | Hard-coded state names, category names, gender values |
| **Long functions** | `clean_data.py` | `clean_schemes()` is 67 lines with multiple responsibilities |
| **No docstrings on key functions** | `clean_data.py` | Some functions lack docstrings |
| **Inconsistent naming** | `clean_data.py` | `state_restricted_to_normalized` vs `state` (in MySQL) |
| **No input validation** | `main.py` | No validation of request data |
| **No response models** | `main.py` | No Pydantic response models |

### Refactoring Opportunities

| Opportunity | Description |
|-------------|-------------|
| **Create `Backend/models/` package** | Pydantic models for UserProfile, Scheme, EligibilityResult |
| **Create `Backend/services/` package** | Eligibility engine, benefit wallet, document checker, readiness scorer |
| **Create `Backend/database/` package** | Connection management, repository pattern |
| **Add CORS middleware** | Enable frontend-backend communication |
| **Add global exception handlers** | Graceful error responses |
| **Add structured logging** | Use `structlog` or standard `logging` |
| **Add health check endpoint** | More descriptive than `GET /` |
| **Add request/response validation** | Pydantic models for all endpoints |
| **Add tests** | pytest with mocks for database-dependent tests |
| **Clean up requirements.txt** | Remove Windows-only packages, use `pyproject.toml` |
| **Add type checking** | Configure `mypy` or `pyright` |
| **Add code formatting** | Configure `black` or `ruff` |

---

## 11. Priority Roadmap

### P0 — Critical (Must Have for MVP)

| # | Task | Files | Dependencies | Difficulty |
|---|------|-------|--------------|------------|
| 1 | Create Pydantic models (UserProfile, Scheme, EligibilityResult, ConditionResult) | `Backend/models/` | pydantic | Easy |
| 2 | Create database layer (connection, scheme repository) | `Backend/database/` | sqlalchemy, pymysql | Medium |
| 3 | Build eligibility engine (evaluate 9 conditions per scheme) | `Backend/services/eligibility_engine.py` | models, database | Hard |
| 4 | Create API routes (POST `/check-eligibility`, GET `/scheme/{id}`) | `Backend/routes.py` | models, services | Medium |
| 5 | Integrate routes into FastAPI app | `Backend/main.py` | routes | Easy |
| 6 | Add CORS middleware | `Backend/main.py` | — | Easy |
| 7 | Write tests for eligibility engine and API | `Backend/tests/` | pytest, httpx | Medium |
| 8 | Add `bpl_required` and `marital_status_required` columns to schema | `schema.sql` | — | Easy |

### P1 — Important (Should Have)

| # | Task | Files | Dependencies | Difficulty |
|---|------|-------|--------------|------------|
| 9 | Create Streamlit profile form | `Frontend/app.py` | streamlit, pydantic | Medium |
| 10 | Create results dashboard | `Frontend/app.py` | streamlit | Medium |
| 11 | Add benefit wallet aggregation | `Backend/services/benefit_wallet.py` | models | Medium |
| 12 | Add document checker | `Backend/services/document_checker.py` | models | Medium |
| 13 | Add readiness scorer | `Backend/services/readiness_scorer.py` | models | Medium |
| 14 | Add future opportunities analyzer | `Backend/services/future_opportunities.py` | models | Medium |
| 15 | Add structured logging | All backend files | — | Easy |
| 16 | Add global exception handlers | `Backend/main.py` | — | Easy |
| 17 | Add health check endpoint | `Backend/routes.py` | — | Easy |
| 18 | Clean up requirements.txt | `requirements.txt` | — | Easy |

### P2 — Nice to Have

| # | Task | Files | Dependencies | Difficulty |
|---|------|-------|--------------|------------|
| 19 | Implement AI chatbot | `AI/chatbot.py` | LLM API | Hard |
| 20 | Implement translation | `Translation/translator.py` | googletrans | Medium |
| 21 | Implement voice I/O | `Voice/` | SpeechRecognition, pyttsx3 | Hard |
| 22 | Add type checking | `pyproject.toml` | mypy/pyright | Easy |
| 23 | Add code formatting | `pyproject.toml` | black/ruff | Easy |
| 24 | Add CI/CD pipeline | `.github/` | GitHub Actions | Medium |
| 25 | Add authentication | `Backend/` | fastapi-users, jwt | Medium |
| 26 | Add rate limiting | `Backend/` | slowapi | Easy |
| 27 | Add security headers | `Backend/` | — | Easy |

---

## 12. Final Score

| Component | Score / 10 | Notes |
|-----------|------------|-------|
| **Backend** | 2/10 | Health check only; no models, services, routes, or database layer |
| **Frontend** | 1/10 | Title and tagline only; no forms or results display |
| **Data Pipeline** | 6/10 | CSV cleaning and MySQL import work; missing inferred field coalescing, benefit classification, document validation |
| **Database** | 4/10 | Single `schemes` table with 17 columns; missing BPL, marital status, documents, authority, verification fields; no related tables |
| **Hackathon Readiness** | 3/10 | Core data pipeline exists but no eligibility engine, no API, no UI; significant work needed for MVP |

### Score Justification

- **Backend (2/10):** The FastAPI app runs and returns a health check, but there are zero business endpoints, no models, no services, and no database integration in the API layer. The data pipeline is functional but separate from the API.
- **Frontend (1/10):** Streamlit app shows a title and tagline. No user interaction, no API calls, no results display.
- **Data Pipeline (6/10):** The CSV cleaning and MySQL import scripts are well-structured and functional. They handle normalization, deduplication, and confidence scoring. However, they don't populate all available CSV fields into MySQL, and they don't add the new fields proposed in the architecture plan.
- **Database (4/10):** The MySQL schema is clean and well-indexed for the `schemes` table, but it's a single table with no relationships. Many useful fields from the CSV are not stored. No `bpl_required`, `marital_status_required`, `is_national_scheme`, `issuing_authority`, `required_documents`, `eligibility_verified`, or `data_quality_score` columns.
- **Hackathon Readiness (3/10):** The project has a solid data foundation (4,702 schemes in CSV, cleaning pipeline, MySQL schema) and comprehensive design documents. However, the actual application code is essentially non-existent. Building the eligibility engine, API, and UI from scratch is a significant effort.

---

## Appendix A: Key Data Gaps for Eligibility Engine

| User Profile Field | Scheme Data Available? | Source |
|--------------------|----------------------|--------|
| `age` | Partially | `min_age`, `max_age` (22.7%, 16.8%); `min_age_inferred`, `max_age_inferred` (86.4%) |
| `gender` | Yes | `gender` column (100%) |
| `state` | Yes | `state` column (100%); "All India" = national |
| `income` | Partially | `max_annual_income` (16.9%); `income_inferred` (3%) |
| `social_category` | Partially | `allowed_social_categories` (16.7%) |
| `occupation` | Partially | `occupation_tokens` (58.5%) |
| `disability_status` | Partially | `required_disability_status` (6.6%) |
| `marital_status` | No | Mentioned in text (184–225 schemes) but no structured field |
| `is_bpl` | No | Mentioned in text (251 schemes) but no structured field |

## Appendix B: Verified Seed Schemes (20)

These 20 schemes have `eligibility_verified=True` and are the highest-confidence candidates for the hackathon demo:

| scheme_id | scheme_name | State | Gender | Min Age | Max Age | Max Income | Occupation | Social Category | Disability |
|-----------|-------------|-------|--------|---------|---------|------------|------------|-----------------|------------|
| pm-kisan-001 | PM-KISAN Samman Nidhi | All India | any | 18 | — | 200,000 | farmer | — | — |
| pmfby-002 | Pradhan Mantri Fasal Bima Yojana | All India | any | 18 | — | — | farmer | — | — |
| pmay-g-003 | Pradhan Mantri Awas Yojana - Gramin | All India | any | 18 | — | 120,000 | — | — | — |
| nsap-igndps-004 | Indira Gandhi National Disability Pension Scheme | All India | any | 18 | 59 | 100,000 | — | — | physical;visual;hearing;intellectual;multiple |
| nsap-igndps-old-005 | Indira Gandhi National Old Age Pension Scheme | All India | any | 60 | — | 100,000 | — | — | — |
| pmjay-006 | Ayushman Bharat PM-JAY | All India | any | — | — | 100,000 | — | — | — |
| nmms-007 | National Means-cum-Merit Scholarship | All India | any | 13 | 18 | 350,000 | student | — | — |
| post-matric-sc-008 | Post-Matric Scholarship for SC Students | All India | any | 15 | — | 250,000 | student | sc | — |
| pmmvy-009 | Pradhan Mantri Matru Vandana Yojana | All India | female | 19 | 45 | 200,000 | — | — | — |
| pm-svanidhi-010 | PM Street Vendor's AtmaNirbhar Nidhi | All India | any | 18 | — | — | self_employed;daily_wage | — | — |
| nrega-011 | Mahatma Gandhi National Rural Employment Guarantee | All India | any | 18 | — | — | daily_wage;unemployed;farmer | — | — |
| kalia-odisha-012 | KALIA Scheme (Odisha) | Odisha | any | 18 | — | 150,000 | farmer;daily_wage | — | — |
| ladli-behna-mp-013 | Ladli Behna Yojana (Madhya Pradesh) | Madhya Pradesh | female | 21 | 60 | 250,000 | — | — | — |
| nfbs-014 | National Family Benefit Scheme | All India | any | 18 | 59 | 100,000 | — | — | — |
| pm-scholarship-obc-015 | Post-Matric Scholarship for OBC Students | All India | any | 15 | — | 150,000 | student | obc | — |
| disability-scholarship-016 | Scholarship for Students with Disabilities | All India | any | 14 | 35 | 250,000 | student | — | physical;visual;hearing;intellectual;multiple |
| widow-pension-017 | Indira Gandhi National Widow Pension Scheme | All India | female | 40 | 79 | 100,000 | — | — | — |
| sukanya-018 | Sukanya Samriddhi Yojana | All India | female | 0 | 10 | — | — | — | — |
| tribal-grant-019 | Pre-Matric Scholarship for ST Students | All India | any | 10 | 18 | 250,000 | student | st | — |
| ews-housing-urban-020 | PMAY-Urban (EWS/LIG) | All India | any | 18 | — | 300,000 | — | ews;general;obc;sc;st | — |

---

*End of Project Audit Report.*
