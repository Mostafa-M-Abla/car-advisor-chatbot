import requests
from typing import Dict, Any, List, Optional
import logging
import os
from openai import OpenAI

class WebSearchHandler:
    """Handles web searches for information not available in the database."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.logger = logging.getLogger(__name__)

    def search_car_information(self, query: str, car_info: Dict[str, Any] = None) -> str:
        """
        Search for car information using GPT-4's knowledge base.

        This method uses GPT-4's training data to provide information about cars
        that may not be in our database, such as reliability, market reputation,
        historical information, etc.

        Args:
            query: User's question about a car
            car_info: Optional car information from database for context

        Returns:
            Response with car information
        """
        try:
            # Build context if car information is available
            context = ""
            if car_info:
                brand = car_info.get('car_brand', '')
                model = car_info.get('car_model', '')
                year = car_info.get('Year', '')
                context = f"The user is asking about a {year} {brand} {model}. "

            # Create a comprehensive prompt for automotive questions
            system_prompt = """You are an expert automotive consultant with comprehensive knowledge about:
            - Car reliability and common issues
            - Market reputation and reviews
            - Historical information about car models
            - Technical specifications and performance
            - Maintenance costs and ownership experience
            - Safety ratings and awards
            - Market comparisons and alternatives
            - Industry trends and technology

            Provide accurate, helpful information based on your automotive knowledge.
            Focus on practical information that would help someone make a car buying decision.
            If you're not certain about specific information, indicate that clearly."""

            user_prompt = f"{context}Question: {query}"

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=600
            )

            result = response.choices[0].message.content.strip()

            # Add disclaimer for information not in database
            disclaimer = "\n\n*Note: This information is based on general automotive knowledge and may not reflect the specific vehicle in our database.*"

            return result + disclaimer

        except Exception as e:
            self.logger.error(f"Error in web search: {e}")
            return "I'm sorry, I'm currently unable to access additional information about this car. I can only provide the specifications available in our database."

    def get_car_reviews_summary(self, brand: str, model: str, year: Optional[int] = None) -> str:
        """
        Get a summary of car reviews and reputation using GPT-4.

        Args:
            brand: Car brand
            model: Car model
            year: Optional model year

        Returns:
            Summary of reviews and reputation
        """
        try:
            year_context = f"{year} " if year else ""
            car_name = f"{year_context}{brand} {model}"

            prompt = f"""Provide a comprehensive review summary for the {car_name} including:

            1. **Overall Reputation**: Market perception and general reliability
            2. **Strengths**: What this car is known for (reliability, performance, features, value, etc.)
            3. **Common Issues**: Known problems or areas of concern
            4. **Target Audience**: Who this car is best suited for
            5. **Market Position**: How it compares to competitors
            6. **Ownership Experience**: Typical maintenance costs, fuel efficiency, resale value

            Please provide factual, balanced information based on automotive industry knowledge."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an automotive expert providing balanced, factual car reviews."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            self.logger.error(f"Error getting reviews summary: {e}")
            return f"I'm unable to provide a detailed review summary for the {brand} {model} at the moment."

    def get_reliability_information(self, brand: str, model: str) -> str:
        """
        Get reliability information for a specific car model.

        Args:
            brand: Car brand
            model: Car model

        Returns:
            Reliability information
        """
        try:
            prompt = f"""Provide reliability information for the {brand} {model}:

            1. **General Reliability Rating**: Overall reliability reputation
            2. **Common Problems**: Typical issues owners report
            3. **Maintenance Costs**: Expected maintenance expenses
            4. **Long-term Ownership**: How the car ages over time
            5. **Recommended Service Intervals**: Important maintenance milestones

            Focus on factual, practical information that would help a potential buyer."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an automotive reliability expert with extensive knowledge of car reliability patterns and issues."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            self.logger.error(f"Error getting reliability info: {e}")
            return f"I'm unable to provide specific reliability information for the {brand} {model} right now."

    def compare_cars(self, car1: Dict[str, Any], car2: Dict[str, Any]) -> str:
        """
        Compare two cars using both database information and general knowledge.

        Args:
            car1: First car information
            car2: Second car information

        Returns:
            Detailed comparison
        """
        try:
            # Extract relevant information from both cars
            def extract_car_summary(car):
                return {
                    'brand': car.get('car_brand', ''),
                    'model': car.get('car_model', ''),
                    'price': car.get('Price_EGP', 0),
                    'engine': car.get('Engine_CC', ''),
                    'horsepower': car.get('Horsepower_HP', ''),
                    'transmission': car.get('Transmission_Type', ''),
                    'body_type': car.get('body_type', ''),
                    'origin': car.get('Origin_Country', ''),
                    'electric': car.get('electric_vehicle', False)
                }

            car1_summary = extract_car_summary(car1)
            car2_summary = extract_car_summary(car2)

            prompt = f"""Compare these two cars and provide a detailed analysis:

            **Car 1: {car1_summary['brand']} {car1_summary['model']}**
            - Price: {car1_summary['price']:,} EGP
            - Engine: {car1_summary['engine']}cc
            - Power: {car1_summary['horsepower']} HP
            - Transmission: {car1_summary['transmission']}
            - Type: {car1_summary['body_type']}
            - Origin: {car1_summary['origin']}

            **Car 2: {car2_summary['brand']} {car2_summary['model']}**
            - Price: {car2_summary['price']:,} EGP
            - Engine: {car2_summary['engine']}cc
            - Power: {car2_summary['horsepower']} HP
            - Transmission: {car2_summary['transmission']}
            - Type: {car2_summary['body_type']}
            - Origin: {car2_summary['origin']}

            Please provide a comparison covering:
            1. **Value for Money**: Which offers better value
            2. **Performance**: Engine performance and driving experience
            3. **Reliability**: Expected reliability and maintenance
            4. **Features & Comfort**: Interior and technology features
            5. **Target Audience**: Who each car is best for
            6. **Recommendation**: Which to choose and why

            Be balanced and consider the Egyptian market context."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an automotive expert providing detailed car comparisons for the Egyptian market."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            self.logger.error(f"Error comparing cars: {e}")
            return "I'm unable to provide a detailed comparison at the moment. You can compare the specifications from our database."

    def get_market_insights(self, query: str) -> str:
        """
        Get market insights and trends for the Egyptian automotive market.

        Args:
            query: Market-related query

        Returns:
            Market insights response
        """
        try:
            prompt = f"""Provide insights about the Egyptian automotive market related to: {query}

            Consider factors like:
            - Popular car segments in Egypt
            - Price trends and affordability
            - Local preferences and buying patterns
            - Import vs local assembly considerations
            - Fuel efficiency importance
            - After-sales service and parts availability
            - Resale value considerations

            Provide practical, market-focused information."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an automotive market analyst with knowledge of the Egyptian automotive market trends and consumer preferences."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            self.logger.error(f"Error getting market insights: {e}")
            return "I'm unable to provide market insights at the moment. Please try again later."

    def search_by_category(self, category: str, user_query: str) -> str:
        """
        Search for information by category (reliability, reviews, specifications, etc.).

        Args:
            category: Type of information requested
            user_query: Original user query

        Returns:
            Category-specific response
        """
        category_handlers = {
            'reliability': lambda: self.search_car_information(f"reliability information: {user_query}"),
            'reviews': lambda: self.search_car_information(f"reviews and ratings: {user_query}"),
            'specifications': lambda: self.search_car_information(f"technical specifications: {user_query}"),
            'performance': lambda: self.search_car_information(f"performance and driving experience: {user_query}"),
            'maintenance': lambda: self.search_car_information(f"maintenance costs and service: {user_query}"),
            'comparison': lambda: self.search_car_information(f"car comparison: {user_query}"),
            'market': lambda: self.get_market_insights(user_query),
            'history': lambda: self.search_car_information(f"history and background: {user_query}")
        }

        handler = category_handlers.get(category.lower())
        if handler:
            return handler()
        else:
            return self.search_car_information(user_query)

    def is_external_knowledge_query(self, query: str) -> tuple[bool, str]:
        """
        Determine if a query requires external knowledge beyond database specs.

        Args:
            query: User's query

        Returns:
            Tuple of (needs_external_search, category)
        """
        external_keywords = {
            'reliability': ['reliable', 'problems', 'issues', 'quality', 'durability'],
            'reviews': ['review', 'rating', 'opinion', 'experience', 'reputation'],
            'performance': ['fast', 'slow', 'acceleration', 'handling', 'ride quality'],
            'maintenance': ['maintenance', 'service', 'repair', 'parts', 'cost to own'],
            'comparison': ['better', 'worse', 'compare', 'vs', 'versus', 'difference'],
            'market': ['market', 'trend', 'popular', 'demand', 'price trend'],
            'history': ['history', 'first introduced', 'when launched', 'background', 'story'],
            'safety': ['safe', 'safety', 'crash test', 'airbag', 'stability'],
            'fuel': ['fuel economy', 'mpg', 'consumption', 'efficient', 'gas mileage']
        }

        query_lower = query.lower()

        for category, keywords in external_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return True, category

        # Check for general automotive questions
        general_indicators = ['how', 'why', 'when', 'should i', 'is it', 'does it', 'can it']
        if any(indicator in query_lower for indicator in general_indicators):
            return True, 'general'

        return False, 'database'