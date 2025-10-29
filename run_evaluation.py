# run_evaluation.py
import pandas as pd
import argparse
from agent import run_agent_interaction
from config import MLFLOW_PROD_EXPERIMENT_PATH, MLFLOW_OFFLINE_EVAL_PATH

def offline_eval(csv_path):
    """Run evaluation on CSV dataset"""
    df = pd.read_csv(csv_path)
    results = []
    for idx, row in df.iterrows():
        output = run_agent_interaction(
            user_id=row["user_id"],
            country=row["country"],
            query_str=row["query_str"],
            extra_context=row.to_dict(),
            mlflow_experiment_path=MLFLOW_OFFLINE_EVAL_PATH
        )
        results.append(output)
    return results

def online_eval(query_str, user_id, country):
    """Run single online evaluation"""
    return run_agent_interaction(
        user_id=user_id,
        country=country,
        query_str=query_str,
        mlflow_experiment_path=MLFLOW_PROD_EXPERIMENT_PATH
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["offline", "online"], required=True)
    parser.add_argument("--csv_path", type=str)
    parser.add_argument("--query_str", type=str)
    parser.add_argument("--user_id", type=str)
    parser.add_argument("--country", type=str)
    args = parser.parse_args()
    
    if args.mode == "offline":
        results = offline_eval(args.csv_path)
        print(f"Processed {len(results)} evaluations")
    else:
        result = online_eval(args.query_str, args.user_id, args.country)
        print(result)

def run_csv_evaluation(uploaded_csv):
    """
    Wrapper for offline_eval() to be Streamlit-compatible.
    Accepts UploadedFile from Streamlit's file_uploader widget.
    """
    import tempfile
    import json

    try:
        # Save Streamlit file buffer to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded_csv.read())
            tmp_path = tmp.name

        # Run offline evaluation
        results = offline_eval(tmp_path)

        # Summarize results nicely for Streamlit JSON viewer
        summary = {"total_queries": len(results)}
        summary["sample_result"] = results[0] if results else {}

        return summary

    except Exception as e:
        return {"error": str(e)}

