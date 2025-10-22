# Multi-Country Retirement Advisory Application

A sophisticated agentic AI application for retirement and pension advisory across Australia, USA, UK, and India, built on Databricks with full governance, MLflow tracking, and Unity Catalog integration.

## Features

### Core Capabilities
- 🌍 **Multi-Country Support**: Australia, USA, UK, India with country-specific:
  - Prompts and questions
  - Regulations and citations
  - National color themes for UI
  - Retirement calculators and tools

- 🎨 **Dynamic UI**: 
  - Member cards styled in national colors (e.g., Australia: green & gold)
  - Country-specific disclaimers and guidance
  - Two-page interface (Advisory + Governance/Developer)

- 📊 **Full Observability**:
  - Unity Catalog audit logging (every interaction)
  - MLflow experiment tracking (prod and offline eval)
  - Judge LLM validation with error tracking
  - Cost estimation per query

- 🔒 **Governance & Compliance**:
  - Persistent audit trail in Unity Catalog
  - Change data feed enabled
  - Session and user tracking
  - Citations for regulatory and tool-based answers

### Pages

#### Page 1: Advisory Interface
- Country selector
- Member selection with themed cards
- Query input with recommendations
- Real-time progress (toggleable)
- Citations and disclaimers

#### Page 2: Governance & Developer
- **Governance Tab**: Unity Catalog audit logs with filtering
- **Developer Tab**: MLflow run traces and evaluation tools

## Architecture

```
Streamlit UI → Agent → Country-Specific Tools → Unity Catalog (Audit)
                ↓                                      ↓
              MLflow (Experiments)              Governance Table
```

### Tech Stack
- **UI**: Streamlit (≥1.37.0)
- **Compute**: Databricks
- **Storage**: Unity Catalog (Delta Tables)
- **Tracking**: MLflow
- **SDK**: Databricks SDK (≥0.20.0)

## Setup Instructions

### 1. Prerequisites
- Databricks Workspace with Unity Catalog enabled
- Access to create tables in Unity Catalog
- MLflow experiment permissions

### 2. Database Setup

Run these SQL scripts in a Databricks SQL Warehouse or notebook:

```sql
-- Create governance table for audit logging
CREATE TABLE IF NOT EXISTS super_advisory_demo.member_data.governance (
    event_id STRING,
    timestamp TIMESTAMP,
    user_id STRING,
    session_id STRING,
    country STRING,
    query_string STRING,
    agent_response STRING,
    result_preview STRING,
    cost DOUBLE,
    citations ARRAY<STRING>,
    tool_used STRING,
    judge_response STRING,
    judge_verdict STRING,
    error_info STRING
) USING DELTA
PARTITIONED BY (country)
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true'
);

-- Add country column to member_profiles
ALTER TABLE super_advisory_demo.member_data.member_profiles 
ADD COLUMN country STRING;

-- Set existing members to Australia
UPDATE super_advisory_demo.member_data.member_profiles
SET country = 'AU';

-- Update member IDs to country format
UPDATE super_advisory_demo.member_data.member_profiles
SET member_id = REPLACE(member_id, 'ART_', 'AU')
WHERE member_id LIKE 'ART_%';
```

See `sql/` folder for complete scripts including sample member inserts.

### 3. Configuration

Update `config.py` with your settings:

```python
# Unity Catalog
UNITY_CATALOG = "super_advisory_demo"
UNITY_SCHEMA = "member_data"

# MLflow Experiments
MLFLOW_PROD_EXPERIMENT_PATH = "/Shared/experiments/prod/retirement-advisory"
MLFLOW_OFFLINE_EVAL_PATH = "/Shared/experiments/offline/retirement-eval"
```

### 4. Deploy to Databricks Apps

1. Upload all files to your Databricks workspace:
   ```
   /Workspace/Users/your_email@company.com/agentic_app_with_judge/
   ```

2. Ensure `requirements.txt` is in the root directory

3. Create a new Databricks App:
   - Navigate to "Apps" in Databricks
   - Click "Create App"
   - Select your workspace folder
   - Choose `app.py` as the entry point
   - Databricks will automatically install requirements

4. Configure compute:
   - Recommended: Serverless compute or small cluster
   - Runtime: DBR 14.3 LTS or higher (with Unity Catalog support)

### 5. Verify Installation

Once deployed:
1. Open the app URL
2. Select a country (Australia, USA, UK, India)
3. Choose a member
4. Ask a test question
5. Check Page 2 → Governance tab for audit logs
6. Check Page 2 → Developer tab for MLflow runs

## File Structure

```
agentic_app_with_judge/
├── app.py                    # Main Streamlit application
├── agent.py                  # Agent orchestration
├── agent_processor.py        # Query processing
├── tools.py                  # Country calculators
├── ui_components.py          # UI components
├── config.py                 # Configuration
├── mlflow_utils.py           # MLflow helpers
├── progress_utils.py         # Progress display
├── run_evaluation.py         # Evaluation script
├── requirements.txt          # Python dependencies
├── country_content/          # Country-specific content
│   ├── prompts.py
│   ├── disclaimers.py
│   └── regulations.py
├── audit/                    # Audit utilities
│   └── audit_utils.py
└── sql/                      # Database scripts
```

## Usage

### Running Queries
1. Select your country from the dropdown
2. Choose a member from the list
3. Enter your retirement/pension question
4. Click "Get Recommendation"
5. View answer with citations and disclaimers

### Viewing Audit Logs
1. Navigate to "Audit/Governance" page
2. Select "Governance" tab
3. Filter by session, user, or country
4. Export logs if needed

### Developer Tools
1. Navigate to "Audit/Governance" page
2. Select "Developer" tab
3. View MLflow experiment runs
4. Run evaluations using `run_evaluation.py`

### Offline Evaluation

```bash
# From Databricks notebook or terminal
python run_evaluation.py --mode offline --csv_path /path/to/eval_data.csv
```

CSV format:
```csv
user_id,country,query_str,age,super_balance
user001,Australia,"How much can I withdraw?",65,450000
user002,USA,"What's my 401k distribution?",62,380000
```

## Customization

### Adding New Countries
1. Update `config.py` → `NATIONAL_COLORS`
2. Add entries in `country_content/prompts.py`
3. Add entries in `country_content/disclaimers.py`
4. Add entries in `country_content/regulations.py`
5. Create calculator function in `tools.py`
6. Update `get_country_tool()` function

### Integrating Judge LLM
Pass a judge function to `run_agent_interaction()`:

```python
def my_judge_llm(answer, query, country):
    # Your judge logic here
    return judge_response, verdict

agent_output = run_agent_interaction(
    ...,
    judge_llm_fn=my_judge_llm
)
```

### Custom Tools/Calculators
Add new functions in `tools.py` and register them in `get_country_tool()`.

## Troubleshooting

### Common Issues

**Error: "Table not found"**
- Run SQL scripts to create governance table
- Verify catalog and schema names in config.py

**Error: "MLflow experiment not found"**
- Create experiments in Databricks workspace
- Update paths in config.py

**No audit logs appearing**
- Check Unity Catalog permissions
- Verify Spark session is active
- Check error_info column in governance table

**Member profiles not loading**
- Verify member_profiles table exists
- Check country column has been added
- Ensure members have country values set

## Support

For issues or questions:
- Check inline code documentation
- Review audit logs for errors
- Contact: support@example.com

## License

Internal use only - [Your Company Name]
