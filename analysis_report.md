# Seva-AI — Comprehensive Analysis Report

**Date:** 18 August 2026  
**Dataset analyzed:** `Data/indian_government_schemes.csv`  
**Note:** The user brief references `Data/schemes.csv`, which does **not** exist in the repository. All data conclusions below are based on `indian_government_schemes.csv`.

---

## 1. Executive Summary

Seva-AI is an early-stage hackathon project with a clear product vision (AI-powered government scheme discovery) but **minimal implemented functionality**. The repository contains scaffolding for a FastAPI backend, Streamlit frontend, AI chatbot, and translation layer — most modules are empty stubs.

The dataset is **substantial and usable for an MVP** (4,702 unique schemes, 29 columns, zero duplicate IDs), but it has **critical data-quality gaps** that directly impact eligibility matching, benefit wallet accuracy, and readiness scoring:

| Risk | Impact |
|------|--------|
| **77–83% missing structured age/income fields** | Rule-based eligibility will fail for most schemes without NLP fallback |
| **946 schemes (20%) have zero structured eligibility** | Must rely entirely on `eligibility_text_clean` |
| **Only 20 schemes manually verified** (`eligibility_verified=True`) | High risk of incorrect automated matches |
| **18.4% missing `benefit_value_numeric`; 227 placeholder values (=1)** | Benefit Wallet totals will be unreliable without normalization |
| **Extreme benefit outliers (up to ₹150B)** | Aggregated benefit estimates will be distorted |
| **No `benefit_frequency`, `benefit_type`, or application steps** | Wallet and readiness must infer from free text or flag gaps |

**Recommendation:** Build a **hybrid eligibility engine** — structured rules where fields exist, text-based extraction + confidence scoring elsewhere. Prioritize the 20 verified seed schemes and state/national schemes with complete structured fields for the hackathon demo. Do not invent eligibility rules; surface data gaps transparently to users.

---

## 2. Repository Architecture Analysis

### 2.1 Current Structure

```
Seva-AI/
├── AI/chatbot.py          # Empty
├── Backend/
│   ├── main.py            # FastAPI app with single health route
│   └── routes.py          # Empty
├── Frontend/app.py        # Streamlit title only
├── Translation/translator.py  # Empty
├── Data/indian_government_schemes.csv
├── requirements.txt       # Full dependency lockfile
└── README.md              # Title only
```

### 2.2 File-by-File Purpose

| File | Purpose | Current State |
|------|---------|---------------|
| `Backend/main.py` | FastAPI application entry point | Running health check at `GET /` |
| `Backend/routes.py` | API route definitions | Empty — no business endpoints |
| `Frontend/app.py` | Streamlit citizen-facing UI | Title + tagline only |
| `AI/chatbot.py` | Conversational AI layer | Empty |
| `Translation/translator.py` | Multilingual support | Empty |
| `Data/indian_government_schemes.csv` | Scheme knowledge base | 4,702 rows, primary data asset |
| `requirements.txt` | Python dependencies | FastAPI, Streamlit, pandas, googletrans, SpeechRecognition, pyttsx3 |

### 2.3 Intended Architecture (Inferred)

```
Streamlit Frontend  ──HTTP──►  FastAPI Backend  ──►  CSV / Future DB
                                      │
                                      ├── Eligibility Engine (not built)
                                      ├── AI/chatbot.py (not built)
                                      └── Translation/translator.py (not built)
```

### 2.4 Dependencies

**Core stack:** Python 3.10+, FastAPI 0.141, Uvicorn, Streamlit 1.61, Pandas 2.3, Pydantic 2.13

**Planned capabilities (from dependencies, not implemented):**
- `googletrans` — translation
- `SpeechRecognition`, `pyttsx3` — voice I/O
- `requests`, `httpx` — HTTP clients

### 2.5 Data Flow (Current)

**None.** Frontend does not call backend. Backend does not load CSV. No shared data layer exists.

### 2.6 Frontend/Backend Communication

