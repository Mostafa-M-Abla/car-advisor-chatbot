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
        self.response_generator = ResponseGenerator()
        self.conversation_manager = ConversationManager(
            max_history=self.config.get('conversation', {}).get('max_history', 10)
        )

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
            result = self.db_handler.execute_query("SELECT COUNT(*) as total FROM cars")
            total_cars = result[0]['total'] if result else 0
            if total_cars == 0:
                raise ValueError("Database appears to be empty")
            self.logger.info(f"Database validated: {total_cars} cars available")
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
        Process a single user message using unified LLM approach.

        Args:
            user_input: User's input message

        Returns:
            Bot's response
        """
        try:
            self.logger.info(f"Processing user message: {user_input}")

            # Get conversation context
            context = self.conversation_manager.get_conversation_context()

            # Use unified LLM call (handles database, knowledge, or hybrid)
            return self._unified_llm_handler(user_input, context)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            error_msg = "I encountered an error. Please try again."
            self.conversation_manager.add_turn(
                user_input=user_input,
                bot_response=error_msg,
                response_type="error"
            )
            return error_msg

    def _unified_llm_handler(self, user_input: str, context: str) -> str:
        """
        Unified LLM handler using single prompt for all query types.
        Handles database queries, knowledge queries, and hybrid scenarios.

        Args:
            user_input: User's query
            context: Conversation context

        Returns:
            Bot's response
        """
        try:
            # Load unified prompt from config
            unified_prompt = self.config.get('prompts', {}).get('unified_prompt', '')
            if not unified_prompt:
                raise ValueError("Unified prompt not found in configuration")

            # Get schema and synonyms
            schema_str = yaml.dump(self.query_processor.schema, default_flow_style=False)
            synonyms_str = yaml.dump(self.query_processor.synonyms, default_flow_style=False)

            # Format prompt with schema, synonyms, user input, and context
            formatted_prompt = unified_prompt.format(
                schema=schema_str,
                synonyms=synonyms_str,
                user_input=user_input,
                context=context if context else "No previous conversation."
            )

            # Call GPT-4.1
            self.logger.info("Calling GPT-4.1 with unified prompt")
            response = self.query_processor.openai_client.chat.completions.create(
                model=self.config.get('openai', {}).get('model', 'gpt-4.1'),
                messages=[
                    {"role": "system", "content": "You are an expert car advisor for the Egyptian automotive market. Always respond with valid JSON."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=self.config.get('openai', {}).get('temperature', 0.1),
                max_tokens=self.config.get('openai', {}).get('max_tokens', 1000)
            )

            # Parse JSON response
            import json
            response_text = response.choices[0].message.content.strip()

            # Clean markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            self.logger.info(f"LLM raw response: {response_text[:200]}...")

            try:
                llm_output = json.loads(response_text)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                self.logger.error(f"Raw response: {response_text}")
                error_msg = "I'm having trouble understanding how to respond. Could you rephrase your question?"
                self.conversation_manager.add_turn(
                    user_input=user_input,
                    bot_response=error_msg,
                    response_type="error"
                )
                return error_msg

            # Extract fields from JSON
            needs_database = llm_output.get('needs_database', False)
            sql_query = llm_output.get('sql_query', '')
            response_type = llm_output.get('response_type', 'knowledge')
            final_response = llm_output.get('response', '')

            # If needs database, execute SQL and use formatted results
            if needs_database and sql_query:
                self.logger.info(f"Executing SQL: {sql_query}")

                # Validate SQL
                if self.db_handler.validate_query(sql_query):
                    results = self.db_handler.execute_query(sql_query)
                    self.logger.info(f"SQL returned {len(results)} results")

                    # Always use formatted results for database queries
                    # The LLM's response might have placeholders, so we use our formatting
                    results_summary = self._format_results(results, user_input)

                    # For hybrid queries, prepend the LLM's additional context/advice
                    if response_type == "hybrid" and final_response and len(final_response) > 50:
                        # Check if response has actual advice (not placeholders)
                        if "[" not in final_response:  # No placeholders
                            final_response = final_response + "\n\n" + results_summary
                        else:
                            final_response = results_summary
                    else:
                        final_response = results_summary

                    # Add to conversation history
                    self.conversation_manager.add_turn(
                        user_input=user_input,
                        bot_response=final_response,
                        sql_query=sql_query,
                        results_count=len(results),
                        response_type=response_type
                    )
                else:
                    self.logger.warning(f"SQL validation failed: {sql_query}")
                    error_msg = "I couldn't process that search query. Could you try rephrasing it with more specific criteria?"
                    self.conversation_manager.add_turn(
                        user_input=user_input,
                        bot_response=error_msg,
                        response_type="error"
                    )
                    return error_msg
            else:
                # Knowledge-only response
                self.conversation_manager.add_turn(
                    user_input=user_input,
                    bot_response=final_response,
                    response_type=response_type
                )

            return final_response

        except Exception as e:
            self.logger.error(f"Error in unified LLM handler: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            error_msg = "I'm having trouble processing your request. Please try again."
            self.conversation_manager.add_turn(
                user_input=user_input,
                bot_response=error_msg,
                response_type="error"
            )
            return error_msg

    def _format_results(self, results: List[Dict[str, Any]], user_query: str) -> str:
        """
        Format database results using response_generator's formatting methods.

        Args:
            results: List of car dictionaries from database
            user_query: Original user query

        Returns:
            Formatted response string
        """
        if not results:
            return "I couldn't find any cars matching your criteria. Try adjusting your budget, features, or origin preferences."

        # Use response_generator's formatting
        return self.response_generator.format_results_summary(results, len(results), user_query)


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

        print(f"\n📊 SESSION STATISTICS:")
        print(f"   ⏱️  Duration: {stats['duration_minutes']} minutes")
        print(f"   💬 Total queries: {stats['total_queries']}")
        print(f"   ✅ Successful searches: {stats['successful_searches']}")
        print(f"   📈 Success rate: {stats['success_rate']:.1f}%")
        print(f"   ❓ Clarification requests: {stats['clarification_requests']}")
        print(f"   🧠 Knowledge questions: {stats['knowledge_questions']}")
        print(f"   🔄 Conversation turns: {stats['conversation_turns']}\n")

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