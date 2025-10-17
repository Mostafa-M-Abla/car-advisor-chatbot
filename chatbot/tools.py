"""
LangChain tools for the car chatbot.

This module defines the tools that the LangChain agent can use to interact
with the car database.
"""

from langchain.tools import tool
from typing import Dict, Any, List
import logging

# Module-level logger
logger = logging.getLogger(__name__)


@tool
def execute_sql_query(sql_query: str) -> Dict[str, Any]:
    """
    Execute a SQL query against the car database to search for vehicles.

    This tool allows searching through 900+ car trims in the Egyptian market
    with comprehensive specs, prices in EGP, and features.

    Args:
        sql_query: A valid SELECT SQL query to execute against the 'cars' table.
                  Must be a safe, read-only SELECT statement.

    Returns:
        Dictionary with success status and results:
        - success (bool): Whether the query executed successfully
        - results_count (int): Number of results returned
        - results (List[Dict]): List of car records (max 20)
        - error (str): Error message if query failed

    Examples:
        - "SELECT * FROM cars WHERE body_type = 'sedan' AND Price_EGP < 1000000 LIMIT 10"
        - "SELECT car_brand, car_model, Price_EGP FROM cars WHERE Origin_Country = 'japan' ORDER BY Price_EGP ASC LIMIT 5"
    """
    # Note: The actual database handler will be injected at runtime
    # This is a placeholder that will be wrapped with the actual handler
    return {
        "success": False,
        "error": "Database handler not initialized. This tool must be bound to a database handler."
    }


def create_sql_tool_with_db(db_handler) -> callable:
    """
    Create a SQL execution tool bound to a specific database handler.

    Args:
        db_handler: DatabaseHandler instance to use for query execution

    Returns:
        A LangChain tool function bound to the database handler
    """
    @tool
    def execute_sql_query_bound(sql_query: str) -> Dict[str, Any]:
        """
        Execute a SQL query against the car database to search for vehicles.

        This tool allows searching through 900+ car trims in the Egyptian market
        with comprehensive specs, prices in EGP, and features.

        Args:
            sql_query: A valid SELECT SQL query to execute against the 'cars' table.
                      Must be a safe, read-only SELECT statement.

        Returns:
            Dictionary with success status and results:
            - success (bool): Whether the query executed successfully
            - results_count (int): Number of results returned
            - results (List[Dict]): List of car records (max 20)
            - error (str): Error message if query failed
        """
        try:
            # Validate SQL
            if not db_handler.validate_query(sql_query):
                logger.warning(f"SQL validation failed: {sql_query}")
                return {
                    "success": False,
                    "error": "SQL query failed validation (must be SELECT from cars table only)"
                }

            # Execute query
            results = db_handler.execute_query(sql_query)
            logger.info(f"SQL query returned {len(results)} results")

            return {
                "success": True,
                "results_count": len(results),
                "results": results[:20]  # Limit to 20 results to avoid token overflow
            }

        except Exception as e:
            logger.error(f"Error executing SQL tool: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    return execute_sql_query_bound
