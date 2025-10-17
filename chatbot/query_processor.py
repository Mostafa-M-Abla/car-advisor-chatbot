import yaml
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
import os

class QueryProcessor:
    """
    Provides schema, synonyms, and LangChain chat model for the agent.

    LANGCHAIN ARCHITECTURE (2025):
    This class now serves as a configuration holder for:
    - Database schema
    - Synonym mappings
    - LangChain ChatOpenAI model instance

    Previous responsibilities removed:
    - SQL generation (now in LangGraph agent with tools)
    - Direct OpenAI API calls (now using LangChain)
    - Regex pattern matching (~300 lines removed earlier)
    - Complex query parsing logic

    Benefits:
    - Single source of truth for schema/synonyms
    - LangChain integration for agent framework
    - Reusable across components
    - Much simpler and focused
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

        # Initialize LangChain ChatOpenAI model
        self.chat_model = ChatOpenAI(
            model=self.config.get('openai', {}).get('model', 'gpt-4.1'),
            temperature=self.config.get('openai', {}).get('temperature', 0.1),
            max_tokens=self.config.get('openai', {}).get('max_tokens', 1500),
            api_key=os.getenv('OPENAI_API_KEY')
        )

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

