from typing import Dict, Any, List, Optional
import logging
import os
import yaml
from openai import OpenAI

class KnowledgeHandler:
    """Handles automotive knowledge queries using LLM capabilities for information not available in the database."""

    def __init__(self, timeout: int = 10, config_path: str = "chatbot_config.yaml"):
        self.timeout = timeout
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
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

    def get_knowledge_response(self, query: str, conversation_context: str = "", database_context: List[Dict[str, Any]] = None) -> str:
        """
        Universal handler for all external knowledge queries using a single, flexible prompt.

        Args:
            query: User's question about cars
            conversation_context: Previous conversation context for continuity
            database_context: Optional list of car data from database for additional context

        Returns:
            Response with automotive knowledge
        """
        try:
            # Build context from database information if provided
            context_info = ""
            if database_context:
                if len(database_context) == 1:
                    # Single car context
                    car = database_context[0]
                    brand = car.get('car_brand', '')
                    model = car.get('car_model', '')
                    year = car.get('Year', '')
                    price = car.get('Price_EGP', 0)
                    context_info = f"\nContext: The user is asking about a {year} {brand} {model} (priced at {price:,} EGP in our database)."
                elif len(database_context) == 2:
                    # Comparison context
                    car1 = database_context[0]
                    car2 = database_context[1]
                    context_info = f"\nContext: Comparing two cars from our database:\n"
                    for i, car in enumerate([car1, car2], 1):
                        context_info += f"Car {i}: {car.get('Year', '')} {car.get('car_brand', '')} {car.get('car_model', '')} - "
                        context_info += f"{car.get('Price_EGP', 0):,} EGP, {car.get('Engine_CC', '')}cc, "
                        context_info += f"{car.get('Horsepower_HP', '')} HP, {car.get('Transmission_Type', '')}\n"

            # Add conversation context if provided
            conversation_info = ""
            if conversation_context:
                conversation_info = f"\nPrevious conversation context:\n{conversation_context}\n"

            # Create a comprehensive, flexible system prompt
            system_prompt = """You are an expert automotive consultant for the Egyptian car market with comprehensive knowledge about:
- Car reliability, common issues, and long-term ownership experience
- Market reputation, reviews, and brand perceptions
- Historical information about car models and manufacturers
- Technical specifications, performance characteristics, and driving dynamics
- Maintenance costs, service availability, and parts pricing
- Safety ratings, crash tests, and safety features
- Car comparisons and alternatives in various segments
- Egyptian market trends, preferences, and buying patterns
- Value for money and resale value considerations
- Fuel efficiency and running costs

Provide accurate, helpful, and conversational responses that directly answer the user's question.
Adapt your response style and depth to match the specific question asked.
Consider the Egyptian market context, including local preferences, service networks, and driving conditions.
Be honest about uncertainties and focus on practical information that helps with car buying decisions.
Keep responses concise but informative - avoid unnecessary structure unless the question requires it."""

            # Build the user prompt
            user_prompt = f"{conversation_info}{context_info}\n\nUser question: {query}"

            response = self.openai_client.chat.completions.create(
                model=self.config.get('openai', {}).get('model', 'gpt-4.1'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )

            result = response.choices[0].message.content.strip()

            # Add disclaimer only if no database context was provided
            if not database_context:
                disclaimer = "\n\n*Note: This information is based on general automotive knowledge.*"
                return result + disclaimer

            return result

        except Exception as e:
            self.logger.error(f"Error in knowledge query: {e}")
            return "I'm sorry, I'm currently unable to access additional automotive information at the moment. Please try again or ask about specific cars in our database."

    def is_external_knowledge_query(self, query: str) -> bool:
        """
        Determine if a query requires external knowledge beyond database specs.

        Args:
            query: User's query

        Returns:
            Boolean indicating if external knowledge is needed
        """
        # Keywords that indicate need for external automotive knowledge
        external_keywords = [
            'reliable', 'reliability', 'problems', 'issues', 'quality', 'durability',
            'review', 'rating', 'opinion', 'experience', 'reputation',
            'fast', 'slow', 'handling', 'ride quality', 'comfortable',
            'maintenance', 'service', 'repair', 'parts', 'cost to own',
            'better', 'worse', 'compare', 'comparison', 'vs', 'versus', 'difference',
            'trend', 'popular', 'demand', 'price trend', 'market',
            'history', 'first introduced', 'when launched', 'background', 'story',
            'safe', 'safety', 'crash test', 'stability', 'ratings'
        ]

        query_lower = query.lower()

        # Check for external knowledge keywords
        if any(keyword in query_lower for keyword in external_keywords):
            return True

        # Check for general automotive questions
        general_indicators = ['how', 'why', 'when', 'should i', 'is it', 'does it', 'can it']
        if any(indicator in query_lower for indicator in general_indicators):
            return True

        return False