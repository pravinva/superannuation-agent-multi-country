#!/usr/bin/env python3
"""
Lakehouse Utilities - Unity Catalog Operations

All Databricks Lakehouse / Unity Catalog operations in one place:
- SQL query execution via Databricks SQL
- Member profile operations
- Citation retrieval from Unity Catalog
- Governance table queries

Eliminates duplicate execute_query() functions!
"""

import pandas as pd
import time
from typing import Optional, List, Dict
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from shared.logging_config import get_logger

logger = get_logger(__name__)

# Single WorkspaceClient instance
_workspace_client = None

def get_workspace_client() -> WorkspaceClient:
    """Get or create WorkspaceClient singleton."""
    global _workspace_client
    if _workspace_client is None:
        _workspace_client = WorkspaceClient()
    return _workspace_client


# ============================================================================
# CORE SQL EXECUTION
# ============================================================================

def execute_sql_query(query: str, warehouse_id: Optional[str] = None) -> pd.DataFrame:
    """
    Execute SQL query and return DataFrame.
    
    Unified function replacing duplicates in data_utils.py and tools.py.
    
    Args:
        query: SQL query string
        warehouse_id: Optional warehouse ID (uses config default if not provided)
        
    Returns:
        pandas DataFrame with results
        
    Raises:
        ValueError: If warehouse_id is not configured
        Exception: For SQL execution errors
    """
    from config import SQL_WAREHOUSE_ID
    
    wh_id = warehouse_id or SQL_WAREHOUSE_ID
    
    # Validate warehouse ID
    if not wh_id or wh_id in ["YOUR_WAREHOUSE_ID_HERE", "<Your SQL Warehouse ID>", "None", "", "null"]:
        raise ValueError("SQL Warehouse ID not configured. Please set it in Configuration.")
    
    w = get_workspace_client()
    
    try:
        statement = w.statement_execution.execute_statement(
            warehouse_id=wh_id,
            statement=query,
            wait_timeout="30s"
        )
        
        # Wait for completion
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            time.sleep(0.5)
            statement = w.statement_execution.get_statement(statement.statement_id)
        
        # Process results
        if statement.status.state == StatementState.SUCCEEDED:
            if statement.result and statement.result.data_array:
                columns = [col.name for col in statement.manifest.schema.columns]
                df = pd.DataFrame(statement.result.data_array, columns=columns)
                return df
            else:
                return pd.DataFrame()
        else:
            raise Exception(f"Query failed with state: {statement.status.state}")
    
    except Exception as e:
        raise Exception(f"SQL execution error: {str(e)}")


def execute_sql_statement(query: str, warehouse_id: Optional[str] = None):
    """
    Execute SQL statement and return raw statement result.
    
    Use this for INSERT, UPDATE, DELETE or when you need the raw result.
    
    Args:
        query: SQL statement string
        warehouse_id: Optional warehouse ID
        
    Returns:
        Statement execution result or None if failed
    """
    from config import SQL_WAREHOUSE_ID
    
    wh_id = warehouse_id or SQL_WAREHOUSE_ID
    
    if not wh_id or wh_id in ["YOUR_WAREHOUSE_ID_HERE", "<Your SQL Warehouse ID>", "None", "", "null"]:
        raise ValueError("SQL Warehouse ID not configured")
    
    w = get_workspace_client()
    
    try:
        statement = w.statement_execution.execute_statement(
            warehouse_id=wh_id,
            statement=query,
            wait_timeout="30s"
        )
        
        # Wait for completion
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            time.sleep(0.5)
            statement = w.statement_execution.get_statement(statement.statement_id)
        
        if statement.status.state == StatementState.SUCCEEDED:
            return statement
        else:
            logger.error(f"Statement failed: {statement.status.state}")
            return None

    except Exception as e:
        logger.error(f"Error executing statement: {e}")
        return None


# ============================================================================
# MEMBER PROFILE OPERATIONS
# ============================================================================

def get_member_by_id(member_id: str) -> Optional[Dict]:
    """
    Get a specific member by ID.
    
    Args:
        member_id: Member identifier
        
    Returns:
        Member profile dict or None if not found
    """
    from config import get_member_profiles_table_path
    
    try:
        table_path = get_member_profiles_table_path()
        query = f"SELECT * FROM {table_path} WHERE member_id = '{member_id}'"
        
        df = execute_sql_query(query)

        if df.empty:
            logger.warning(f"⚠️ Member not found: {member_id}")
            return None

        return df.iloc[0].to_dict()

    except Exception as e:
        logger.error(f"❌ Error loading member {member_id}: {str(e)}")
        return None


