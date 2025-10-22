# data_utils.py
"""Utilities for retrieving member data from Unity Catalog"""

from pyspark.sql import SparkSession
import pandas as pd
from config import get_member_profiles_table_path

def get_spark():
    """Get or create Spark session"""
    return SparkSession.builder.getOrCreate()

def get_members_by_country(country):
    """
    Retrieve member profiles for a specific country.
    No warehouse configuration needed - uses Databricks App's Spark session.
    """
    try:
        spark = get_spark()
        table_path = get_member_profiles_table_path()
        query = f"SELECT * FROM {table_path} WHERE country = '{country}'"
        df = spark.sql(query)
        return df.toPandas()
    except Exception as e:
        print(f"Error retrieving members: {e}")
        return pd.DataFrame()

def get_member_by_id(member_id):
    """Retrieve a specific member by ID"""
    try:
        spark = get_spark()
        table_path = get_member_profiles_table_path()
        query = f"SELECT * FROM {table_path} WHERE member_id = '{member_id}'"
        df = spark.sql(query)
        result = df.toPandas()
        return result.to_dict('records')[0] if not result.empty else None
    except Exception as e:
        print(f"Error retrieving member: {e}")
        return None

def get_all_members():
    """Retrieve all member profiles"""
    try:
        spark = get_spark()
        table_path = get_member_profiles_table_path()
        df = spark.table(table_path)
        return df.toPandas()
    except Exception as e:
        print(f"Error retrieving all members: {e}")
        return pd.DataFrame()

