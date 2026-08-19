# Seva-AI — Architecture & Product Design Plan

**Version:** 1.0 (Hackathon MVP)  
**Dataset:** `Data/indian_government_schemes.csv` (4,702 schemes)

---

## Part A — Clean Data Schema

### A. Existing Fields — Direct Use

| Field | Type | Purpose | Example | Required | Feature |
|-------|------|---------|---------|----------|---------|
| `scheme_id` | TEXT | Unique identifier | `pm-kisan-001` | Yes | All |
| `scheme_name` | TEXT | Display name | PM-KISAN Samman Nidhi | Yes | All |
| `scheme_category_clean` | TEXT | Filter/browse | `agriculture` | Yes | Eligible Schemes |
| `issuing_authority_normalized` | TEXT | Trust/source display | Ministry of Agriculture | Yes | All |
| `state_restricted_to_normalized` | TEXT | State filter | `Odisha` | Yes | Eligibility |
| `gender_restricted_to` | TEXT | Gender filter | `female` | Yes | Eligibility |
| `is_national_scheme` | BOOLEAN | National vs state | `True` | Yes | Eligibility |
| `eligibility_text_clean` | TEXT | Full rules (NLP/fallback) | Bullet list | Yes | Eligibility, Future |
| `benefit_summary` | TEXT | Human benefit description | Income support of ₹6,000... | Yes | Benefit Wallet |
| `benefit_value_estimate` | TEXT | Display amount/range | ₹6,000/year | No | Benefit Wallet |
| `application_url` | URL | Apply link | https://pmkisan.gov.in/ | Yes | Readiness |
| `official_source_url` | URL | Verification link | https://pmkisan.gov.in/ | Yes | All |
| `last_verified_date` | DATE | Freshness | 2026-07-10 | Yes | Trust |
| `eligibility_verified` | BOOLEAN | Manual verification flag | `True` | Yes | Confidence |
| `data_quality_score` | REAL | Quality tier | 88.2 | Yes | Confidence |

### B. Existing Fields — Need Cleaning/Transformation

| Field | Transform | Output | Feature |
|-------|-----------|--------|---------|
| `min_age`, `max_age`, `*_inferred` | Coalesce + validate | `min_age_effective`, `max_age_effective` | Eligibility |
| `max_annual_income`, `income_inferred` | Coalesce + validate | `max_income_effective` | Eligibility |
| `allowed_occupations` | Parse semicolon list | `occupations[]` | Eligibility |
| `allowed_social_categories` | Parse semicolon list | `social_categories[]` | Eligibility |
| `required_disability_status` | Parse semicolon list | `disability_types[]` | Eligibility |
| `required_documents` | Parse + validate tokens | `documents_required[]` | Missing Documents |
| `benefit_value_numeric` | Null placeholders, flag institutional | `benefit_amount_effective` | Benefit Wallet |
| `benefit_currency` | ₹ → INR | `benefit_currency` | Benefit Wallet |
| `scheme_category` | Map women_child | Use `scheme_category_clean` only | Browse |

### C. New Fields to Add

| Field | Type | Purpose | Example | Required | Feature |
|-------|------|---------|---------|----------|---------|
| `benefit_type` | ENUM | Monetary vs non-monetary | `cash_grant` | No | Benefit Wallet |
| `benefit_frequency` | ENUM | Payment cadence | `yearly` | No | Benefit Wallet |
| `benefit_is_institutional` | BOOLEAN | Exclude from individual totals | `false` | No | Benefit Wallet |
| `eligibility_confidence` | REAL 0-1 | Match reliability | 0.92 | Yes | All |
| `eligibility_rules_json` | JSON | Structured rules for engine | `{...}` | No | Eligibility |
| `bpl_required` | BOOLEAN | BPL condition | `true` | No | Eligibility |
| `marital_status_required` | ENUM | widow/divorced/any | `widow` | No | Eligibility |
| `land_required` | BOOLEAN | Farmer land condition | `true` | No | Eligibility |
| `documents_suggested` | JSON array | Text-extracted docs | `["land_record"]` | No | Missing Documents |
| `documents_confidence` | REAL 0-1 | Doc list reliability | 0.7 | No | Missing Documents |
| `data_tier` | ENUM | verified/high/medium/low | `verified` | Yes | All |
| `applicant_type` | ENUM | citizen/institution/enterprise | `citizen` | Yes | Eligibility |
| `trigger_event` | TEXT | Event-based schemes | `death_of_breadwinner` | No | Future Opportunities |

---

## Part B — Database Design (SQLite MVP)

