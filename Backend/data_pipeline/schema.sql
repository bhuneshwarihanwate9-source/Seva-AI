-- Seva-AI MySQL schema for government schemes (eligibility engine source)
-- Database creation is handled by load_to_mysql.py before this script runs.

CREATE TABLE IF NOT EXISTS schemes (
    scheme_id                 VARCHAR(128)  NOT NULL,
    scheme_name               VARCHAR(512)  NOT NULL,
    state                     VARCHAR(128)  NOT NULL,
    category                  VARCHAR(64)   NOT NULL,
    benefit_summary           TEXT          NOT NULL,
    eligibility_text_clean    TEXT          NOT NULL,
    gender                    VARCHAR(16)   NOT NULL DEFAULT 'any',
    min_age                   DECIMAL(5, 1) NULL,
    max_age                   DECIMAL(5, 1) NULL,
    max_annual_income         DECIMAL(15, 2) NULL,
    occupation_tokens         VARCHAR(256)  NULL,
    allowed_social_categories VARCHAR(128)  NULL,
    required_disability_status VARCHAR(256) NULL,
    benefit_value_numeric     DECIMAL(18, 2) NULL,
    confidence_score          DECIMAL(5, 4) NOT NULL DEFAULT 0.0000,
    application_url           TEXT          NOT NULL,
    official_source_url       TEXT          NOT NULL,
    PRIMARY KEY (scheme_id),
    INDEX idx_schemes_state (state),
    INDEX idx_schemes_category (category),
    INDEX idx_schemes_confidence_score (confidence_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
