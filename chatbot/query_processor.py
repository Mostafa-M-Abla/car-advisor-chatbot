import re
import yaml
import logging
from typing import Dict, Any, List, Optional, Tuple
from openai import OpenAI
import os

class QueryProcessor:
    """Processes natural language queries and converts them to SQL."""

    def __init__(self, schema_path: str = "schema.yaml", synonyms_path: str = "synonyms.yaml", config_path: str = "chatbot_config.yaml"):
        self.schema_path = schema_path
        self.synonyms_path = synonyms_path
        self.config_path = config_path
        self.schema = self._load_schema()
        self.synonyms = self._load_synonyms()
        self.config = self._load_config()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.logger = logging.getLogger(__name__)

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

    def extract_criteria(self, user_input: str) -> Dict[str, Any]:
        """
        Extract search criteria from user input using pattern matching and GPT-4.

        Args:
            user_input: User's natural language input

        Returns:
            Dictionary with extracted criteria
        """
        criteria = {}
        user_lower = user_input.lower()

        # Extract price information
        criteria.update(self._extract_price(user_lower))

        # Extract body type
        body_type = self._extract_body_type(user_lower)
        if body_type:
            criteria['body_type'] = body_type

        # Extract transmission type
        transmission = self._extract_transmission(user_lower)
        if transmission:
            criteria['transmission'] = transmission

        # Extract origin preferences
        origin_info = self._extract_origin_preferences(user_lower)
        criteria.update(origin_info)

        # Extract features
        features = self._extract_features(user_lower)
        criteria.update(features)

        # Extract limit (number of results requested)
        limit = self._extract_limit(user_lower)
        if limit:
            criteria['limit'] = limit

        # Extract brand preferences
        brand = self._extract_brand(user_lower)
        if brand:
            criteria['brand'] = brand

        return criteria

    def _extract_price(self, text: str) -> Dict[str, Any]:
        """Extract price criteria from text."""
        criteria = {}

        # Pattern for "under X", "below X", "max X", "up to X"
        under_patterns = [
            r'under\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|m|egp)?',
            r'below\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|m|egp)?',
            r'max\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|m|egp)?',
            r'up to\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|m|egp)?',
        ]

        for pattern in under_patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '')
                price = float(price_str)

                # Handle millions
                if 'million' in match.group(0) or 'm' in match.group(0):
                    price *= 1_000_000
                elif price < 100:  # Assume millions if number is small
                    price *= 1_000_000

                criteria['max_price'] = int(price)
                break

        # Pattern for "over X", "above X", "minimum X"
        over_patterns = [
            r'over\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|m|egp)?',
            r'above\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|m|egp)?',
            r'minimum\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|m|egp)?',
        ]

        for pattern in over_patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '')
                price = float(price_str)

                if 'million' in match.group(0) or 'm' in match.group(0):
                    price *= 1_000_000
                elif price < 100:
                    price *= 1_000_000

                criteria['min_price'] = int(price)
                break

        # Pattern for "X to Y" or "between X and Y"
        range_patterns = [
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|m)?\s*to\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|m|egp)?',
            r'between\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|m)?\s*and\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|m|egp)?'
        ]

        for pattern in range_patterns:
            match = re.search(pattern, text)
            if match:
                min_price = float(match.group(1).replace(',', ''))
                max_price = float(match.group(2).replace(',', ''))

                # Handle millions
                if 'million' in match.group(0) or 'm' in match.group(0):
                    min_price *= 1_000_000
                    max_price *= 1_000_000
                elif min_price < 100 and max_price < 100:
                    min_price *= 1_000_000
                    max_price *= 1_000_000

                criteria['min_price'] = int(min_price)
                criteria['max_price'] = int(max_price)
                break

        return criteria

    def _extract_body_type(self, text: str) -> Optional[str]:
        """Extract body type from text."""
        body_types = {
            'sedan': ['sedan', 'saloon'],
            'hatchback': ['hatchback', 'hatch'],
            'crossover/suv': ['crossover', 'suv', 'cross over', 'sport utility'],
            'coupe': ['coupe', 'coup'],
            'convertible': ['convertible', 'cabriolet'],
            'van': ['van', 'minivan']
        }

        for standard_type, variants in body_types.items():
            for variant in variants:
                if variant in text:
                    return standard_type

        return None

    def _extract_transmission(self, text: str) -> Optional[str]:
        """Extract transmission type from text."""
        # Check synonyms first
        if self.synonyms and 'value_aliases' in self.synonyms and 'Transmission' in self.synonyms['value_aliases']:
            aliases = self.synonyms['value_aliases']['Transmission']
            for standard, variants in aliases.items():
                for variant in variants:
                    if variant in text:
                        return standard

        # Fallback patterns
        if 'automatic' in text or 'auto' in text or 'at' in text:
            return 'automatic'
        if 'manual' in text or 'man' in text:
            return 'manual'
        if 'dsg' in text or 'dual clutch' in text:
            return 'dsg'
        if 'cvt' in text:
            return 'cvt'

        return None

    def _extract_origin_preferences(self, text: str) -> Dict[str, Any]:
        """Extract origin country preferences."""
        criteria = {}

        # Check for exclusions first
        if 'non-chinese' in text or 'non chinese' in text or 'not chinese' in text:
            criteria['exclude_origin'] = 'china'

        # Check for specific countries using synonyms
        if self.synonyms and 'predicates' in self.synonyms:
            predicates = self.synonyms['predicates']
            for predicate_name, predicate_info in predicates.items():
                if predicate_name in text:
                    if predicate_info['op'] == '=':
                        criteria['origin_country'] = predicate_info['value']
                    elif predicate_info['op'] == '!=':
                        criteria['exclude_origin'] = predicate_info['value']

        return criteria

    def _extract_features(self, text: str) -> Dict[str, Any]:
        """Extract feature requirements."""
        features = {}

        # Use synonyms for feature mapping
        if self.synonyms and 'columns' in self.synonyms:
            for column, synonyms_list in self.synonyms['columns'].items():
                for synonym in synonyms_list:
                    if synonym in text:
                        features[column.lower()] = True

        # Direct feature matching
        feature_keywords = {
            'abs': 'abs',
            'esp': 'esp',
            'airbag': 'driver_airbag',
            'air conditioning': 'air_conditioning',
            'ac': 'air_conditioning',
            'sunroof': 'sunroof',
            'bluetooth': 'bluetooth',
            'gps': 'gps',
            'cruise control': 'cruise_control',
            'turbo': 'engine_turbo',
            # Note: electric_vehicle column removed from schema
        }

        for keyword, column in feature_keywords.items():
            if keyword in text:
                if column == 'electric_vehicle':
                    features[column] = True
                else:
                    features[column.lower()] = True

        return features

    def _extract_limit(self, text: str) -> Optional[int]:
        """Extract number of results requested."""
        # Pattern for "X cars", "top X", "first X"
        patterns = [
            r'(\d+)\s+cars?',
            r'top\s+(\d+)',
            r'first\s+(\d+)',
            r'show\s+(\d+)',
            r'suggest\s+(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        return None

    def _extract_brand(self, text: str) -> Optional[str]:
        """Extract specific brand mentions."""
        # Common brand names
        brands = [
            'toyota', 'honda', 'nissan', 'hyundai', 'kia', 'bmw', 'mercedes',
            'audi', 'volkswagen', 'vw', 'ford', 'chevrolet', 'peugeot',
            'renault', 'fiat', 'skoda', 'mitsubishi', 'mazda', 'suzuki',
            'chery', 'geely', 'mg', 'byd', 'xpeng', 'porsche'
        ]

        for brand in brands:
            if brand in text:
                return brand

        return None

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

Examples:
- "crossovers under 2M EGP" → SELECT * FROM cars WHERE body_type = 'crossover/suv' AND Price_EGP < 2000000 ORDER BY Price_EGP ASC
- "non-Chinese automatic cars with ESP" → SELECT * FROM cars WHERE Origin_Country != 'china' AND Transmission_Type = 'automatic' AND ESP = 1 ORDER BY Price_EGP ASC"""

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

            self.logger.info(f"Generated SQL: {sql_query}")
            return sql_query

        except Exception as e:
            self.logger.error(f"Error generating SQL with GPT-4: {e}")
            return ""

    def parse_query(self, user_input: str, context: str = "") -> Tuple[Dict[str, Any], str]:
        """
        Parse user query and return both structured criteria and SQL query.

        Args:
            user_input: User's natural language input
            context: Previous conversation context

        Returns:
            Tuple of (criteria dict, sql query string)
        """
        # Extract criteria using pattern matching
        criteria = self.extract_criteria(user_input)

        # Generate SQL query using GPT-4
        sql_query = self.generate_sql_with_gpt4(user_input, context)

        self.logger.info(f"Parsed criteria: {criteria}")
        self.logger.info(f"Generated SQL: {sql_query}")

        return criteria, sql_query

    def validate_and_clean_sql(self, sql_query: str) -> str:
        """
        Validate and clean the generated SQL query.

        Args:
            sql_query: Raw SQL query

        Returns:
            Cleaned and validated SQL query
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

        return sql_query.strip()