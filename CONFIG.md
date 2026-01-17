# Configuration Guide

This document explains how to configure the Superannuation Agent for your environment.

## Overview

The agent supports configuration through two methods:
1. **YAML configuration** (`config/config.yaml`)
2. **Environment variables** (`.env` file or system environment)

Environment variables **always take precedence** over YAML configuration.

## Quick Setup

### Option 1: Using Environment Variables (Recommended for Production)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your values:
   ```bash
   DATABRICKS_SQL_WAREHOUSE_ID=4b9b953939869799
   MLFLOW_EXPERIMENT_PATH=/Users/your-email@databricks.com/prodretirement-advisory
   MLFLOW_EVAL_PATH=/Users/your-email@databricks.com/retirement-eval
   ```

3. The `.env` file is automatically ignored by git and won't be committed.

### Option 2: Using YAML Configuration (For Local Development)

1. Copy the example config:
   ```bash
   cp config/config.yaml.example config/config.yaml
   ```

2. Edit `config/config.yaml` and update these values:
   ```yaml
   databricks:
     sql_warehouse_id: "4b9b953939869799"

   mlflow:
     prod_experiment_path: "/Users/your-email@databricks.com/prodretirement-advisory"
     offline_eval_path: "/Users/your-email@databricks.com/retirement-eval"
   ```

**⚠️ Warning:** If you edit `config/config.yaml` locally, be careful not to commit sensitive values to git!

## Environment Variable Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABRICKS_SQL_WAREHOUSE_ID` | SQL Warehouse ID from your Databricks workspace | `4b9b953939869799` |
| `MLFLOW_EXPERIMENT_PATH` | MLflow experiment path for production runs | `/Users/email@databricks.com/prodretirement-advisory` |
| `MLFLOW_EVAL_PATH` | MLflow experiment path for offline evaluation | `/Users/email@databricks.com/retirement-eval` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABRICKS_UNITY_CATALOG` | Unity Catalog name | `super_advisory_demo` |
| `DATABRICKS_UNITY_SCHEMA` | Unity Schema name | `member_data` |

## Configuration Values That CAN Be in Git

The following values are application-specific and safe to commit:

- **LLM endpoint names**: `databricks-claude-opus-4-1`, `databricks-claude-sonnet-4`, etc.
- **Unity Catalog/Schema names**: These are database names, not secrets
- **Brand configuration**: Logo, support email, etc.
- **Country settings**: Enabled countries and their codes
- **Agent behavior**: Timeouts, retry counts, temperature settings

## Configuration Values That Should NOT Be in Git

These are environment-specific or contain user information:

- ❌ **SQL Warehouse IDs**: Specific to your Databricks workspace
- ❌ **MLflow experiment paths**: Contain user email addresses
- ❌ **Databricks tokens**: If you need to set `DATABRICKS_TOKEN`

## How It Works

The configuration loader in `config/__init__.py`:

1. Loads `config/config.yaml` at import time
2. For sensitive values, checks if an environment variable is set
3. Uses environment variable if present, otherwise uses YAML value
4. Validates configuration on startup

Example:
```python
# In config/__init__.py
SQL_WAREHOUSE_ID = _get_env_or_config('DATABRICKS_SQL_WAREHOUSE_ID',
                                     _config['databricks']['sql_warehouse_id'])
```

## Databricks Apps Deployment

When deploying to Databricks Apps:

1. Set environment variables in the App configuration UI
2. Or use Databricks Secrets and reference them:
   ```bash
   DATABRICKS_SQL_WAREHOUSE_ID={{secrets/scope/sql-warehouse-id}}
   ```

## Validation

On startup, the agent validates configuration and warns about:
- Missing SQL Warehouse ID
- Placeholder values in MLflow paths
- Default support email (optional)

You'll see warnings like:
```
Configuration issues found:
- SQL_WAREHOUSE_ID not configured
- MLFLOW_PROD_EXPERIMENT_PATH contains placeholder
```

## Troubleshooting

### "Configuration file not found"
- Make sure `config/config.yaml` exists
- Copy from `config/config.yaml.example` if needed

### "SQL_WAREHOUSE_ID not configured"
- Set `DATABRICKS_SQL_WAREHOUSE_ID` environment variable, or
- Update `sql_warehouse_id` in `config/config.yaml`

### "Statement execution failed"
- Check that your SQL Warehouse ID is correct
- Verify your Databricks authentication (token or profile)
- Ensure the warehouse is running

## Best Practices

1. **For local development**: Use `.env` file (never commit it!)
2. **For team sharing**: Keep `config/config.yaml` with placeholder values
3. **For production**: Use environment variables or Databricks Secrets
4. **For CI/CD**: Use environment variables in your pipeline

## Security Notes

- `.env` files are automatically ignored by git (see `.gitignore`)
- `config/config.yaml` is tracked in git but has placeholder values
- Never commit actual SQL Warehouse IDs or user-specific paths
- Use Databricks Secrets for production deployments