Not implemented. No CORS config, no API client in Streamlit, no shared Pydantic models.

### 2.7 AI/Chatbot Functionality

Not implemented. No LLM integration, no RAG pipeline, no prompt templates.

### 2.8 Translation Functionality

Not implemented despite `googletrans` in requirements.

### 2.9 Existing API Routes

| Method | Path | Response |
|--------|------|----------|
| GET | `/` | `{"message": "Seva-AI Backend Running properly!"}` |

### 2.10 Integration Points

| Component | Integration Point |
|-----------|-------------------|
| CSV → Backend | Load at startup via pandas/SQLite |
| Backend → Eligibility | New service module |
| Backend → Frontend | REST: `/profile`, `/schemes/eligible`, `/benefits`, `/documents`, `/readiness`, `/future` |
| AI/chatbot | Wrap eligibility results + RAG over scheme text |
| Translation | Post-process API responses or UI labels |

### 2.11 Code Quality Issues

- Empty modules create false impression of progress
- No project package structure (`__init__.py`, shared models)
- No tests, linting, or CI
- `requirements.txt` is a full pip freeze (includes Windows-only packages: `pywin32`, `pypiwin32`)
- No environment configuration (`.env` pattern exists in gitignore but unused)
- No error handling, logging, or validation layers

### 2.12 Missing Components

- Data loading and cleaning pipeline
- Database layer (SQLite recommended for MVP)
- User profile model and persistence
- Eligibility engine
- Document checker
- Readiness scorer
- Benefit wallet aggregator
- Future opportunities analyzer
- API routes beyond health check
- Frontend forms and result views
- Chatbot and translation implementations

### 2.13 Potential Conflicts

| Conflict | Description |
|----------|-------------|
| CSV vs DB | Direct CSV reads won't scale; need one canonical cleaned store |
| Structured vs text eligibility | 80% of schemes need text parsing; pure rule engine insufficient |
| Default document lists | `required_documents` appears auto-populated (aadhaar on 79.8%); may over-state requirements |
| Category naming | `women_child` vs `women_and_child` requires mapping |
| National vs state | 85% state-restricted; user state is mandatory for accurate results |

---

## 3. Dataset Analysis

### 3.1 Basic Statistics

| Metric | Value |
|--------|-------|
| **Rows** | 4,702 |
| **Columns** | 29 |
| **Duplicate rows** | 0 |
| **Duplicate `scheme_id`** | 0 |
| **Duplicate `scheme_name`** | 0 |
| **Unique schemes** | 4,702 |

### 3.2 All Column Names and Data Types

| Column | Data Type | Non-Null | Missing % |
|--------|-----------|----------|-----------|
| `scheme_id` | string | 4,702 | 0% |
| `scheme_name` | string | 4,702 | 0% |
| `scheme_category` | string | 4,702 | 0% |
| `scheme_category_clean` | string | 4,702 | 0% |
| `issuing_authority` | string | 4,702 | 0% |
| `issuing_authority_normalized` | string | 4,702 | 0% |
| `min_age` | float | 1,066 | 77.33% |
| `max_age` | float | 791 | 83.18% |
| `max_annual_income` | float | 793 | 83.13% |
| `min_age_inferred` | float | 641 | 86.37% |
| `max_age_inferred` | float | 641 | 86.37% |
| `income_inferred` | float | 141 | 97.0% |
| `allowed_occupations` | string (semicolon-list) | 2,750 | 41.51% |
| `allowed_social_categories` | string (semicolon-list) | 785 | 83.3% |
| `required_disability_status` | string (semicolon-list) | 309 | 93.43% |
| `state_restricted_to_normalized` | string | 4,702 | 0% |
| `gender_restricted_to` | string | 4,702 | 0% |
| `is_national_scheme` | boolean | 4,702 | 0% |
| `eligibility_text_clean` | string | 4,702 | 0% |
| `benefit_summary` | string | 4,702 | 0% |
| `benefit_value_estimate` | string | 4,701 | 0.02% |
| `benefit_value_numeric` | float | 3,838 | 18.38% |
| `benefit_currency` | string (₹) | 4,702 | 0% |
| `required_documents` | string (semicolon-list) | 4,702 | 0% |
| `application_url` | string (URL) | 4,702 | 0% |
| `official_source_url` | string (URL) | 4,702 | 0% |
| `last_verified_date` | string (date) | 4,702 | 0% |
| `eligibility_verified` | boolean | 4,702 | 0% |
| `data_quality_score` | float | 4,702 | 0% |

