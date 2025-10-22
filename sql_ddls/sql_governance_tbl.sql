-- Create the governance/audit table
CREATE TABLE IF NOT EXISTS super_advisory_demo.member_data.governance (
    event_id STRING COMMENT 'Unique identifier for each logged interaction',
    timestamp TIMESTAMP COMMENT 'UTC datetime of the interaction',
    user_id STRING COMMENT 'User ID, email, or session identifier',
    session_id STRING COMMENT 'Session identifier',
    country STRING COMMENT 'Country context (AU, US, UK, IN)',
    query_string STRING COMMENT 'The exact query or question asked',
    agent_response STRING COMMENT 'The answer or recommendation generated',
    result_preview STRING COMMENT 'Preview/snippet of main calculation result',
    cost DOUBLE COMMENT 'Estimated cost of computation/API calls',
    citations ARRAY<STRING> COMMENT 'List of citation references',
    tool_used STRING COMMENT 'Name/version of tool or calculator used',
    judge_response STRING COMMENT 'Judge LLM validation output',
    judge_verdict STRING COMMENT 'Verdict: Pass, Fail, Review, ERROR',
    error_info STRING COMMENT 'Error details or traceback if any error occurred'
)
USING DELTA
COMMENT 'Governance and audit log for all agent interactions'
PARTITIONED BY (country)
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- Verify it was created
DESCRIBE TABLE super_advisory_demo.member_data.governance;