### Entity Relationship Overview

```
user_profiles ──< eligibility_results >── schemes
      │                                      │
      │                                      ├── scheme_benefits
      │                                      ├── scheme_documents
      │                                      └── scheme_eligibility_rules
      │
      ├── user_documents
      └── readiness_snapshots
```

### Table: `schemes`

| Column | Type | PK/FK | Notes |
|--------|------|-------|-------|
| scheme_id | TEXT | PK | |
| scheme_name | TEXT | | |
| category | TEXT | | indexed |
| issuing_authority | TEXT | | |
| state | TEXT | | indexed |
| is_national | BOOLEAN | | |
| gender | TEXT | | |
| eligibility_text | TEXT | | |
| eligibility_verified | BOOLEAN | | |
| eligibility_confidence | REAL | | |
| benefit_summary | TEXT | | |
| benefit_amount | REAL | | nullable |
| benefit_type | TEXT | | |
| benefit_frequency | TEXT | | |
| benefit_is_institutional | BOOLEAN | | |
| application_url | TEXT | | |
| official_source_url | TEXT | | |
| last_verified_date | DATE | | |
| data_quality_score | REAL | | |
| data_tier | TEXT | | indexed |
| applicant_type | TEXT | | default 'citizen' |

**Indexes:** `category`, `state`, `data_tier`, `is_national`

### Table: `scheme_eligibility_rules`

| Column | Type | PK/FK |
|--------|------|-------|
| id | INTEGER | PK |
| scheme_id | TEXT | FK → schemes |
| rule_type | TEXT | age_min, age_max, income_max, occupation, category, disability, gender, state, bpl, marital, land |
| operator | TEXT | eq, in, lte, gte, between |
| value | TEXT | JSON-encoded |
| is_hard_requirement | BOOLEAN | |
| source | TEXT | structured, text_extracted, manual |

**Indexes:** `scheme_id`, `rule_type`

### Table: `scheme_documents`

| Column | Type | PK/FK |
|--------|------|-------|
| id | INTEGER | PK |
| scheme_id | TEXT | FK → schemes |
| document_type | TEXT | aadhaar, etc. |
| is_required | BOOLEAN | |
| source | TEXT | structured, suggested |
| confidence | REAL | |

**Indexes:** `scheme_id`, `document_type`

### Table: `user_profiles`

| Column | Type | PK/FK |
|--------|------|-------|
| user_id | TEXT | PK (UUID) |
| created_at | TIMESTAMP | |
| age | INTEGER | nullable |
| gender | TEXT | nullable |
| state | TEXT | nullable |
| annual_income | INTEGER | nullable |
| social_category | TEXT | nullable |
| occupation | TEXT | nullable |
| disability_type | TEXT | nullable |
| marital_status | TEXT | nullable |
| is_bpl | BOOLEAN | nullable |
| has_land | BOOLEAN | nullable |
| profile_completeness | REAL | computed |

### Table: `user_documents`

| Column | Type | PK/FK |
|--------|------|-------|
| id | INTEGER | PK |
| user_id | TEXT | FK → user_profiles |
| document_type | TEXT | |
| has_document | BOOLEAN | |
| verified | BOOLEAN | default false |

**Indexes:** `user_id`

### Table: `eligibility_results`

| Column | Type | PK/FK |
|--------|------|-------|
| id | INTEGER | PK |
| user_id | TEXT | FK |
| scheme_id | TEXT | FK |
| status | TEXT | eligible, ineligible, partial, unknown |
| confidence | REAL | |
| explanation_json | TEXT | |
| computed_at | TIMESTAMP | |

**Indexes:** `user_id`, `scheme_id`, `status`

### Table: `readiness_snapshots`

| Column | Type | PK/FK |
|--------|------|-------|
| id | INTEGER | PK |
| user_id | TEXT | FK |
| scheme_id | TEXT | FK |
| score | INTEGER | 0-100 |
| factors_json | TEXT | |
| computed_at | TIMESTAMP | |

---

## Part C — Eligibility Engine Design

### C.1 Input User Profile

```python
UserProfile = {
    "age": int | null,
    "gender": "male" | "female" | "other" | null,
    "state": str | null,           # e.g. "Odisha"
    "annual_income": int | null,   # INR
    "social_category": "sc"|"st"|"obc"|"ews"|"general"|null,
    "occupation": str | null,
    "disability_type": str | null,
    "marital_status": str | null,
    "is_bpl": bool | null,
    "has_land": bool | null,
    "documents_held": list[str]
}
```

### C.2 Eligibility Rules (Per Scheme)