### 3.3 Field Validation Summary

#### Age — **PRESENT (sparse)**
- `min_age`: 1,066 populated (22.7%); range 0–66; 13 rows with `min_age=0`
- `max_age`: 791 populated (16.8%); range 0–80; 2 rows with `max_age=0`
- `min_age_inferred` / `max_age_inferred`: 641 each; max inferred age up to 180 (suspicious)
- 633 schemes have both `min_age` and `max_age`
- **36.5%** of schemes have at least one age field (primary or inferred)

#### Income — **PRESENT (sparse)**
- `max_annual_income`: 793 populated (16.9%); range ₹3,600–₹20,00,000
- `income_inferred`: 141 populated (3%); one outlier at ₹5B
- **19.9%** have any income field

#### Gender — **PRESENT**
- Values: `any` (4,238), `female` (448), `male` (16)
- Fully populated

#### Category (Social) — **PRESENT (sparse)**
- `allowed_social_categories`: 785 schemes (16.7%)
- Tokens: `sc`, `st`, `obc`, `ews`, `general`

#### Occupation — **PRESENT (moderate)**
- `allowed_occupations`: 2,750 schemes (58.5%)
- Tokens: `farmer`, `student`, `daily_wage`, `self_employed`, `unemployed`, `salaried`

#### State — **PRESENT (well-normalized)**
- 37 unique values including `All India` and all states/UTs
- 4,005 schemes (85.2%) are state/UT-specific; 697 national

#### Benefit — **PRESENT (quality issues)**
- `benefit_summary`: 100% populated (free text)
- `benefit_value_numeric`: 81.6% populated; mean skewed by outliers; 227 rows = 1 (placeholder)
- `benefit_value_estimate`: human-readable companion
- **MISSING:** `benefit_frequency`, `benefit_type` (monetary vs non-monetary vs in-kind vs subsidy vs loan)

#### Eligibility — **PRESENT (dual-layer)**
- Structured fields (sparse) + `eligibility_text_clean` (100%, avg 634 chars)
- 47 schemes with very short eligibility text (<50 chars)
- 946 schemes with **no structured eligibility fields at all**
- `eligibility_verified`: only **20 True** (0.4%) — seed schemes

#### Documents — **PRESENT (coverage concern)**
- 100% populated with semicolon-separated tokens
- 10 document types; avg 3.31 documents per scheme
- 313 schemes list only `aadhaar`
- Aadhaar appears in 79.8% of all schemes — likely partially inferred/defaulted

#### Scheme Category — **PRESENT**
- Raw: 10 categories; `women_child` maps to clean `women_and_child` (225 rows)
- Clean categories: agriculture, disability, education, employment, financial_inclusion, health, housing, other, pension, women_and_child

#### Application Information — **PARTIAL**
- `application_url`: 100%
- **MISSING:** step-by-step application process, offline/online mode, processing time

### 3.4 Missing Fields (Not in Dataset)

| Field | Why It Matters | How It Should Be Added |
|-------|----------------|------------------------|
| `benefit_frequency` | Wallet cannot show monthly/yearly/one-time | Extract from `benefit_summary` via NLP rules; manual tag for seed schemes |
| `benefit_type` | Cannot distinguish loan vs grant vs pension vs in-kind | Classifier on `benefit_summary` + manual review |
| `marital_status` | Widow schemes (184 mention in text) cannot be matched structurally | Add enum field; NLP extraction from eligibility text |
| `land_ownership` | Many farmer schemes require landholding | Boolean + NLP from text |
| `bpl_status` | Many NSAP schemes reference BPL | Boolean field |
| `application_process` | Readiness score incomplete | Text field from official sources |
| `document_optional_vs_required` | All docs treated equally today | Separate required/optional arrays |
| `eligibility_rules_structured` | AND/OR logic in text not machine-readable | JSON rules column post-NLP extraction |

