import yaml
import logging
from typing import Dict, Any
from openai import OpenAI
import os

class QueryProcessor:
    """
    Processes natural language queries and converts them to SQL using AI only.

    SIMPLIFIED ARCHITECTURE:
    This class has ONE responsibility: AI-powered SQL generation using GPT-4.1.

    Previous complexity removed:
    - No regex pattern matching (~300 lines removed)
    - No structured criteria extraction
    - No fallback logic

    Benefits:
    - Single, clear execution path
    - Leverages GPT-4.1's high reliability
    - Much simpler and more maintainable
    - When AI fails, user is asked to rephrase (honest and often more helpful)
    """

    def __init__(self, schema_path: str = "schema.yaml", synonyms_path: str = "synonyms.yaml", config_path: str = "chatbot_config.yaml"):
        """
        Initialize the QueryProcessor with schema, synonyms, and configuration.

        Args:
            schema_path: Path to database schema YAML file
            synonyms_path: Path to synonyms YAML file (maps user terms to DB columns)
            config_path: Path to chatbot configuration YAML file
        """
        self.schema_path = schema_path
        self.synonyms_path = synonyms_path
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.schema = self._load_schema()
        self.synonyms = self._load_synonyms()
        self.config = self._load_config()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def _load_config(self) -> Dict[str, Any]:
        """Load chatbot configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}

    def _load_schema(self) -> Dict[str, Any]:
        """Load database schema from YAML file."""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Failed to load schema: {e}")
            return {}

    def _load_synonyms(self) -> Dict[str, Any]:
        """Load synonyms from YAML file."""
        try:
            with open(self.synonyms_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Failed to load synonyms: {e}")
            return {}

    def generate_sql_with_gpt4(self, user_input: str, context: str = "") -> str:
        """
        Use GPT-4 to generate SQL query from natural language.

        Args:
            user_input: User's natural language query
            context: Previous conversation context

        Returns:
            Generated SQL query
        """
        try:
            schema_str = yaml.dump(self.schema, default_flow_style=False)
            synonyms_str = yaml.dump(self.synonyms, default_flow_style=False)

            prompt = f"""Based on the user's request, generate a SQL query for the cars database.

Database schema:
{schema_str}

Available synonyms:
{synonyms_str}

User request: {user_input}
Conversation context: {context}

Instructions:
- Generate ONLY the SQL query, no explanations
- Use proper column names from the schema
- Handle synonyms appropriately (e.g., "auto" -> "automatic")
- Apply appropriate filters for price, origin, features, etc.
- For price ranges, use appropriate comparison operators
- For "non-Chinese", use Origin_Country != 'china'
- For body types, use exact values: sedan, hatchback, crossover/suv, coupe, convertible, van
- For boolean features (ABS, ESP, etc.), use = 1 for presence
- Order by Price_EGP ASC for budget-conscious results
- ALWAYS include LIMIT clause (default LIMIt 20, user can ask for LIMIT less than 20, but never more than 20)

Examples:
- "crossovers under 2M EGP" → SELECT * FROM cars WHERE body_type = 'crossover/suv' AND Price_EGP < 2000000 ORDER BY Price_EGP ASC LIMIT 20
- "non-Chinese automatic cars with ESP" → SELECT * FROM cars WHERE Origin_Country != 'china' AND Transmission_Type = 'automatic' AND ESP = 1 ORDER BY Price_EGP ASC LIMIT 20
- "show me 5 sedans" → SELECT * FROM cars WHERE body_type = 'sedan' ORDER BY Price_EGP ASC LIMIT 5"""

            response = self.openai_client.chat.completions.create(
                model=self.config.get('openai', {}).get('model', 'gpt-4.1'),
                messages=[
                    {"role": "system", "content": "You are an expert SQL generator for automotive databases. Generate only valid SQL queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            sql_query = response.choices[0].message.content.strip()

            # Clean up the query (remove markdown formatting if present)
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]

            sql_query = sql_query.strip()

            # Validate and clean the SQL query for security
            sql_query = self.validate_and_clean_sql(sql_query)

            self.logger.info(f"Generated SQL: {sql_query}")
            return sql_query

        except Exception as e:
            self.logger.error(f"Error generating SQL with GPT-4: {e}")
            return ""

    def parse_query(self, user_input: str, context: str = "") -> str:
        """
        Parse user query and generate SQL query using GPT-4.1 (SIMPLIFIED - SINGLE PATH).

        This method now uses ONLY AI to generate SQL queries, removing the
        redundant regex pattern matching fallback. The system is more reliable
        by having a single, clear path rather than complex fallback logic.

        When SQL generation fails:
        - Returns empty string
        - car_chatbot.py will show error message and ask user to rephrase
        - Much simpler than trying to parse with inferior regex patterns

        Args:
            user_input: User's natural language input (e.g., "show me sedans under 1M EGP")
            context: Previous conversation context for maintaining continuity

        Returns:
            SQL query string, or empty string if generation fails
        """
        # Generate SQL query using GPT-4.1 (single path - no fallback)
        sql_query = self.generate_sql_with_gpt4(user_input, context)

        self.logger.info(f"Generated SQL: {sql_query}")

        return sql_query

    def validate_and_clean_sql(self, sql_query: str) -> str:
        """
        Validate and clean the generated SQL query.
        Adds LIMIT 20 if no LIMIT clause exists to reduce costs and improve performance.

        Args:
            sql_query: Raw SQL query

        Returns:
            Cleaned and validated SQL query with LIMIT clause
        """
        if not sql_query:
            return ""

        sql_lower = sql_query.lower().strip()

        # Must be a SELECT query
        if not sql_lower.startswith('select'):
            return ""

        # Remove potentially harmful statements
        forbidden_keywords = ['insert', 'update', 'delete', 'drop', 'create', 'alter']
        for keyword in forbidden_keywords:
            if keyword in sql_lower:
                return ""

        # Ensure proper table name
        if 'from cars' not in sql_lower:
            return ""

        # Add LIMIT 20 if no LIMIT clause exists (to reduce costs and improve performance)
        if 'limit' not in sql_lower:
            sql_query = sql_query.strip()
            if sql_query.endswith(';'):
                sql_query = sql_query[:-1].strip()
            sql_query += ' LIMIT 20'

        return sql_query.strip()