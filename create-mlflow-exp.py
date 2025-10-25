#!/usr/bin/env python3
"""
create_mlflow_experiment.py

Script to create MLflow experiment for retirement advisory app
Run this on your Mac to create the missing experiment in Databricks

Usage:
    python create_mlflow_experiment.py
"""

import mlflow
import sys

# Your experiment path from config.py
EXPERIMENT_PATH = "/Workspace/Users/pravin.varma@databricks.com/prodretirement-advisory"

def create_experiment():
    """Create the MLflow experiment if it doesn't exist"""
    
    print("=" * 70)
    print("MLflow Experiment Creator")
    print("=" * 70)
    print()
    
    try:
        # Set tracking URI to Databricks
        print("🔗 Setting MLflow tracking URI to 'databricks'...")
        mlflow.set_tracking_uri("databricks")
        print("✅ Connected to Databricks MLflow")
        print()
        
        # Check if experiment exists
        print(f"🔍 Checking if experiment exists: {EXPERIMENT_PATH}")
        experiment = mlflow.get_experiment_by_name(EXPERIMENT_PATH)
        
        if experiment is not None:
            print("✅ Experiment already exists!")
            print(f"   Experiment ID: {experiment.experiment_id}")
            print(f"   Name: {experiment.name}")
            print(f"   Artifact Location: {experiment.artifact_location}")
            print()
            print("✨ No action needed - you're all set!")
            return True
        
        # Create the experiment
        print("⚠️  Experiment not found. Creating now...")
        experiment_id = mlflow.create_experiment(EXPERIMENT_PATH)
        print("✅ Experiment created successfully!")
        print(f"   Experiment ID: {experiment_id}")
        print(f"   Path: {EXPERIMENT_PATH}")
        print()
        
        # Verify creation
        print("🔍 Verifying experiment creation...")
        experiment = mlflow.get_experiment(experiment_id)
        if experiment:
            print("✅ Verification successful!")
            print(f"   Status: {experiment.lifecycle_stage}")
            print()
            print("🎉 You can now use the enhanced audit tab in your app!")
            return True
        else:
            print("❌ Verification failed - experiment not found after creation")
            return False
            
    except PermissionError as e:
        print("❌ Permission Error!")
        print(f"   {str(e)}")
        print()
        print("💡 Solution:")
        print("   1. Ensure you have Databricks workspace access")
        print("   2. Check your Databricks CLI configuration")
        print("   3. Verify your authentication token is valid")
        return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print()
        print("💡 Troubleshooting:")
        print("   1. Ensure Databricks CLI is configured:")
        print("      databricks configure --token")
        print()
        print("   2. Test connection:")
        print("      databricks workspace ls /")
        print()
        print("   3. Check your credentials:")
        print("      cat ~/.databrickscfg")
        return False

def main():
    """Main execution"""
    success = create_experiment()
    
    print()
    print("=" * 70)
    
    if success:
        print("✅ COMPLETE - Experiment is ready!")
        print()
        print("Next steps:")
        print("   1. Restart your Streamlit app")
        print("   2. Navigate to Audit/Governance → Enhanced Audit")
        print("   3. Go to MLflow Traces tab")
        print("   4. You should now see experiment connection")
        sys.exit(0)
    else:
        print("❌ FAILED - Experiment could not be created")
        print()
        print("Alternative: Run this in a Databricks notebook:")
        print()
        print("   import mlflow")
        print("   mlflow.set_tracking_uri('databricks')")
        print(f"   mlflow.create_experiment('{EXPERIMENT_PATH}')")
        sys.exit(1)

if __name__ == "__main__":
    main()