Each rule produces: `PASS | FAIL | UNKNOWN | NOT_APPLICABLE`

| Rule | Logic | Unknown When |
|------|-------|--------------|
| State | user.state in scheme.state OR scheme.is_national | user.state missing |
| Gender | user.gender == scheme.gender OR scheme.gender == 'any' | user.gender missing AND scheme restricts |
| Age min | user.age >= min_age | user.age missing |
| Age max | user.age <= max_age | user.age missing |
| Income | user.income <= max_income | user.income missing |
| Occupation | user.occupation in allowed[] | user.occupation missing |
| Category | user.category in allowed[] | user.category missing |
| Disability | user.disability in required[] | user.disability missing |

### C.3 Rule Matching Logic

```
FOR each scheme:
  IF scheme.applicant_type != 'citizen': SKIP (not for individuals)
  
  rules = get_rules(scheme)
  results = [evaluate(rule, profile) for rule in rules]
  
  hard_fails = [r for r in results if r == FAIL]
  unknowns = [r for r in results if r == UNKNOWN]
  passes = [r for r in results if r == PASS]
  
  IF any hard_fails:
    status = INELIGIBLE
  ELIF all applicable rules PASS:
    status = ELIGIBLE
  ELIF unknowns and no hard_fails:
    status = PARTIAL  # "may be eligible — complete profile"
  ELSE:
    status = UNKNOWN
```

### C.4 AND/OR Conditions

- **Default:** AND — all hard requirements must pass
- **OR groups:** Parsed from text where explicit ("SC or ST") → stored in `eligibility_rules_json` as rule groups
- **Preferences:** "Preference to women" → does NOT fail non-women; tagged as `bonus`

### C.5 Partial Matches

Status `PARTIAL` when:
- No failures but ≥1 UNKNOWN on hard criteria
- Show: "Add your income to confirm eligibility"

### C.6 Explanation Output

```json
{
  "scheme_id": "pm-kisan-001",
  "status": "ELIGIBLE",
  "confidence": 0.95,
  "checks": [
    {"criterion": "state", "result": "PASS", "detail": "All India scheme"},
    {"criterion": "occupation", "result": "PASS", "detail": "farmer matches farmer"},
    {"criterion": "income", "result": "PASS", "detail": "₹1,50,000 ≤ ₹2,00,000 limit"}
  ]
}
```

Or ineligible:

```json
{
  "status": "INELIGIBLE",
  "checks": [
    {"criterion": "gender", "result": "FAIL", "detail": "Scheme for female applicants only"}
  ]
}
```

### C.7 Confidence Score

```
confidence = (
  0.4 * structured_field_coverage +
  0.3 * eligibility_verified +
  0.2 * data_quality_score_normalized +
  0.1 * (1 - unknown_ratio)
)
```

---

## Part D — Missing Document Logic

### D.1 Required Documents Source Priority

1. `scheme_documents` where `is_required = true` AND `source = structured`
2. `scheme_documents` where `source = suggested` (lower confidence — show separately)

### D.2 Algorithm

```
FOR each eligible/partial scheme:
  required = get_required_documents(scheme_id)
  held = user.documents_held
  
  missing = required - held
  has = required ∩ held
  needs_verification = [d for d in has if not user.document_verified(d)]
  
  RETURN {
    "scheme_id": ...,
    "required": required,
    "has": has,
    "missing": missing,
    "needs_verification": needs_verification,
    "document_confidence": scheme.documents_confidence
  }
```

### D.3 Data Gap

- **No optional vs required distinction** in source data → all listed docs treated as required with confidence label
- **313 schemes** list only aadhaar — likely under-specified; show: "Official source may list additional documents"
- **No verification workflow data** — `needs_verification` based on user self-declaration only

### D.4 User-Facing Output

| Document | Status |
|----------|--------|
| Aadhaar | ✅ You have this |
| Income Certificate | ❌ Missing — needed for PM-KISAN |
| Ration Card | ⚠️ You reported having this; verification recommended |

---

## Part E — Readiness Score (0–100)

### E.1 Scoring Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Profile Completeness | 25% | % of relevant profile fields filled |
| Eligibility Confidence | 30% | Engine confidence for this scheme |
| Document Readiness | 30% | % required docs held |
| Application Info | 15% | Has application URL + official source |

### E.2 Formula

```
readiness = round(
  0.25 * profile_completeness * 100 +
  0.30 * eligibility_confidence * 100 +
  0.30 * (docs_held / max(docs_required, 1)) * 100 +
  0.15 * application_info_score * 100
)
```

