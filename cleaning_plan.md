# Seva-AI — Data Cleaning Plan

**Dataset:** `Data/indian_government_schemes.csv`  
**Rows:** 4,702 | **Columns:** 29  
**Status:** Plan only — **do not execute until approved**

---

## 1. Objectives

1. Produce a **production-ready cleaned dataset** suitable for rule-based eligibility matching
2. Preserve **provenance** — every transformed value must trace to source column + method
3. **Never invent** eligibility rules, benefit amounts, or document requirements
4. Flag uncertainty explicitly rather than filling gaps with guesses

---

## 2. Cleaning Pipeline Overview

```
Raw CSV
  │
  ├─► Stage 1: Ingest & Validate Schema
  ├─► Stage 2: Deduplicate & Key Integrity
  ├─► Stage 3: Categorical Standardization
  ├─► Stage 4: Numeric Normalization (age, income, benefits)
  ├─► Stage 5: Multi-Value Field Parsing (occupations, docs, categories)
  ├─► Stage 6: Eligibility Coalescence (primary + inferred)
  ├─► Stage 7: Benefit Classification (type, frequency, individual vs institutional)
  ├─► Stage 8: Document Validation
  ├─► Stage 9: Quality Scoring & Tier Assignment
  └─► Stage 10: Export to SQLite + cleaned CSV
```

---

## 3. Missing-Value Handling

### 3.1 Do Not Impute (Leave Null + Flag)

| Column | Rationale |
|--------|-----------|
| `min_age`, `max_age` | Inventing age limits creates false eligibility |
| `max_annual_income` | Income thresholds must come from official data |
| `allowed_social_categories` | Category restrictions are legally sensitive |
| `required_disability_status` | Cannot assume disability requirement |

**Action:** Set `eligibility_field_status = 'missing'` in cleaned schema; engine returns `UNKNOWN` for that criterion.

### 3.2 Coalesce with Confidence Flag

| Primary | Fallback | Output Fields |
|---------|----------|---------------|
| `min_age` | `min_age_inferred` | `min_age_effective`, `min_age_source` (primary/inferred/none) |
| `max_age` | `max_age_inferred` | `max_age_effective`, `max_age_source` |
| `max_annual_income` | `income_inferred` | `max_income_effective`, `income_source` |

**Rules:**
- If inferred value is placeholder (`1`) → reject, treat as null
- If `max_age_inferred > 120` → reject as invalid
- If `income_inferred > ₹1 crore` without primary confirmation → flag `suspicious`, do not use for hard matching

### 3.3 Default Values (Safe Only)

| Column | Default | Condition |
|--------|---------|-----------|
| `gender_restricted_to` | Already complete | No action |
| `state_restricted_to_normalized` | Already complete | No action |
| `benefit_currency` | `INR` | Normalize `₹` symbol to ISO code |

### 3.4 Text Fields — Never Null-Fill

`eligibility_text_clean`, `benefit_summary` are 100% populated. Preserve verbatim; clean encoding only.

---

## 4. Duplicate Removal

**Current state:** Zero duplicates detected.

**Validation rules (run on every import):**
```python
assert df["scheme_id"].is_unique
assert df["scheme_name"].is_unique
assert df.duplicated().sum() == 0
```

**Near-duplicate detection (advisory only):**
- Fuzzy match on `scheme_name` (>95% similarity) → flag for manual review, do not auto-merge
- Same `application_url` + different `scheme_id` → flag potential split schemes

---

## 5. Categorical Standardization

### 5.1 Scheme Category

| Raw Value | Clean Value |
|-----------|-------------|
| `women_child` | `women_and_child` |
| All others | Use `scheme_category_clean` as canonical |

**Output:** Single column `category` (drop dual-column confusion in production DB).

### 5.2 State Names

**Current state:** Already well-normalized (37 values).

**Validation rules:**
- Must be in approved enum (All India + 36 states/UTs)
- Reject/flag any value not in enum
- Map user input aliases: `UP` → `Uttar Pradesh`, `DNHDD` → `Dadra and Nagar Haveli and Daman and Diu`

### 5.3 Gender

| Value | Canonical |
|-------|-----------|
| `any` | `any` |
| `female` | `female` |
| `male` | `male` |

Lowercase; reject unknown values.

### 5.4 Occupation Tokens

Approved enum: `farmer`, `student`, `daily_wage`, `self_employed`, `unemployed`, `salaried`

**Parsing:** Split on `;`, strip whitespace, lowercase, validate against enum. Unknown tokens → `occupation_parse_warnings[]`.

### 5.5 Social Category Tokens

Approved enum: `sc`, `st`, `obc`, `ews`, `general`

Same parsing rules as occupations.