---

## 4. Data Quality Issues

### 4.1 Highest-Risk Problems (Priority Order)

1. **Sparse structured eligibility (80%+ missing age/income)** — automated matching unreliable
2. **946 schemes with zero structured fields** — text-only eligibility
3. **Only 20 verified schemes** — low trust for production-like demo
4. **Benefit numeric placeholders (227 rows = 1)** and **864 missing** — wallet math wrong
5. **Benefit outliers (74 schemes > ₹1 crore; max ₹150B)** — aggregate totals meaningless without capping/type classification
6. **Document list likely over-assigned** — aadhaar on 79.8% may not reflect true requirements
7. **Inferred fields unreliable** — `max_age_inferred` up to 180; `income_inferred` placeholders
8. **Category inconsistency** — `women_child` vs `women_and_child`
9. **Complex eligibility in free text** — AND/OR, temporal conditions, event-triggered (death, crop loss) not structured
10. **No benefit frequency/type** — cannot build accurate Benefit Wallet

### 4.2 Formatting Inconsistencies

- Scheme names with embedded quotes (e.g., row 22 `ira-wrflsncs`)
- `benefit_summary` contains markdown (`>`, `**`)
- `benefit_value_estimate` uses mixed formats (ranges, percentages, prose)
- `eligibility_text_clean` uses numbered lists inconsistently (`1.`, `-`, `>`)

### 4.3 Invalid/Suspicious Values

| Issue | Count |
|-------|-------|
| `benefit_value_numeric = 1` (placeholder) | 227 |
| `benefit_value_numeric` missing | 864 |
| `min_age = 0` | 13 |
| `max_age = 0` | 2 |
| `max_age_inferred > 120` | present |
| `income_inferred = 1` | 73 |
| `data_quality_score < 70` | 1,173 (24.9%) |

### 4.4 Duplicate Analysis

No duplicate rows, IDs, or names detected. Dataset integrity at scheme level is good.

---

## 5. Data Cleaning Strategy

See **`cleaning_plan.md`** for the full step-by-step plan. Summary:

1. Load CSV into SQLite with audit trail
2. Normalize categories, states, gender, occupations, social categories
3. Coalesce age/income from primary + inferred with confidence flags
4. Parse and validate `required_documents` tokens
5. Classify benefits (type, frequency) from text
6. Cap or exclude non-individual benefit amounts (institutional subsidies)
7. Flag unverified schemes; prioritize 20 seed schemes
8. Never invent eligibility — mark `unknown` where data insufficient

---

## 6. Recommended Dataset Schema

See **`architecture_plan.md` Section 4** for full schema. Key additions:

- `benefit_type`, `benefit_frequency`, `benefit_is_individual`
- `eligibility_confidence`, `rules_json`
- `marital_status_required`, `bpl_required`, `land_required`
- `documents_required[]`, `documents_optional[]`
- `data_source_tier` (verified / extracted / inferred)

---

## 7. Database Schema

See **`architecture_plan.md` Section 5**.

**MVP recommendation:** SQLite with normalized tables for schemes, eligibility rules, benefits, documents, user profiles, and readiness snapshots.

---

## 8. Eligibility Engine Design

See **`architecture_plan.md` Section 6**.

**Approach:** Hybrid rule engine with explainable pass/fail/unknown per criterion.

---

## 9. Missing Document Logic

See **`architecture_plan.md` Section 7**.

**Key gap:** Documents are listed but not marked required vs optional; 313 schemes only require aadhaar (likely under-specified).

---

## 10. Readiness Score Design

