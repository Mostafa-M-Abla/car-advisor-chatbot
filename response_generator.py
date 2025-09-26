import yaml
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
import os

class ResponseGenerator:
    """Generates conversational responses using GPT-4 and car data."""

    def __init__(self, config_path: str = "chatbot_config.yaml"):
        self.config_path = config_path
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

    def format_price(self, price: Optional[int]) -> str:
        """Format price with proper EGP formatting."""
        if price is None:
            return "N/A"
        return f"{price:,} EGP"

    def format_car_result(self, car: Dict[str, Any], rank: int = None) -> str:
        """
        Format a single car result for display.

        Args:
            car: Car data dictionary
            rank: Optional ranking number

        Returns:
            Formatted car information string
        """
        rank_prefix = f"{rank}. " if rank else ""

        brand = car.get('car_brand', 'Unknown')
        model = car.get('car_model', 'Unknown')
        trim = car.get('car_trim', '')
        price = self.format_price(car.get('Price_EGP'))
        body_type = car.get('body_type', 'Unknown')
        origin = car.get('Origin_Country', 'Unknown')
        transmission = car.get('Transmission_Type', 'Unknown')

        # Build the basic info
        result = f"{rank_prefix}**{brand} {model}"
        if trim:
            result += f" {trim}"
        result += "**\n"

        result += f"   **Price**: {price}\n"
        result += f"   **Type**: {body_type.title()}\n"
        result += f"   **Origin**: {origin.title()}\n"
        result += f"   **Transmission**: {transmission.title()}\n"

        # Add engine information
        engine_cc = car.get('Engine_CC')
        if engine_cc:
            result += f"   🔧 **Engine**: {engine_cc}cc"
            if car.get('Engine_Turbo'):
                result += " Turbo"
            result += "\n"

        # Add key features
        features = []
        safety_features = []
        comfort_features = []
        tech_features = []

        # Safety features
        if car.get('ABS'):
            safety_features.append("ABS")
        if car.get('ESP'):
            safety_features.append("ESP")
        if car.get('Driver_Airbag'):
            safety_features.append("Driver Airbag")
        if car.get('Passenger_Airbag'):
            safety_features.append("Passenger Airbag")

        # Comfort features
        if car.get('Air_Conditioning'):
            comfort_features.append("A/C")
        if car.get('Power_Steering'):
            comfort_features.append("Power Steering")
        if car.get('Sunroof'):
            comfort_features.append("Sunroof")
        if car.get('Cruise_Control'):
            comfort_features.append("Cruise Control")
        if car.get('Leather_Seats'):
            comfort_features.append("Leather Seats")

        # Technology features
        if car.get('Bluetooth'):
            tech_features.append("Bluetooth")
        if car.get('GPS'):
            tech_features.append("GPS")
        if car.get('Rear_Camera'):
            tech_features.append("Rear Camera")
        if car.get('Multimedia_Touch_Screen'):
            tech_features.append("Touch Screen")

        # Special indicators
        if car.get('electric_vehicle'):
            result += f"   ⚡ **Electric Vehicle**\n"

        # Combine features
        if safety_features:
            result += f"   🛡️ **Safety**: {', '.join(safety_features)}\n"
        if comfort_features:
            result += f"   ✨ **Comfort**: {', '.join(comfort_features)}\n"
        if tech_features:
            result += f"   📱 **Tech**: {', '.join(tech_features)}\n"

        return result

    def format_results_summary(self, results: List[Dict[str, Any]],
                              total_found: int,
                              user_query: str) -> str:
        """
        Format a summary of search results.

        Args:
            results: List of car dictionaries
            total_found: Total number of cars found
            user_query: Original user query

        Returns:
            Formatted summary string
        """
        if not results:
            return "No cars found matching your criteria."

        summary = f"Found **{total_found}** car{'s' if total_found != 1 else ''} matching your criteria"

        if len(results) < total_found:
            summary += f" (showing top {len(results)})"

        summary += ":\n\n"

        # Add individual car results
        for i, car in enumerate(results, 1):
            summary += self.format_car_result(car, i)
            summary += "\n"

        return summary

    def generate_response(self,
                         user_input: str,
                         sql_query: str,
                         results: List[Dict[str, Any]],
                         context: str = "",
                         criteria: Dict[str, Any] = None) -> str:
        """
        Generate a conversational response using GPT-4.

        Args:
            user_input: Original user query
            sql_query: SQL query used
            results: Query results
            context: Conversation context
            criteria: Extracted criteria

        Returns:
            Generated response
        """
        try:
            # Format results for GPT-4 context
            results_summary = self.format_results_summary(results, len(results), user_input)

            # Get prompts from config
            prompts = self.config.get('prompts', {})
            system_prompt = prompts.get('system_prompt', '')
            response_prompt = prompts.get('response_generation_prompt', '')

            # Build the user prompt
            user_prompt = response_prompt.format(
                user_input=user_input,
                sql_query=sql_query,
                results=results_summary,
                count=len(results)
            )

            response = self.openai_client.chat.completions.create(
                model=self.config.get('openai', {}).get('model', 'gpt-4.1'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.get('openai', {}).get('temperature', 0.1),
                max_tokens=self.config.get('openai', {}).get('max_tokens', 1000)
            )

            generated_response = response.choices[0].message.content.strip()

            # If GPT-4 response is too generic, enhance with formatted results
            if len(generated_response) < 100 and results:
                enhanced_response = self._enhance_response(generated_response, results, criteria)
                return enhanced_response

            return generated_response

        except Exception as e:
            self.logger.error(f"Error generating response with GPT-4: {e}")
            # Fallback to formatted results
            return self._create_fallback_response(user_input, results, criteria)

    def _enhance_response(self, base_response: str,
                         results: List[Dict[str, Any]],
                         criteria: Dict[str, Any] = None) -> str:
        """Enhance a basic response with detailed car information."""
        enhanced = base_response + "\n\n"

        if results:
            enhanced += self.format_results_summary(results, len(results), "")

            # Add helpful follow-up suggestions
            if len(results) > 1:
                enhanced += "\n💡 **Want to know more about any of these cars?** Just ask me about specific features, comparisons, or detailed specs!"

        return enhanced

    def _create_fallback_response(self, user_input: str,
                                 results: List[Dict[str, Any]],
                                 criteria: Dict[str, Any] = None) -> str:
        """Create a fallback response when GPT-4 fails."""
        if not results:
            return self._generate_no_results_response(criteria)

        response = f"Here are the cars I found based on your request:\n\n"
        response += self.format_results_summary(results, len(results), user_input)

        return response

    def _generate_no_results_response(self, criteria: Dict[str, Any] = None) -> str:
        """Generate response when no cars are found."""
        response = "I couldn't find any cars matching your exact criteria. "

        suggestions = []

        if criteria:
            if 'max_price' in criteria:
                new_budget = int(criteria['max_price'] * 1.2)
                suggestions.append(f"increase your budget to {self.format_price(new_budget)}")

            if 'exclude_origin' in criteria:
                suggestions.append(f"include cars from {criteria['exclude_origin'].title()}")

            if 'body_type' in criteria:
                alternative_types = {
                    'sedan': 'hatchback',
                    'hatchback': 'sedan',
                    'crossover/suv': 'sedan',
                    'coupe': 'sedan',
                    'convertible': 'coupe'
                }
                alt = alternative_types.get(criteria['body_type'])
                if alt:
                    suggestions.append(f"consider {alt}s instead of {criteria['body_type']}s")

            if 'transmission' in criteria and criteria['transmission'] == 'automatic':
                suggestions.append("consider manual transmission")

        if suggestions:
            response += "Here are some suggestions:\n"
            for i, suggestion in enumerate(suggestions[:3], 1):
                response += f"{i}. {suggestion.title()}\n"

        response += "\nWould you like me to try one of these alternatives?"

        return response

    def generate_clarification_request(self, user_input: str,
                                     unclear_aspects: List[str]) -> str:
        """
        Generate a clarification request when user input is ambiguous.

        Args:
            user_input: Original user input
            unclear_aspects: List of unclear aspects

        Returns:
            Clarification request
        """
        try:
            prompts = self.config.get('prompts', {})
            clarification_prompt = prompts.get('clarification_prompt', '')

            if not clarification_prompt:
                return self._create_fallback_clarification(unclear_aspects)

            user_prompt = clarification_prompt.format(
                user_input=user_input,
                unclear_aspects=", ".join(unclear_aspects)
            )

            response = self.openai_client.chat.completions.create(
                model=self.config.get('openai', {}).get('model', 'gpt-4.1'),
                messages=[
                    {"role": "system", "content": "You are a helpful car advisor asking for clarification."},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            self.logger.error(f"Error generating clarification request: {e}")
            return self._create_fallback_clarification(unclear_aspects)

    def _create_fallback_clarification(self, unclear_aspects: List[str]) -> str:
        """Create a fallback clarification request."""
        clarifications = {
            'budget': "What's your budget range in EGP?",
            'body_type': "What type of car are you looking for? (sedan, hatchback, crossover/SUV, etc.)",
            'transmission': "Do you prefer automatic or manual transmission?",
            'origin': "Any preference for the car's country of origin?",
            'features': "Are there any specific features you need? (ABS, ESP, sunroof, etc.)"
        }

        questions = []
        for aspect in unclear_aspects:
            if aspect in clarifications:
                questions.append(clarifications[aspect])

        if not questions:
            questions = ["Could you provide more details about what you're looking for?"]

        response = "I need a bit more information to help you better:\n\n"
        for i, question in enumerate(questions, 1):
            response += f"{i}. {question}\n"

        return response

    def generate_general_knowledge_response(self, question: str) -> str:
        """
        Generate response for general automotive questions not in database.

        Args:
            question: User's general automotive question

        Returns:
            Generated response using GPT-4's knowledge
        """
        try:
            system_prompt = """You are an expert automotive consultant with comprehensive knowledge about cars,
            their specifications, market trends, and technology. Provide helpful, accurate, and concise answers
            about automotive topics. Focus on information relevant to the Egyptian automotive market when applicable."""

            response = self.openai_client.chat.completions.create(
                model=self.config.get('openai', {}).get('model', 'gpt-4.1'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.2,
                max_tokens=500
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            self.logger.error(f"Error generating general knowledge response: {e}")
            return "I'm sorry, I'm having trouble accessing my automotive knowledge right now. Could you try rephrasing your question or ask about specific cars in my database?"