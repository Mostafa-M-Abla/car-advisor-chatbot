import os
import yaml
import logging
import sys
from typing import Dict, Any, List
from dotenv import load_dotenv

# Import our custom modules
from database.database_handler import DatabaseHandler
from chatbot.query_processor import QueryProcessor
from chatbot.response_generator import ResponseGenerator
from chatbot.conversation_manager import ConversationManager
from chatbot.knowledge_handler import KnowledgeHandler

class CarChatbot:
    """Main chatbot class that orchestrates all components."""

    def __init__(self, config_path: str = "chatbot_config.yaml"):
        # Load environment variables
        load_dotenv()

        # Set up logging
        self._setup_logging()

        # Load configuration
        self.config_path = config_path
        self.config = self._load_config()

        # Initialize components with correct paths
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, "database", "cars.db")
        schema_path = os.path.join(project_root, "database", "schema.yaml")
        self.db_handler = DatabaseHandler(db_path=db_path, schema_path=schema_path)
        synonyms_path = os.path.join(project_root, "database", "synonyms.yaml")
        self.query_processor = QueryProcessor(schema_path=schema_path, synonyms_path=synonyms_path, config_path=config_path)
        self.response_generator = ResponseGenerator(config_path)
        self.conversation_manager = ConversationManager(
            max_history=self.config.get('conversation', {}).get('max_history', 10)
        )
        self.knowledge_handler = KnowledgeHandler(config_path=config_path)

        self.logger = logging.getLogger(__name__)

        # Validate setup
        self._validate_setup()

        self.logger.info("Car chatbot initialized successfully")

    def _setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('../chatbot.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Warning: Failed to load config from {self.config_path}: {e}")
            return {}

    def _validate_setup(self):
        """Validate that all required components are properly set up."""
        # Check OpenAI API key
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY environment variable is required")

        # Check database
        try:
            stats = self.db_handler.get_database_stats()
            if stats.get('total_cars', 0) == 0:
                raise ValueError("Database appears to be empty")
            self.logger.info(f"Database validated: {stats['total_cars']} cars available")
        except Exception as e:
            raise ValueError(f"Database validation failed: {e}")

    def start_conversation(self):
        """Start the interactive chat interface."""
        # Display greeting - require it from config
        greeting = self.config.get('conversation', {}).get('greeting')
        if not greeting:
            raise ValueError("Greeting message not found in configuration file")
        print("\n" + "="*80)
        print("Welcome to the Egyptian Car Market Chatbot!")
        print("="*80)
        print(greeting)
        print("\n" + "-"*80)
        print("Commands: 'help' for assistance, 'stats' for session info, 'clear' to reset, 'export' to save, 'quit' to exit")
        print("-"*80 + "\n")

        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    self._handle_goodbye()
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'stats':
                    self._show_stats()
                    continue
                elif user_input.lower() == 'clear':
                    self._clear_conversation()
                    continue
                elif user_input.lower() == 'export':
                    self._export_conversation()
                    continue

                # Process the user's message
                response = self.process_message(user_input)
                print(f"\nBot: {response}\n")

            except KeyboardInterrupt:
                print("\n\nGoodbye! Thanks for using the car chatbot!")
                break
            except Exception as e:
                self.logger.error(f"Error in conversation loop: {e}")
                print(f"\nBot: I'm sorry, I encountered an error. Please try again.\n")

    def process_message(self, user_input: str) -> str:
        """
        Process a single user message and return the bot's response.

        Args:
            user_input: User's input message

        Returns:
            Bot's response
        """
        try:
            self.logger.info(f"Processing user message: {user_input}")

            # Get conversation context
            context = self.conversation_manager.get_conversation_context()

            # Check if this is an external knowledge query
            needs_external = self.knowledge_handler.is_external_knowledge_query(user_input)

            if needs_external:
                return self._handle_external_knowledge_query(user_input, context)

            # Process as database search query
            return self._handle_database_query(user_input, context)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            error_msg = self.config.get('error_messages', {}).get('general_error',
                                                                 "I encountered an error. Please try again.")
            self.conversation_manager.add_turn(
                user_input=user_input,
                bot_response=error_msg,
                response_type="error"
            )
            return error_msg

    def _handle_database_query(self, user_input: str, context: str) -> str:
        """Handle queries that search the car database."""
        try:
            # Parse the query
            criteria, sql_query = self.query_processor.parse_query(user_input, context)

            # Refine criteria based on user preferences
            refined_criteria = self.conversation_manager.get_refined_criteria(criteria)

            # Execute database search
            if sql_query and self.db_handler.validate_query(sql_query):
                # Use generated SQL query
                self.logger.info(f"Using AI-generated SQL query for: '{user_input}'")
                results = self.db_handler.execute_query(sql_query)
            else:
                # Fallback to structured search (non-AI)
                if not sql_query:
                    self.logger.warning(f"FALLBACK: No SQL query generated by AI for: '{user_input}'. Using non-AI search_cars() with criteria: {refined_criteria}")
                else:
                    self.logger.warning(f"FALLBACK: AI-generated SQL failed validation for: '{user_input}'. Query was: '{sql_query}'. Using non-AI search_cars() with criteria: {refined_criteria}")
                results = self.db_handler.search_cars(refined_criteria)

            # Generate response
            response = self.response_generator.generate_response(
                user_input=user_input,
                sql_query=sql_query,
                results=results,
                context=context,
                criteria=refined_criteria
            )

            # Add to conversation history
            self.conversation_manager.add_turn(
                user_input=user_input,
                bot_response=response,
                sql_query=sql_query,
                results_count=len(results),
                criteria=refined_criteria,
                response_type="search"
            )

            return response

        except Exception as e:
            self.logger.error(f"Error in database query: {e}")
            error_msg = self.config.get('error_messages', {}).get('database_error',
                                                                 "I'm having trouble accessing the car database.")
            self.conversation_manager.add_turn(
                user_input=user_input,
                bot_response=error_msg,
                response_type="error"
            )
            return error_msg

    def _handle_external_knowledge_query(self, user_input: str, context: str) -> str:
        """Handle queries that require external knowledge beyond the database."""
        try:
            # Check if query mentions specific cars from our database
            car_context = self._extract_car_context_from_query(user_input)

            # Use unified knowledge handler
            response = self.knowledge_handler.get_knowledge_response(
                query=user_input,
                conversation_context=context,
                database_context=car_context if car_context else None
            )

            # Add to conversation history
            self.conversation_manager.add_turn(
                user_input=user_input,
                bot_response=response,
                response_type="knowledge"
            )

            return response

        except Exception as e:
            self.logger.error(f"Error in external knowledge query: {e}")
            error_msg = "I'm sorry, I'm having trouble accessing external automotive knowledge right now. Could you try asking about specific cars in our database or rephrase your question?"
            self.conversation_manager.add_turn(
                user_input=user_input,
                bot_response=error_msg,
                response_type="error"
            )
            return error_msg

    def _extract_car_context_from_query(self, query: str) -> List[Dict[str, Any]]:
        """Extract car information mentioned in the query from the database."""
        # Simple approach: try to find brand/model mentions
        brands = self.db_handler.get_brands()
        mentioned_cars = []

        query_lower = query.lower()

        for brand in brands:
            if brand.lower() in query_lower:
                # Try to find specific models of this brand
                brand_cars = self.db_handler.execute_query(
                    "SELECT DISTINCT * FROM cars WHERE car_brand = ? LIMIT 5",
                    (brand,)
                )
                if brand_cars:
                    mentioned_cars.extend(brand_cars)

        return mentioned_cars[:2]  # Return up to 2 cars for comparison

    def _show_help(self):
        """Show help information."""
        help_text = """
CAR CHATBOT HELP

You can ask me about cars in various ways:

💰 BUDGET SEARCHES:
   • "Show me cars under 2 million EGP"
   • "What's the cheapest sedan?"
   • "Cars between 1.5 and 3 million EGP"

BY BODY TYPE:
   • "I want a crossover"
   • "Show me hatchbacks"
   • "Find me an SUV"

🌍 BY ORIGIN:
   • "Non-Chinese cars only"
   • "German cars"
   • "Japanese or Korean cars"

⚙️ BY FEATURES:
   • "Cars with automatic transmission and ESP"
   • "Electric vehicles"
   • "Cars with sunroof and GPS"

🔍 SPECIFIC QUESTIONS:
   • "Is the Toyota Camry reliable?"
   • "Compare Honda Civic vs Toyota Corolla"
   • "When was the BMW X5 first introduced?"

📊 COMMANDS:
   • 'help' - Show this help
   • 'stats' - Show session statistics
   • 'clear' - Clear conversation history
   • 'export' - Export conversation to JSON file
   • 'quit' - Exit the chatbot

Just ask naturally - I'll understand! 🤖
        """
        print(help_text)

    def _show_stats(self):
        """Show session statistics."""
        stats = self.conversation_manager.get_session_summary()
        db_stats = self.db_handler.get_database_stats()

        print(f"\n📊 SESSION STATISTICS:")
        print(f"   ⏱️  Duration: {stats['duration_minutes']} minutes")
        print(f"   💬 Total queries: {stats['total_queries']}")
        print(f"   ✅ Successful searches: {stats['successful_searches']}")
        print(f"   📈 Success rate: {stats['success_rate']:.1f}%")
        print(f"   ❓ Clarification requests: {stats['clarification_requests']}")

        if stats['user_preferences']:
            print(f"\n🎯 LEARNED PREFERENCES:")
            preferences = self.conversation_manager.get_user_preferences_summary()
            print(f"   {preferences}")

        print(f"\nDATABASE STATISTICS:")
        print(f"   📦 Total cars: {db_stats.get('total_cars', 0):,}")
        print(f"   🏢 Total brands: {db_stats.get('total_brands', 0)}")
        print(f"   💰 Price range: {db_stats.get('min_price', 0):,} - {db_stats.get('max_price', 0):,} EGP")

        if 'body_types' in db_stats:
            print(f"   🚙 Body types:")
            for body_type, count in list(db_stats['body_types'].items())[:5]:
                print(f"      • {body_type}: {count}")

    def _clear_conversation(self):
        """Clear conversation history."""
        self.conversation_manager.clear_conversation()
        print("✨ Conversation history cleared! Starting fresh.")

    def _export_conversation(self):
        """Export conversation history to a JSON file."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_export_{timestamp}.json"

        if self.conversation_manager.export_conversation(filename):
            print(f"✅ Conversation exported successfully to: {filename}")
        else:
            print("❌ Failed to export conversation. Please try again.")

    def _handle_goodbye(self):
        """Handle goodbye and show session summary."""
        stats = self.conversation_manager.get_session_summary()

        print(f"\nThanks for using the Car Chatbot!")
        print(f"Session Summary:")
        print(f"   • {stats['total_queries']} queries processed")
        print(f"   • {stats['successful_searches']} successful car searches")
        print(f"   • {stats['duration_minutes']} minutes of conversation")

        if stats['user_preferences']:
            print(f"   • Learned your preferences: {self.conversation_manager.get_user_preferences_summary()}")

        print(f"\nHappy car hunting! 🚙")

def main():
    """Main entry point for the chatbot."""
    try:
        # Determine correct config path relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "chatbot", "chatbot_config.yaml")
        chatbot = CarChatbot(config_path=config_path)
        chatbot.start_conversation()
    except ValueError as e:
        print(f"Setup Error: {e}")
        print("Please ensure all requirements are met and try again.")
    except Exception as e:
        print(f"Unexpected Error: {e}")
        print("An unexpected error occurred. Please check the logs for details.")

if __name__ == "__main__":
    main()