Where:
- `profile_completeness` = filled relevant fields / relevant fields for scheme
- `application_info_score` = 1.0 if both URLs present, 0.5 if one, 0 if none

### E.3 Interpretation

| Score | Label | Citizen Message |
|-------|-------|-----------------|
| 80–100 | Ready | You can likely apply now. Verify documents and apply via the official link. |
| 60–79 | Almost Ready | A few documents or details missing. |
| 40–59 | Needs Work | Several requirements unmet. Review missing items. |
| 0–39 | Not Ready | Complete your profile and gather documents first. |

### E.4 Example Calculation

**PM-KISAN, user: age 35, farmer, income ₹150K, state Bihar, has aadhaar + ration card**

| Factor | Value | Points |
|--------|-------|--------|
| Profile completeness | 6/6 = 1.0 | 25 |
| Eligibility confidence | 0.95 | 28.5 |
| Document readiness | 2/2 = 1.0 | 30 |
| Application info | 1.0 | 15 |
| **Total** | | **98.5 → 99** |

---

## Part F — Future Opportunities Design

### F.1 Concept

Identify schemes where user is **currently ineligible** but **one deterministic change** would flip a failed criterion to passable — no speculative predictions.

### F.2 Near-Miss Detection

| Pattern | Example | Opportunity Message |
|---------|---------|---------------------|
| Age below min | User 17, scheme min 18 | "Eligible in 1 year when you turn 18" |
| Age above max | User 61, scheme max 60 | Not a future opportunity — permanent ineligibility |
| Income slightly above | User ₹2.1L, limit ₹2L | Not predicted — income may not decrease; show only if user could qualify with valid change |
| Missing occupation | User unemployed, scheme for farmers | "If you register as a farmer, you may qualify" — only if occupation change is realistic |
| State mismatch | User in Bihar, scheme Odisha-only | "Available if you are a resident of Odisha" |

### F.3 Rules (Conservative)

Include in Future Opportunities ONLY if:
1. Exactly 1–2 failed criteria
2. Failed criterion is **time-based (age)** OR **profile-completable** (missing field, not wrong value)
3. Do NOT include schemes where user fails gender, disability, or social category ( generally immutable)
4. Do NOT predict income changes

### F.4 Output Format

```json
{
  "scheme_id": "nmms-007",
  "scheme_name": "National Means-cum-Merit Scholarship",
  "current_status": "INELIGIBLE",
  "blocking_criteria": ["age"],
  "what_could_change": "You will meet the minimum age (13) when you turn 13.",
  "relevant_attribute": "age",
  "current_value": 12,
  "required_value": "≥ 13"
}
```

---

## Part G — Complete Product Architecture

### G.1 Component Pipeline

```
┌─────────────────┐
│  User Profile   │  Streamlit form + session/DB storage
└────────┬────────┘
         ▼
┌─────────────────┐
│ Eligibility     │  Backend service: structured rules + text fallback
│ Engine          │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Eligible        │  Filter status ∈ {ELIGIBLE, PARTIAL}
│ Schemes         │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Benefit Wallet  │  Sum individual benefits; group by type/frequency
└────────┬────────┘
         ▼
┌─────────────────┐
│ Document        │  Set diff: required − held
│ Checker         │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Readiness       │  Weighted 0–100 per scheme + overall
│ Score           │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Future          │  Near-miss analyzer on INELIGIBLE set
│ Opportunities   │
└─────────────────┘
```

### G.2 Component Placement

| Component | Frontend | Backend | AI | DB | Translation |
|-----------|----------|---------|-----|-----|-------------|
| User Profile | Form UI | API + validation | — | SQLite | Labels |
| Eligibility Engine | Results display | Core service | Text fallback NLP | Rules cache | — |
| Benefit Wallet | Charts/tables | Aggregation API | Summarize totals | schemes | Amount labels |
| Document Checker | Checklist UI | Set diff API | — | user_documents | Doc names |
| Readiness Score | Gauge/badge | Scoring API | Explain score | snapshots | — |
| Future Opportunities | Timeline/cards | Near-miss API | Explain conditions | schemes | — |
| Chatbot | Chat UI | Orchestration | LLM explains results | RAG context | Input/output |
| Dataset | — | Loaded at startup | RAG source | Source of truth | — |

### G.3 Recommended Backend Module Structure