See **`architecture_plan.md` Section 8**.

**Formula (0–100):** Weighted combination of profile completeness (25%), eligibility confidence (30%), document readiness (30%), application info availability (15%).

---

## 11. Future Opportunities Design

See **`architecture_plan.md` Section 9**.

**Approach:** Identify schemes where exactly one or two structured criteria fail (e.g., age 17 vs min 18), with explicit "what would change" — no speculative predictions.

---

## 12. Complete Product Architecture

See **`architecture_plan.md` Section 10**.

---

## 13. Data Flow

```
User Profile (Streamlit form)
    │
    ▼
POST /api/profile  ──►  Store in SQLite (user_profiles)
    │
    ▼
POST /api/analyze  ──►  Eligibility Engine
    │                      ├── Structured rule match
    │                      └── Text fallback (confidence scored)
    │
    ├──► Eligible Schemes List
    ├──► Benefit Wallet (aggregate + per-scheme)
    ├──► Missing Documents (set diff)
    ├──► Readiness Score (weighted formula)
    └──► Future Opportunities (near-miss analysis)
    │
    ▼
Optional: AI/chatbot explains results in natural language
    │
    ▼
Optional: Translation layer localizes response
```

---

## 14. Missing Data / Gaps

| Gap | Product Feature Affected | Mitigation |
|-----|--------------------------|------------|
| 80% missing age/income | Eligible Schemes | NLP + ask user; show confidence |
| No benefit frequency/type | Benefit Wallet | Text classification; show "estimated" |
| No application steps | Readiness Score | Link to URL only; lower score |
| Unverified eligibility | All features | Badge "unverified"; prioritize 20 seed schemes |
| No marital/BPL/land fields | Eligibility | Profile questions + text extraction |
| Document over-assignment | Missing Documents | Show "likely required" vs "confirmed required" |

---

## 15. Security and Privacy Considerations

- **PII:** User profiles contain age, income, gender, caste category, disability, state — treat as sensitive
- **Storage:** MVP SQLite local; production needs encryption at rest
- **Transport:** HTTPS in deployment; CORS restricted to frontend origin
- **Consent:** Explicit consent before storing profile; option to use session-only (no persistence)
- **Aadhaar:** Never collect or store Aadhaar numbers — only document possession flags
- **Data minimization:** Collect only fields needed for matching
- **Audit:** Log eligibility decisions for explainability, not for profiling
- **Translation API:** `googletrans` sends text to Google — disclose to users; consider offline models for sensitive fields
- **Voice (SpeechRecognition):** Audio may leave device — document in privacy notice

---

## 16. Hackathon MVP Roadmap

See **`architecture_plan.md` Section 11**.

---

## 17. Recommended Development Order

1. Data cleaning pipeline → SQLite
2. Pydantic models (UserProfile, Scheme, EligibilityResult)
3. Structured eligibility engine (seed schemes first)
4. Backend API routes
5. Streamlit profile form + results dashboard
6. Document checker + readiness score
7. Future opportunities (near-miss)
8. Benefit wallet with type/frequency labels
9. Chatbot explanation layer
10. Translation (if time permits)

---

## 18. Risks and Potential Failure Points

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| False eligibility from incomplete data | High | High | Confidence scores + "verify officially" disclaimers |
| Benefit totals wildly inaccurate | High | Medium | Exclude institutional schemes; show ranges not sums |
| Document list wrong | Medium | High | Label document confidence; link to official source |
| Text parsing errors | High | Medium | Hybrid approach; human-verified seed set for demo |
| Frontend/backend integration delays | Medium | High | Start with monolithic Streamlit + shared Python modules |
| Over-scoping AI chatbot | High | Medium | Chatbot explains pre-computed results only |
| googletrans rate limits / blocking | Medium | Low | Fallback to English; cache translations |
| User distrust of automated results | Medium | High | Explainability UI; official URLs prominent |

---

*End of analysis report. Companion documents: `cleaning_plan.md`, `architecture_plan.md`.*
