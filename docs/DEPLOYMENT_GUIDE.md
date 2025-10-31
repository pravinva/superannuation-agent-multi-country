# Deployment Guide

## Overview

This guide covers deployment options for the Multi-Country Pension Advisor system, including:
- Databricks Asset Bundles (DABS) for SQL/infrastructure
- GitHub Actions workflows for Streamlit app deployment
- Multiple deployment strategies for different environments

## Architecture Components

The system consists of:
1. **SQL Infrastructure**: Unity Catalog schemas, tables, and SQL functions
2. **Python Application**: Streamlit UI and agent logic
3. **MLflow**: Experiment tracking and prompt registry
4. **Monitoring**: Lakehouse Monitoring setup

## Deployment Strategy

### Option 1: DABS + Databricks Apps (Recommended)

Use DABS for infrastructure and Databricks Apps for Streamlit deployment.

### Option 2: DABS + Workspace Files

Use DABS for infrastructure and upload files to Databricks workspace.

### Option 3: DABS + Databricks Job

Use DABS for infrastructure and run Streamlit as a scheduled job.

### Option 4: Full Manual Deployment

Manual deployment for development/testing environments.

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

## Part 2: GitHub Actions - Streamlit Deployment

### Option A: Deploy to Databricks Apps

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

### Option B: Deploy to Workspace Files + Run as Job

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

### Option C: Deploy to External Streamlit Cloud

Deploy to Streamlit Community Cloud or custom server.

#### .github/workflows/deploy-streamlit-cloud.yml

```yaml
name: Deploy to Streamlit Cloud

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
      
      - name: Validate requirements.txt
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt --dry-run
      
      - name: Deploy to Streamlit Cloud
        env:
          STREAMLIT_CLOUD_TOKEN: ${{ secrets.STREAMLIT_CLOUD_TOKEN }}
        run: |
          # Streamlit Cloud automatically deploys from GitHub
          # This step validates the deployment
          echo "Streamlit Cloud will auto-deploy from this repository"
          echo "Ensure repository is connected in Streamlit Cloud dashboard"
```

**Setup**: Connect GitHub repository in Streamlit Cloud dashboard.

---

### Option D: Deploy to Remote Server via SSH

Deploy to a remote server running Streamlit.

#### .github/workflows/deploy-ssh.yml

```yaml
name: Deploy to Remote Server

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
      
      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.7.0
        with:
          ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}
      
      - name: Add server to known hosts
        run: |
          ssh-keyscan -H ${{ secrets.SERVER_HOST }} >> ~/.ssh/known_hosts
      
      - name: Deploy to server
        env:
          SERVER_HOST: ${{ secrets.SERVER_HOST }}
          SERVER_USER: ${{ secrets.SERVER_USER }}
          SERVER_PATH: ${{ secrets.SERVER_PATH }}
        run: |
          # Copy files to server
          rsync -avz --exclude '.git' --exclude '__pycache__' \
            --exclude '*.md' --exclude 'docs' \
            ./ $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
          
          # SSH into server and restart Streamlit
          ssh $SERVER_USER@$SERVER_HOST << 'EOF'
            cd $SERVER_PATH
            pip install -r requirements.txt
            pkill -f streamlit || true
            nohup streamlit run app.py --server.port 8501 > streamlit.log 2>&1 &
            echo "Streamlit app restarted"
          EOF
```

**Server Requirements**:
- Python 3.9+ installed
- Streamlit installed
- SSH access configured
- Firewall allows port 8501

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

1. **For Databricks**:
   - `DATABRICKS_HOST`: Your Databricks workspace URL (e.g., `https://your-workspace.cloud.databricks.com`)
   - `DATABRICKS_TOKEN`: Personal access token or service principal token
   - `DATABRICKS_WORKSPACE_PATH`: Workspace path for app (e.g., `/Workspace/Users/user@example.com/app`)

2. **For SSH Deployment** (if using Option D):
   - `SSH_PRIVATE_KEY`: SSH private key for server access
   - `SERVER_HOST`: Server hostname or IP
   - `SERVER_USER`: SSH username
   - `SERVER_PATH`: Deployment path on server

3. **For Streamlit Cloud** (if using Option C):
   - `STREAMLIT_CLOUD_TOKEN`: Streamlit Cloud API token (optional)

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
| DABS + Databricks Apps | Native Databricks integration | Limited CLI support | Production Databricks environments |
| DABS + Workspace Files | Full control, automated | Manual app configuration | CI/CD pipelines |
| DABS + Job | Scheduled execution | Not interactive | Batch processing |
| Streamlit Cloud | Easy setup, free tier | External dependency | Development/testing |
| SSH Deployment | Full control | Server management | Self-hosted environments |

---

## Recommendations

1. **Production**: Use DABS for infrastructure + Databricks Apps or Workspace Files for Streamlit
2. **Development**: Use manual deployment or Streamlit Cloud for quick iteration
3. **CI/CD**: Use GitHub Actions workflows for automated deployment
4. **Monitoring**: Setup Lakehouse Monitoring post-deployment

---

## Additional Resources

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Databricks CLI Documentation](https://docs.databricks.com/dev-tools/cli/index.html)
- [Streamlit Deployment Guide](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