def get_members_by_country(country_code: str, default_return: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Get all members for a specific country.
    
    Args:
        country_code: Country code (AU, US, UK, IN)
        default_return: Default value to return on error
        
    Returns:
        DataFrame with member profiles
    """
    if default_return is None:
        default_return = pd.DataFrame()
    
    from config import get_member_profiles_table_path
    
    try:
        table_path = get_member_profiles_table_path()
        query = f"SELECT * FROM {table_path} WHERE country = '{country_code}'"
        
        df = execute_sql_query(query)

        if df.empty:
            logger.warning(f"⚠️ No members found for country: {country_code}")
            return default_return

        logger.info(f"✅ Found {len(df)} members for {country_code}")
        return df

    except Exception as e:
        logger.error(f"❌ Error loading members for {country_code}: {str(e)}")
        return default_return


# ============================================================================
# CITATION OPERATIONS
# ============================================================================

def get_citations(citation_ids: List[str], warehouse_id: Optional[str] = None) -> List[Dict]:
    """
    Fetch citations from registry.
    
    Args:
        citation_ids: List of citation IDs to fetch
        warehouse_id: Optional warehouse ID
        
    Returns:
        List of citation dictionaries
    """
    if not citation_ids:
        return []
    
    from config import SQL_WAREHOUSE_ID
    wh_id = warehouse_id or SQL_WAREHOUSE_ID
    
    ids_str = "', '".join(citation_ids)
    query = f"""
    SELECT 
        citation_id, authority, regulation_name, regulation_code,
        source_url, description
    FROM super_advisory_demo.member_data.citation_registry
    WHERE citation_id IN ('{ids_str}')
    ORDER BY citation_id
    """
    
    try:
        result = execute_sql_statement(query, wh_id)
        if not result or not result.result or not result.result.data_array:
            return []
        
        citations = []
        for row in result.result.data_array:
            citations.append({
                'citation_id': row[0],
                'authority': row[1],
                'regulation': f"{row[2]} ({row[3]})",
                'source_url': row[4],
                'description': row[5]
            })
        return citations
    except Exception as e:
        logger.error(f"⚠️ Error fetching citations: {e}")
        return []


# ============================================================================
# AUDIT & GOVERNANCE QUERIES
# ============================================================================

def get_audit_logs(limit: int = 50) -> List[Dict]:
    """
    Fetch recent governance table entries.
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        List of audit log dictionaries with classification_method extracted
    """
    from config import SQL_WAREHOUSE_ID
    
    try:
        sql = f"""
        SELECT *
        FROM super_advisory_demo.member_data.governance
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        statement = execute_sql_statement(sql, SQL_WAREHOUSE_ID)
        
        if not statement or not statement.result:
            return []
        
        result = statement.result.data_array
        keys = [c.name for c in statement.manifest.schema.columns]
        formatted = []
        
        for r in result:
            row_dict = dict(zip(keys, r))
            
            # ✅ Extract classification_method from error_info if present
            # Format: "classification_method=regex|..." or "classification_method=embedding"
            error_info = row_dict.get('error_info', '') or ''
            classification_method = None
            
            if error_info and 'classification_method=' in error_info:
                # Extract classification_method from error_info
                parts = error_info.split('|')
                for part in parts:
                    if part.startswith('classification_method='):
                        classification_method = part.replace('classification_method=', '')
                        # Remove from error_info if it's the only thing
                        if len(parts) == 1:
                            row_dict['error_info'] = ''
                        else:
                            row_dict['error_info'] = '|'.join([p for p in parts if not p.startswith('classification_method=')])
                        break
            
            # ✅ Extract judge_confidence from judge_response JSON if present
            # Format: JSON string {"reasoning": "...", "confidence": 0.95}
            judge_response = row_dict.get('judge_response', '') or ''
            judge_confidence = None
            
            if judge_response:
                try:
                    import json as json_lib
                    # Try to parse as JSON
                    if judge_response.strip().startswith('{'):
                        judge_data = json_lib.loads(judge_response)
                        if isinstance(judge_data, dict):
                            judge_confidence = judge_data.get('confidence')
                            # Keep original judge_response for backward compatibility
                    else:
                        # Not JSON, might be plain text reasoning (old format)
                        # Try to extract from reasoning if it contains confidence info
                        pass
                except:
                    # Not valid JSON, keep as is
                    pass
            
            # Add extracted fields as separate columns
            row_dict['classification_method'] = classification_method
            row_dict['judge_confidence'] = judge_confidence
            
            formatted.append(row_dict)

        return formatted
    except Exception as e:
        logger.error(f"⚠️ get_audit_logs() could not fetch governance logs: {e}")
        return []


def get_cost_summary(limit: int = 100) -> List[Dict]:
    """
    Get aggregated cost summary per country or user.
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        List of cost summary dictionaries
    """
    from config import SQL_WAREHOUSE_ID
    
    try:
        sql = f"""
        SELECT
            country,
            user_id,
            ROUND(SUM(cost), 4) AS total_cost,
            COUNT(*) AS query_count,
            ROUND(AVG(cost), 6) AS avg_cost
        FROM super_advisory_demo.member_data.governance
        GROUP BY country, user_id
        ORDER BY total_cost DESC
        LIMIT {limit}
        """
        statement = execute_sql_statement(sql, SQL_WAREHOUSE_ID)
        
        if not statement or not statement.result:
            return []
        
        result = statement.result.data_array
        keys = [c.name for c in statement.manifest.schema.columns]
        formatted = [dict(zip(keys, r)) for r in result]
        return formatted
    except Exception as e:
        logger.error(f"⚠️ get_cost_summary() could not compute cost summary: {e}")
        return []

