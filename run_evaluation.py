# run_evaluation.py
import pandas as pd
import argparse
import uuid
from agent_processor import agent_query
from config import MLFLOW_PROD_EXPERIMENT_PATH, MLFLOW_OFFLINE_EVAL_PATH

def offline_eval(csv_path):
    """Run evaluation on CSV dataset"""
    df = pd.read_csv(csv_path)
    results = []
    
    for idx, row in df.iterrows():
        # Generate unique session ID for each evaluation
        session_id = str(uuid.uuid4())
        
        # Map country display name to country code if needed
        country = row.get("country", "AU")
        country_code_map = {
            "Australia": "AU",
            "USA": "US",
            "United Kingdom": "UK",
            "India": "IN",
            "AU": "AU",
            "US": "US",
            "UK": "UK",
            "IN": "IN"
        }
        country_code = country_code_map.get(country, country)
        
        # Run agent query
        output = agent_query(
            user_id=row.get("user_id", "eval_user"),
            session_id=session_id,
            country=country_code,
            query_string=row.get("query_str", row.get("query_string", "")),
            validation_mode="llm_judge",
            enable_observability=True
        )
        
        results.append({
            "row_index": idx,
            "user_id": row.get("user_id"),
            "country": country_code,
            "query": row.get("query_str", row.get("query_string", "")),
            "session_id": session_id,
            "result": output
        })
    
    return results

def online_eval(query_str, user_id, country):
    """Run single online evaluation"""
    session_id = str(uuid.uuid4())
    
    # Map country display name to country code if needed
    country_code_map = {
        "Australia": "AU",
        "USA": "US",
        "United Kingdom": "UK",
        "India": "IN",
        "AU": "AU",
        "US": "US",
        "UK": "UK",
        "IN": "IN"
    }
    country_code = country_code_map.get(country, country)
    
    return agent_query(
        user_id=user_id,
        session_id=session_id,
        country=country_code,
        query_string=query_str,
        validation_mode="llm_judge",
        enable_observability=True
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

