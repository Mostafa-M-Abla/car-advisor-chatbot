import os
import yaml
import logging
import sys
from typing import Dict, Any, List
from dotenv import load_dotenv

# Import our custom modules
from database.database_handler import DatabaseHandler
from chatbot.query_processor import QueryProcessor
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

    def _get_sql_tool_definition(self) -> Dict[str, Any]:
        """
        Define the SQL query execution tool for OpenAI function calling.

        Returns:
            Tool definition dictionary
        """
        return {
            "type": "function",
            "function": {
                "name": "execute_sql_query",
                "description": "Execute a SQL query against the car database to search for vehicles. Returns a list of car records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql_query": {
                            "type": "string",
                            "description": "A valid SELECT SQL query to execute against the 'cars' table. Must be a safe, read-only SELECT statement."
                        }
                    },
                    "required": ["sql_query"]
                }
            }
        }

    def _execute_sql_tool(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute SQL query and return results for the LLM.

        Args:
            sql_query: SQL query to execute

        Returns:
            Dictionary with success status and results or error message
        """
        try:
            # Validate SQL
            if not self.db_handler.validate_query(sql_query):
                return {
                    "success": False,
                    "error": "SQL query failed validation (must be SELECT from cars table only)"
                }

            # Execute query
            results = self.db_handler.execute_query(sql_query)
            self.logger.info(f"SQL query returned {len(results)} results")

            return {
                "success": True,
                "results_count": len(results),
                "results": results[:20]  # Limit to 20 results to avoid token overflow
            }

        except Exception as e:
            self.logger.error(f"Error executing SQL tool: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _unified_llm_handler(self, user_input: str, context: str) -> str:
        """
        Agentic LLM handler with SQL tool calling (max 3 iterations).
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

            # Format system prompt with schema and synonyms
            system_prompt = unified_prompt.format(
                schema=schema_str,
                synonyms=synonyms_str
            )

            # Initialize conversation messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Conversation context: {context if context else 'No previous conversation.'}\n\nUser query: {user_input}"}
            ]

            # Tool definition
            tools = [self._get_sql_tool_definition()]

            # Multi-turn agent loop (max 3 tool calls)
            max_iterations = 3
            iteration = 0
            sql_queries_executed = []

            while iteration < max_iterations:
                self.logger.info(f"Agent iteration {iteration + 1}/{max_iterations}")

                # Call GPT-4.1 with tool support
                response = self.query_processor.openai_client.chat.completions.create(
                    model=self.config.get('openai', {}).get('model', 'gpt-4.1'),
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=self.config.get('openai', {}).get('temperature', 0.1),
                    max_tokens=self.config.get('openai', {}).get('max_tokens', 1500)
                )

                assistant_message = response.choices[0].message

                # Add assistant's response to messages
                messages.append(assistant_message)

                # Check if assistant wants to call a tool
                if assistant_message.tool_calls:
                    for tool_call in assistant_message.tool_calls:
                        if tool_call.function.name == "execute_sql_query":
                            # Parse arguments
                            import json
                            args = json.loads(tool_call.function.arguments)
                            sql_query = args.get('sql_query', '')

                            self.logger.info(f"LLM requested SQL execution: {sql_query}")
                            sql_queries_executed.append(sql_query)

                            # Execute SQL tool
                            tool_result = self._execute_sql_tool(sql_query)

                            # Add tool result to messages
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(tool_result)
                            })

                    iteration += 1
                else:
                    # No tool calls, assistant provided final response
                    final_response = assistant_message.content

                    # Determine response type
                    response_type = "knowledge"
                    if sql_queries_executed:
                        response_type = "database" if len(sql_queries_executed) == 1 else "hybrid"

                    # Add to conversation history
                    self.conversation_manager.add_turn(
                        user_input=user_input,
                        bot_response=final_response,
                        sql_query=sql_queries_executed[-1] if sql_queries_executed else None,
                        results_count=None,  # We don't track this anymore
                        response_type=response_type
                    )

                    return final_response

            # If we hit max iterations, force final response
            self.logger.warning(f"Hit max iterations ({max_iterations}), forcing final response")
            final_response = assistant_message.content if assistant_message.content else "I've searched the database multiple times but I'm having trouble formulating a response. Could you rephrase your question?"

            self.conversation_manager.add_turn(
                user_input=user_input,
                bot_response=final_response,
                sql_query=sql_queries_executed[-1] if sql_queries_executed else None,
                response_type="database" if sql_queries_executed else "knowledge"
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