```
Backend/
├── main.py
├── routes.py
├── models/
│   ├── profile.py
│   ├── scheme.py
│   └── results.py
├── services/
│   ├── data_loader.py
│   ├── eligibility_engine.py
│   ├── benefit_wallet.py
│   ├── document_checker.py
│   ├── readiness_scorer.py
│   └── future_opportunities.py
└── db/
    ├── schema.sql
    └── connection.py

AI/
└── chatbot.py          # Explains pre-computed results

Translation/
└── translator.py       # Wraps googletrans

Frontend/
└── app.py              # Streamlit multi-page app
```

### G.4 API Endpoints (Proposed)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/profile` | Create/update profile |
| GET | `/api/profile/{id}` | Get profile |
| POST | `/api/analyze` | Full pipeline run |
| GET | `/api/schemes/eligible` | Eligible schemes |
| GET | `/api/benefits/wallet` | Benefit wallet |
| GET | `/api/documents/missing` | Missing documents |
| GET | `/api/readiness` | Readiness scores |
| GET | `/api/opportunities/future` | Future opportunities |
| POST | `/api/chat` | Chatbot turn |
| GET | `/health` | Health check |

---

## Part H — Hackathon MVP Roadmap

### P0 — Must Have

| Feature | Goal | Files | Deps | Difficulty | Output | Testing |
|---------|------|-------|------|------------|--------|---------|
| Data pipeline | Clean CSV → SQLite | `Data/cleaning/clean_schemes.py`, `Backend/db/` | pandas | Medium | `schemes.db` | Row count, no dupes |
| User profile form | Collect age, state, income, gender, occupation, category | `Frontend/app.py`, `Backend/models/profile.py` | streamlit, pydantic | Easy | Working form | Submit + validate |
| Structured eligibility | Match on age, income, state, gender, occupation, category | `Backend/services/eligibility_engine.py` | sqlite | Hard | Eligible list + explanations | 20 seed schemes |
| Results dashboard | Show eligible schemes with reasons | `Frontend/app.py` | streamlit | Medium | Scheme cards | Manual test profiles |
| Official links | Every result links to application_url | `Frontend/app.py` | — | Easy | Clickable URLs | Spot check |

### P1 — Important

| Feature | Goal | Files | Deps | Difficulty | Output | Testing |
|---------|------|-------|------|------------|--------|---------|
| Benefit Wallet | Show per-scheme + total benefits | `Backend/services/benefit_wallet.py`, Frontend | pandas | Medium | Wallet view | Exclude institutional |
| Missing Documents | Compare required vs held | `Backend/services/document_checker.py` | — | Medium | Missing doc list | Known scheme docs |
| Readiness Score | 0–100 with breakdown | `Backend/services/readiness_scorer.py` | — | Medium | Score gauge | Formula unit tests |
| API routes | Connect frontend to backend | `Backend/routes.py` | fastapi | Medium | REST API | curl/httpx tests |
| Data quality badges | Show verified/unverified | Frontend | — | Easy | Badges | Visual check |

### P2 — Nice to Have

| Feature | Goal | Files | Deps | Difficulty | Output | Testing |
|---------|------|-------|------|------------|--------|---------|
| Future Opportunities | Near-miss age/profile gaps | `Backend/services/future_opportunities.py` | — | Medium | Opportunity cards | Age boundary cases |
| Chatbot | Explain results in natural language | `AI/chatbot.py` | LLM API | Hard | Chat UI | Ask "why eligible?" |
| Translation | Hindi/regional language UI | `Translation/translator.py` | googletrans | Medium | Translated labels | Sample strings |
| Voice input | Speech-to-text profile | Frontend | SpeechRecognition | Hard | Voice form | Manual |
| Text eligibility NLP | Parse eligibility_text | `Backend/services/nlp_extractor.py` | regex/LLM | Hard | More matches | Compare to manual |

---

## Part I — Recommended Development Order

```
Week/Day 1:  Data cleaning → SQLite → seed scheme validation
Day 2:       Pydantic models + eligibility engine (structured only)
Day 3:       FastAPI routes + Streamlit profile form
Day 4:       Results dashboard + benefit wallet + documents
Day 5:       Readiness score + future opportunities
Day 6:       Polish, badges, disclaimers, demo profiles
Day 7:       Chatbot/translation if time; rehearse demo
```

---

## Part J — Demo Profile Suggestions

| Profile | Expected Highlights |
|---------|---------------------|
| Female, 22, MP, low income | Ladli Behna, PMMVY, scholarships |
| Male, 45, farmer, All India | PM-KISAN, PMFBY, crop schemes |
| SC student, 17, ₹2L income | Scholarships, future age opportunities |
| Senior, 65, BPL | Old age pension |

---

*This architecture plan is design-only. No application code has been generated.*
