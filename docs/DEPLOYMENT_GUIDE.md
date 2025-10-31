# Deployment Guide

## Overview

This guide covers deployment options for the Multi-Country Pension Advisor system on Databricks. All deployment methods use Databricks-native tools and services.

## Architecture Components

The system consists of:
1. **SQL Infrastructure**: Unity Catalog schemas, tables, and SQL functions
2. **Python Application**: Streamlit UI and agent logic
3. **MLflow**: Experiment tracking and prompt registry
4. **Monitoring**: Lakehouse Monitoring setup

## Deployment Options

### Option 1: DABS + Databricks Apps (Recommended)

Use Databricks Asset Bundles (DABS) for infrastructure and Databricks Apps for Streamlit deployment.

**Best for**: Production Databricks environments requiring native integration

### Option 2: DABS + Workspace Files + Jobs

Use DABS for infrastructure and deploy Streamlit app to workspace files, then run as a Databricks Job.

**Best for**: CI/CD pipelines and automated deployments

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

### Option 1: Deploy to Databricks Apps

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
  deploy:
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

### Option 2: Deploy to Workspace Files + Run as Job

Deploy files to workspace and create a Databricks Job to run Streamlit.

#### .github/workflows/deploy-workspace-job.yml

```yaml
name: Deploy to Databricks Workspace (Job)

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
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
          pip install databricks-cli databricks-sdk
          pip install -r requirements.txt
      
      - name: Authenticate Databricks
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          databricks auth login --host $DATABRICKS_HOST --token $DATABRICKS_TOKEN
      
      - name: Upload application files
        env:
          DATABRICKS_WORKSPACE_PATH: ${{ secrets.DATABRICKS_WORKSPACE_PATH }}
        run: |
          # Upload main application
          databricks workspace import_dir . "$DATABRICKS_WORKSPACE_PATH/app" \
            --exclude-hidden-files \
            --exclude '*.md' \
            --exclude '__pycache__' \
            --exclude '.git' \
            --exclude 'docs' \
            --exclude 'sql_ddls'
      
      - name: Create/Update Databricks Job
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
          DATABRICKS_WORKSPACE_PATH: ${{ secrets.DATABRICKS_WORKSPACE_PATH }}
        run: |
          python << EOF
          from databricks.sdk import WorkspaceClient
          from databricks.sdk.service.jobs import JobSettings, Task, NotebookTask
          
          w = WorkspaceClient(host="$DATABRICKS_HOST", token="$DATABRICKS_TOKEN")
          
          job_settings = JobSettings(
              name="Pension Advisor Streamlit App",
              tasks=[
                  Task(
                      task_key="run_streamlit",
                      notebook_task=NotebookTask(
                          notebook_path="$DATABRICKS_WORKSPACE_PATH/app/run_streamlit.py"
                      ),
                      new_cluster={
                          "spark_version": "13.3.x-scala2.12",
                          "node_type_id": "i3.xlarge",
                          "num_workers": 0,
                          "spark_conf": {
                              "spark.databricks.cluster.profile": "singleNode"
                          }
                      },
                      libraries=[
                          {"pypi": {"package": "streamlit>=1.37.0"}},
                          {"pypi": {"package": "mlflow>=2.8.0"}},
                          {"pypi": {"package": "databricks-sdk>=0.12.0"}},
                          {"pypi": {"package": "pandas>=2.0.0"}},
                          {"pypi": {"package": "plotly>=5.14.0"}}
                      ]
                  )
              ],
              max_concurrent_runs=1
          )
          
          # Check if job exists
          jobs = w.jobs.list()
          existing_job = None
          for job in jobs:
              if job.settings.name == "Pension Advisor Streamlit App":
                  existing_job = job
                  break
          
          if existing_job:
              print(f"Updating job {existing_job.job_id}")
              w.jobs.update(job_id=existing_job.job_id, new_settings=job_settings)
          else:
              print("Creating new job")
              job = w.jobs.create(**job_settings.as_dict())
              print(f"Job created: {job.job_id}")
          EOF
```

**Note**: Requires `run_streamlit.py` notebook that wraps the Streamlit app.

---

## Part 3: Combined Workflow (DABS + Streamlit)

Complete workflow that deploys both infrastructure and application.

### .github/workflows/deploy-complete.yml

```yaml
name: Complete Deployment

on:
  push:
    branches: [ main ]
    paths:
      - 'sql_ddls/**'
      - '*.py'
      - 'app.yaml'
      - 'requirements.txt'
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
      
      - name: Upload application files
        env:
          DATABRICKS_WORKSPACE_PATH: ${{ secrets.DATABRICKS_WORKSPACE_PATH }}
        run: |
          databricks workspace import_dir . "$DATABRICKS_WORKSPACE_PATH/app" \
            --exclude-hidden-files \
            --exclude '*.md' \
            --exclude '__pycache__' \
            --exclude '.git'
      
      - name: Deploy notification
        run: |
          echo "Deployment complete!"
          echo "Access app at: ${{ secrets.DATABRICKS_HOST }}/apps"
```

---

## Part 4: Environment Configuration

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

## Part 5: Post-Deployment Steps

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

1. Access Streamlit app via configured deployment method
2. Run a test query
3. Verify governance logging
4. Check MLflow experiment tracking

---

## Part 6: Troubleshooting

### Common Issues

**Issue**: DABS deployment fails
- **Solution**: Verify `databricks.yml` syntax and workspace permissions

**Issue**: Streamlit app not accessible
- **Solution**: Check deployment method configuration and network access

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

# Check job status
databricks jobs list

# View app logs (if deployed as job)
databricks jobs runs list --job-id <job-id>
```

---

## Deployment Comparison

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| DABS + Databricks Apps | Native Databricks integration, managed platform | Limited CLI support, manual UI configuration | Production Databricks environments |
| DABS + Workspace Files + Job | Full control, automated deployment, CI/CD friendly | Requires job management, scheduled execution | CI/CD pipelines, automated deployments |

---

## Recommendations

1. **Production**: Use DABS for infrastructure + Databricks Apps for Streamlit
2. **CI/CD**: Use GitHub Actions workflows for automated deployment (Option 2)
3. **Monitoring**: Setup Lakehouse Monitoring post-deployment

---

## Additional Resources

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Databricks CLI Documentation](https://docs.databricks.com/dev-tools/cli/index.html)
- [Databricks Apps Documentation](https://docs.databricks.com/apps/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
