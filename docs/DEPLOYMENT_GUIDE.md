# Deployment Guide

## Overview

This guide covers deployment of the Multi-Country Pension Advisor system on Databricks using Databricks Asset Bundles (DABS) for infrastructure and Databricks Apps for the Streamlit application.

## Architecture Components

The system consists of:
1. **SQL Infrastructure**: Unity Catalog schemas, tables, and SQL functions
2. **Python Application**: Streamlit UI and agent logic
3. **MLflow**: Experiment tracking and prompt registry
4. **Monitoring**: Lakehouse Monitoring setup

## Deployment Method

### DABS + Databricks Apps

Use Databricks Asset Bundles (DABS) for infrastructure and Databricks Apps for Streamlit deployment. This is the recommended approach for production Databricks environments.

---

## Part 1: DABS Configuration

### Prerequisites

```bash
# Install Databricks CLI
pip install databricks-cli

# Install DABS
pip install databricks-assets

# Authenticate
databricks auth login
```

### DABS Project Structure

Create the following structure:

```
databricks-assets/
├── databricks.yml
├── resources/
│   ├── sql/
│   │   ├── super_advisory_demo_schema.sql
│   │   └── super_advisory_demo_functions.sql
│   └── jobs/
│       └── prompt_registry.yml
└── src/
    └── prompts_registry.py
```

### databricks.yml

```yaml
bundle:
  name: pension-advisor
  resources:
    sql:
      schemas:
        super_advisory_demo:
          databases:
            - name: member_data
              path: resources/sql/super_advisory_demo_schema.sql
            - name: pension_calculators
              path: resources/sql/super_advisory_demo_functions.sql
    
    jobs:
      prompt_registry_job:
        name: Register Prompts
        tasks:
          - task_key: register_prompts
            python_wheel_task:
              package_name: pension-advisor
              entry_point: prompts_registry.register_prompts_with_mlflow
              parameters: []
            libraries:
              - whl: "file://src/prompts_registry.py"
            new_cluster:
              spark_version: "13.3.x-scala2.12"
              node_type_id: "i3.xlarge"
              num_workers: 0
```

### Deploy with DABS

```bash
# Validate configuration
databricks bundle validate

# Deploy
databricks bundle deploy

# Deploy to specific environment
databricks bundle deploy --target production
```

---

## Part 2: Streamlit App Deployment

### Deploy to Databricks Apps

Deploy Streamlit app as a Databricks App using `app.yaml`.

#### GitHub Secrets Required

```
DATABRICKS_HOST
DATABRICKS_TOKEN
DATABRICKS_WORKSPACE_PATH
```

#### .github/workflows/deploy-databricks-app.yml

```yaml
name: Deploy to Databricks Apps

on:
  push:
    branches: [ main, develop ]
  workflow_dispatch:

jobs:
  deploy-infrastructure:
    name: Deploy Infrastructure (DABS)
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install DABS
        run: |
          pip install databricks-cli databricks-assets
      
      - name: Authenticate Databricks
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          databricks auth login --host $DATABRICKS_HOST --token $DATABRICKS_TOKEN
      
      - name: Deploy SQL Infrastructure
        run: |
          # Deploy schemas and functions
          databricks bundle deploy --target production
  
  deploy-application:
    name: Deploy Streamlit App
    needs: deploy-infrastructure
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install databricks-cli
          pip install -r requirements.txt
      
      - name: Authenticate Databricks
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          databricks auth login --host $DATABRICKS_HOST --token $DATABRICKS_TOKEN
      
      - name: Upload files to workspace
        env:
          DATABRICKS_WORKSPACE_PATH: ${{ secrets.DATABRICKS_WORKSPACE_PATH }}
        run: |
          # Upload application files
          databricks workspace import_dir . "$DATABRICKS_WORKSPACE_PATH/app" \
            --exclude-hidden-files \
            --exclude '*.md' \
            --exclude '__pycache__' \
            --exclude '.git'
      
      - name: Deploy Databricks App
        env:
          DATABRICKS_WORKSPACE_PATH: ${{ secrets.DATABRICKS_WORKSPACE_PATH }}
        run: |
          # Note: Databricks Apps deployment via CLI may require additional setup
          # This step uploads files - app.yaml will be used by Databricks Apps platform
          echo "App files uploaded. Configure Databricks Apps in UI using app.yaml"
          echo "App location: $DATABRICKS_WORKSPACE_PATH/app/app.yaml"
```

