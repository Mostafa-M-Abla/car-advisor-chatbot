from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation (SIMPLIFIED)."""
    timestamp: datetime = field(default_factory=datetime.now)
    user_input: str = ""
    bot_response: str = ""
    sql_query: str = ""
    results_count: int = 0
    response_type: str = "search"  # search, clarification, knowledge, error

class ConversationManager:
    """Manages conversation history and context for the chatbot."""

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[ConversationTurn] = []
        self.session_stats: Dict[str, Any] = {
            'total_queries': 0,
            'successful_searches': 0,
            'clarification_requests': 0,
            'knowledge_questions': 0,
            'session_start': datetime.now()
        }
        self.logger = logging.getLogger(__name__)

    def add_turn(self,
                 user_input: str,
                 bot_response: str,
                 sql_query: str = "",
                 results_count: int = 0,
                 response_type: str = "search") -> None:
        """
        Add a new conversation turn to the history (SIMPLIFIED).

        Args:
            user_input: User's input message
            bot_response: Bot's response message
            sql_query: SQL query used (if any)
            results_count: Number of results returned
            response_type: Type of response (search, clarification, knowledge, error)

        Note:
            Removed criteria parameter and preference tracking after simplification.
            Conversation history is still tracked for context generation.
        """
        turn = ConversationTurn(
            user_input=user_input,
            bot_response=bot_response,
            sql_query=sql_query,
            results_count=results_count,
            response_type=response_type
        )

        self.history.append(turn)

        # Maintain max history limit
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Update session statistics
        self.session_stats['total_queries'] += 1
        if response_type == "search" and results_count > 0:
            self.session_stats['successful_searches'] += 1
        elif response_type == "clarification":
            self.session_stats['clarification_requests'] += 1
        elif response_type == "knowledge":
            self.session_stats['knowledge_questions'] += 1

        self.logger.info(f"Added conversation turn: {response_type}, {results_count} results")

    def get_conversation_context(self, turns: int = 6) -> str:
        """
        Get conversation context for the last N turns.

        Args:
            turns: Number of recent turns to include in context

        Returns:
            Formatted conversation context string
        """
        if not self.history:
            return ""

        recent_history = self.history[-turns:] if len(self.history) >= turns else self.history

        context_parts = []
        for i, turn in enumerate(recent_history):
            context_parts.append(f"Turn {i+1}:")
            context_parts.append(f"User: {turn.user_input}")
            context_parts.append(f"Bot: {turn.bot_response[:100]}..." if len(turn.bot_response) > 100 else f"Bot: {turn.bot_response}")
            context_parts.append("")

        return "\n".join(context_parts)

    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session."""
        session_duration = datetime.now() - self.session_stats['session_start']

        return {
            'duration_minutes': int(session_duration.total_seconds() / 60),
            'total_queries': self.session_stats['total_queries'],
            'successful_searches': self.session_stats['successful_searches'],
            'success_rate': (self.session_stats['successful_searches'] / max(1, self.session_stats['total_queries'])) * 100,
            'clarification_requests': self.session_stats['clarification_requests'],
            'knowledge_questions': self.session_stats['knowledge_questions'],
            'conversation_turns': len(self.history)
        }

    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.history.clear()
        self.session_stats = {
            'total_queries': 0,
            'successful_searches': 0,
            'clarification_requests': 0,
            'knowledge_questions': 0,
            'session_start': datetime.now()
        }
        self.logger.info("Conversation history cleared")

    def export_conversation(self, filepath: str) -> bool:
        """
        Export conversation history to a JSON file.

        Args:
            filepath: Path to save the conversation

        Returns:
            True if successful, False otherwise
        """
        try:
            export_data = {
                'session_stats': self.session_stats,
                'history': []
            }

            for turn in self.history:
                turn_data = {
                    'timestamp': turn.timestamp.isoformat(),
                    'user_input': turn.user_input,
                    'bot_response': turn.bot_response,
                    'sql_query': turn.sql_query,
                    'results_count': turn.results_count,
                    'response_type': turn.response_type
                }
                export_data['history'].append(turn_data)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Conversation exported to {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export conversation: {e}")
            return False