### 5.6 Disability Tokens

Approved enum: `physical`, `visual`, `hearing`, `intellectual`, `multiple`

### 5.7 Issuing Authority

Use `issuing_authority_normalized` as canonical; retain raw for audit.

---

## 6. Income Normalization

### 6.1 Target Format

- **Type:** Integer (INR per annum)
- **Column:** `max_annual_income_effective`

### 6.2 Rules

1. Use `max_annual_income` if present and > 0
2. Else use `income_inferred` if present, not equal to 1, and ≤ ₹1,00,00,000
3. Else null + `income_status = 'unknown'`

### 6.3 Validation

| Check | Action |
|-------|--------|
| Value < ₹1,000 | Flag `suspicious_low` |
| Value > ₹50,00,000 | Flag `suspicious_high` — may be scheme budget not individual limit |
| Conflicting primary vs inferred (>20% difference) | Prefer primary; log conflict |

### 6.4 Text Extraction (Secondary Pass)

For rows with null income but eligibility text containing `₹X`, extract via regex — mark as `income_source = 'text_extracted'`, `confidence = low`. Do not use for hard exclusion without review.

---

## 7. Age-Range Normalization

### 7.1 Target Format

- `min_age_effective`: Integer or null
- `max_age_effective`: Integer or null

### 7.2 Rules

1. Coalesce primary → inferred with source tracking
2. Reject `min_age = 0` unless scheme is explicitly for infants (cross-check text for "girl child", "0-10" etc.)
3. Reject `max_age_inferred > 120`
4. If only `min_age` present → treat as open-ended upper bound
5. If only `max_age` present → treat as open-ended lower bound (min = null)

### 7.3 Validation

| Check | Action |
|-------|--------|
| `min_age > max_age` | Swap if inferred error; else flag `invalid_range` |
| Age range spans > 80 years | Flag for review |

---

## 8. Benefit Normalization

### 8.1 Numeric Cleaning

**Column:** `benefit_value_numeric` → `benefit_amount_effective`

| Condition | Action |
|-----------|--------|
| Null | Keep null; derive display from `benefit_value_estimate` text |
| Value = 1 | Treat as placeholder → null unless text confirms ₹1 benefit |
| Value > ₹1,00,00,000 | Set `benefit_is_institutional = true`; exclude from individual wallet totals |
| Value = 8.2 (Sukanya interest rate) | Set `benefit_type = 'interest_rate'`, not monetary amount |

### 8.2 Benefit Type Classification (New Field)

Extract from `benefit_summary` keywords:

| Type | Keywords |
|------|----------|
| `cash_grant` | assistance, grant, financial assistance |
| `pension` | pension, monthly |
| `scholarship` | scholarship, fellowship |
| `loan` | loan, collateral-free |
| `insurance` | insurance, cover, hospitalization |
| `subsidy` | subsidy, interest subsidy |
| `in_kind` | uniform, textbook, toolkit, supply |
| `insurance_pension` | combined patterns |
| `unknown` | no match |

### 8.3 Benefit Frequency Classification (New Field)

| Frequency | Keywords |
|-----------|----------|
| `one_time` | one-time, lumpsum, single installment |
| `monthly` | monthly, per month, /month |
| `yearly` | per year, annually, /year |
| `daily` | per day, daily wage |
| `variable` | up to, range, % |
| `unknown` | no match |

### 8.4 Currency

Normalize `₹` → `INR` in all outputs.

---

## 9. Eligibility-Field Normalization

### 9.1 Structured Eligibility Record (New JSON)

For each scheme, build:

```json
{
  "min_age": 18,
  "max_age": 60,
  "max_annual_income": 200000,
  "occupations": ["farmer"],
  "social_categories": [],
  "disability_types": [],
  "gender": "any",
  "state": "All India",
  "national": true,
  "conditions_logic": "AND",
  "unstructured_text": "...",
  "confidence": 0.85,
  "verified": false
}
```

### 9.2 Handling Ambiguous Eligibility Rules

| Scenario | Handling |
|----------|----------|
| Text says "preference to SC/ST" | Not a hard filter; tag `preference`, not `requirement` |
| Text says "must be BPL" | Set `bpl_required = true`; flag if no structured income |
| Text says "OR" conditions | Set `conditions_logic = 'OR'`; parse sub-rules where possible |
| Event-triggered (death, crop loss) | Tag `trigger_event`; exclude from standard profile matching |
| Institution eligibility (AICTE approved) | Tag `applicant_type = institution`; exclude from citizen matching |

**Rule:** When ambiguous → `eligibility_status = 'needs_review'`, not auto-eligible.

---

## 10. Document-Field Normalization

