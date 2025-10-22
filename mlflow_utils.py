# mlflow_utils.py
import mlflow
import streamlit as st

def log_mlflow_run(experiment_path, params, metrics, artifacts):
    """Log an MLflow run with params, metrics, and artifacts"""
    try:
        mlflow.set_experiment(experiment_path)
        with mlflow.start_run():
            for k, v in params.items():
                mlflow.log_param(k, str(v))
            for k, v in metrics.items():
                mlflow.log_metric(k, float(v))
            for name, value in artifacts.items():
                mlflow.log_text(str(value), f"{name}.txt")
    except Exception as e:
        print(f"MLflow logging error: {e}")

def show_mlflow_runs(exp_path):
    """Display MLflow runs in Streamlit"""
    try:
        mlflow.set_experiment(exp_path)
        runs = mlflow.search_runs()
        if runs.empty:
            st.warning("No MLflow runs found.")
            return
        
        # Show key columns
        display_cols = ['run_id', 'start_time', 'status']
        available_cols = [col for col in display_cols if col in runs.columns]
        st.dataframe(runs[available_cols].head(20), use_container_width=True)
    except Exception as e:
        st.error(f"Error loading MLflow runs: {e}")