**Limitations**: Databricks Apps deployment via CLI is limited. You may need to:
1. Upload files via this workflow
2. Manually configure the app in Databricks UI using `app.yaml`

---

## Part 3: Environment Configuration

### GitHub Secrets Setup

Configure the following secrets in your GitHub repository:

**For Databricks**:
- `DATABRICKS_HOST`: Your Databricks workspace URL (e.g., `https://your-workspace.cloud.databricks.com`)
- `DATABRICKS_TOKEN`: Personal access token or service principal token
- `DATABRICKS_WORKSPACE_PATH`: Workspace path for app (e.g., `/Workspace/Users/user@example.com/app`)

### Environment Variables

Create `.env` files for different environments:

**.env.production**:
```
DATABRICKS_HOST=https://prod-workspace.cloud.databricks.com
MLFLOW_PROD_EXPERIMENT_PATH=/Users/prod@company.com/prod-retirement-advisory
SQL_WAREHOUSE_ID=prod-warehouse-id
```

**.env.development**:
```
DATABRICKS_HOST=https://dev-workspace.cloud.databricks.com
MLFLOW_PROD_EXPERIMENT_PATH=/Users/dev@company.com/dev-retirement-advisory
SQL_WAREHOUSE_ID=dev-warehouse-id
```

---

## Part 4: Post-Deployment Steps

### 1. Verify Infrastructure

```bash
# Check Unity Catalog schemas
databricks sql execute --query "SHOW SCHEMAS IN super_advisory_demo"

# Check SQL functions
databricks sql execute --query "SHOW FUNCTIONS IN super_advisory_demo.pension_calculators"

# Verify tables
databricks sql execute --query "SHOW TABLES IN super_advisory_demo.member_data"
```

### 2. Initialize MLflow

```python
from prompts_registry import PromptsRegistry

registry = PromptsRegistry()
registry.register_prompts_with_mlflow(run_name="prompts_v1.0.0")
```

### 3. Setup Lakehouse Monitoring

```python
from observability import create_observability

obs = create_observability(
    enable_mlflow=True,
    enable_lakehouse_monitoring=True
)

monitor = obs.setup_lakehouse_monitoring(
    schedule="0 0 * * *"  # Daily at midnight
)
```

### 4. Test Application

1. Access Streamlit app via Databricks Apps
2. Run a test query
3. Verify governance logging
4. Check MLflow experiment tracking

---

## Part 5: Troubleshooting

### Common Issues

**Issue**: DABS deployment fails
- **Solution**: Verify `databricks.yml` syntax and workspace permissions

**Issue**: Streamlit app not accessible
- **Solution**: Check Databricks Apps configuration and ensure app.yaml is properly configured

**Issue**: MLflow experiments not found
- **Solution**: Verify experiment path in `config.py` matches workspace

**Issue**: Unity Catalog permissions denied
- **Solution**: Ensure service principal or user has appropriate permissions

### Debugging Commands

```bash
# Check Databricks CLI authentication
databricks auth test

# List workspace files
databricks workspace ls /Workspace/Users/

# Check deployed bundles
databricks bundle list
```

---

## Additional Resources

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Databricks CLI Documentation](https://docs.databricks.com/dev-tools/cli/index.html)
- [Databricks Apps Documentation](https://docs.databricks.com/apps/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