### 10.1 Parsing

Split `required_documents` on `;` → validate against approved enum:

```
aadhaar, ration_card, income_certificate, caste_certificate,
bank_passbook, domicile_certificate, education_marksheet,
voter_id, disability_certificate, land_record
```

### 10.2 Quality Flags

| Flag | Condition |
|------|-----------|
| `documents_likely_defaulted` | Only `aadhaar` listed AND eligibility text mentions other docs |
| `documents_over_assigned` | ≥5 docs AND `data_quality_score < 70` |
| `documents_from_text` | Extracted from eligibility text, not structured field |

### 10.3 Do Not Add Documents

If eligibility text mentions a document not in structured field → add to `documents_suggested[]` with `source = 'text'`, NOT to `documents_required[]`.

---

## 11. Validation Rules (Post-Clean)

### 11.1 Row-Level

- [ ] `scheme_id` non-empty, unique, lowercase slug format
- [ ] `scheme_name` non-empty
- [ ] `category` in approved enum
- [ ] `state` in approved enum
- [ ] `gender` in {any, female, male}
- [ ] `min_age_effective <= max_age_effective` when both present
- [ ] `benefit_amount_effective >= 0` when present
- [ ] At least one of: structured eligibility OR `eligibility_text_clean` length > 50

### 11.2 Dataset-Level

- [ ] Row count = 4,702 (unless explicitly dropping invalid rows with audit log)
- [ ] No duplicate scheme_ids
- [ ] ≥95% have `application_url` and `official_source_url`
- [ ] Document tokens 100% in approved enum

---

## 12. Recommended Final Data Types

| Field | Type | Notes |
|-------|------|-------|
| `scheme_id` | TEXT PK | |
| `scheme_name` | TEXT NOT NULL | |
| `category` | TEXT NOT NULL | enum |
| `issuing_authority` | TEXT | |
| `min_age_effective` | INTEGER NULL | |
| `max_age_effective` | INTEGER NULL | |
| `max_income_effective` | INTEGER NULL | INR/year |
| `occupations` | JSON array | |
| `social_categories` | JSON array | |
| `disability_types` | JSON array | |
| `gender` | TEXT | enum |
| `state` | TEXT | enum |
| `is_national` | BOOLEAN | |
| `eligibility_text` | TEXT | |
| `eligibility_verified` | BOOLEAN | |
| `eligibility_confidence` | REAL 0-1 | |
| `benefit_summary` | TEXT | |
| `benefit_amount_effective` | REAL NULL | |
| `benefit_type` | TEXT | enum |
| `benefit_frequency` | TEXT | enum |
| `benefit_is_institutional` | BOOLEAN | |
| `benefit_currency` | TEXT | default INR |
| `documents_required` | JSON array | |
| `documents_suggested` | JSON array | |
| `application_url` | TEXT | |
| `official_source_url` | TEXT | |
| `last_verified_date` | DATE | |
| `data_quality_score` | REAL | |
| `data_tier` | TEXT | verified / high / medium / low |

---

## 13. Handling Priority Tiers

| Tier | Criteria | Use in MVP |
|------|----------|------------|
| **T1 Verified** | `eligibility_verified = True` (20 schemes) | Full rule matching + demo |
| **T2 High Quality** | `data_quality_score >= 82` AND ≥3 structured fields | Rule matching |
| **T3 Medium** | Has eligibility text, some structured fields | Hybrid matching |
| **T4 Low** | No structured fields, low quality score | Text search only; show disclaimer |

---

## 14. Execution Checklist (When Approved)

- [ ] Create `Data/cleaning/` directory for scripts and logs
- [ ] Implement `clean_schemes.py` with staged pipeline
- [ ] Write unit tests for parsers (occupations, documents, benefits)
- [ ] Generate `Data/schemes_cleaned.csv`
- [ ] Generate `Data/schemes.db` (SQLite)
- [ ] Produce `Data/cleaning/audit_report.json` with counts per transformation
- [ ] Manual review of T1 schemes (20) and 50 random T3/T4 schemes
- [ ] Do NOT overwrite original CSV

---

## 15. Expected Outcomes After Cleaning

| Metric | Before | Expected After |
|--------|--------|----------------|
| Schemes with effective age | 36.5% | ~40% (with validated coalesce) |
| Schemes with effective income | 19.9% | ~22% (reject bad inferred) |
| Schemes with benefit type | 0% | ~85% (text classification) |
| Schemes with benefit frequency | 0% | ~60% (text classification) |
| Placeholder benefit amounts | 227 | 0 (nulled with flag) |
| Institutional benefits flagged | 0 | ~74+ |

---

*This plan does not modify any files. Execute only after team review.*
