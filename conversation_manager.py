from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""
    timestamp: datetime = field(default_factory=datetime.now)
    user_input: str = ""
    bot_response: str = ""
    sql_query: str = ""
    results_count: int = 0
    criteria: Dict[str, Any] = field(default_factory=dict)
    response_type: str = "search"  # search, clarification, general, error

class ConversationManager:
    """Manages conversation history and context for the chatbot."""

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[ConversationTurn] = []
        self.user_preferences: Dict[str, Any] = {}
        self.session_stats: Dict[str, Any] = {
            'total_queries': 0,
            'successful_searches': 0,
            'clarification_requests': 0,
            'general_questions': 0,
            'session_start': datetime.now()
        }
        self.logger = logging.getLogger(__name__)

    def add_turn(self,
                 user_input: str,
                 bot_response: str,
                 sql_query: str = "",
                 results_count: int = 0,
                 criteria: Dict[str, Any] = None,
                 response_type: str = "search") -> None:
        """
        Add a new conversation turn to the history.

        Args:
            user_input: User's input message
            bot_response: Bot's response message
            sql_query: SQL query used (if any)
            results_count: Number of results returned
            criteria: Search criteria used
            response_type: Type of response (search, clarification, general, error)
        """
        if criteria is None:
            criteria = {}

        turn = ConversationTurn(
            user_input=user_input,
            bot_response=bot_response,
            sql_query=sql_query,
            results_count=results_count,
            criteria=criteria,
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
        elif response_type == "general":
            self.session_stats['general_questions'] += 1

        # Update user preferences based on criteria
        self._update_user_preferences(criteria)

        self.logger.info(f"Added conversation turn: {response_type}, {results_count} results")

    def _update_user_preferences(self, criteria: Dict[str, Any]) -> None:
        """Update user preferences based on search criteria."""
        if not criteria:
            return

        # Track price preferences
        if 'max_price' in criteria:
            if 'preferred_max_price' not in self.user_preferences:
                self.user_preferences['preferred_max_price'] = criteria['max_price']
            else:
                # Update with average of previous preferences
                current = self.user_preferences['preferred_max_price']
                self.user_preferences['preferred_max_price'] = (current + criteria['max_price']) // 2

        if 'min_price' in criteria:
            if 'preferred_min_price' not in self.user_preferences:
                self.user_preferences['preferred_min_price'] = criteria['min_price']
            else:
                current = self.user_preferences['preferred_min_price']
                self.user_preferences['preferred_min_price'] = (current + criteria['min_price']) // 2

        # Track body type preferences
        if 'body_type' in criteria:
            if 'preferred_body_types' not in self.user_preferences:
                self.user_preferences['preferred_body_types'] = []
            if criteria['body_type'] not in self.user_preferences['preferred_body_types']:
                self.user_preferences['preferred_body_types'].append(criteria['body_type'])

        # Track transmission preferences
        if 'transmission' in criteria:
            self.user_preferences['preferred_transmission'] = criteria['transmission']

        # Track origin preferences
        if 'origin_country' in criteria:
            if 'preferred_origins' not in self.user_preferences:
                self.user_preferences['preferred_origins'] = []
            if criteria['origin_country'] not in self.user_preferences['preferred_origins']:
                self.user_preferences['preferred_origins'].append(criteria['origin_country'])

        if 'exclude_origin' in criteria:
            if 'excluded_origins' not in self.user_preferences:
                self.user_preferences['excluded_origins'] = []
            if criteria['exclude_origin'] not in self.user_preferences['excluded_origins']:
                self.user_preferences['excluded_origins'].append(criteria['exclude_origin'])

        # Track feature preferences
        feature_keys = [key for key in criteria.keys()
                       if key.endswith(('_turbo', '_abs', '_esp', '_conditioning', '_sunroof', '_bluetooth', '_gps'))]

        if feature_keys:
            if 'preferred_features' not in self.user_preferences:
                self.user_preferences['preferred_features'] = []
            for feature in feature_keys:
                if feature not in self.user_preferences['preferred_features']:
                    self.user_preferences['preferred_features'].append(feature)

    def get_conversation_context(self, turns: int = 3) -> str:
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

            if turn.criteria:
                criteria_str = ", ".join([f"{k}: {v}" for k, v in turn.criteria.items()])
                context_parts.append(f"Criteria: {criteria_str}")

            context_parts.append("")

        return "\n".join(context_parts)

    def get_user_preferences_summary(self) -> str:
        """Get a summary of user preferences learned from conversation."""
        if not self.user_preferences:
            return "No preferences learned yet."

        summary_parts = []

        # Price preferences
        if 'preferred_max_price' in self.user_preferences or 'preferred_min_price' in self.user_preferences:
            min_price = self.user_preferences.get('preferred_min_price', 0)
            max_price = self.user_preferences.get('preferred_max_price', float('inf'))
            price_range = f"{min_price:,}" if min_price > 0 else "No minimum"
            if max_price != float('inf'):
                price_range += f" - {max_price:,} EGP"
            else:
                price_range += " EGP and up"
            summary_parts.append(f"Budget: {price_range}")

        # Body type preferences
        if 'preferred_body_types' in self.user_preferences:
            body_types = ", ".join(self.user_preferences['preferred_body_types'])
            summary_parts.append(f"Body types: {body_types}")

        # Transmission preference
        if 'preferred_transmission' in self.user_preferences:
            summary_parts.append(f"Transmission: {self.user_preferences['preferred_transmission']}")

        # Origin preferences
        if 'preferred_origins' in self.user_preferences:
            origins = ", ".join(self.user_preferences['preferred_origins'])
            summary_parts.append(f"Preferred origins: {origins}")

        if 'excluded_origins' in self.user_preferences:
            excluded = ", ".join(self.user_preferences['excluded_origins'])
            summary_parts.append(f"Excluded origins: {excluded}")

        # Feature preferences
        if 'preferred_features' in self.user_preferences:
            features = ", ".join(self.user_preferences['preferred_features'])
            summary_parts.append(f"Important features: {features}")

        return "; ".join(summary_parts) if summary_parts else "No specific preferences identified."

    def should_ask_for_clarification(self, user_input: str) -> tuple[bool, List[str]]:
        """
        Determine if clarification is needed based on user input.

        Args:
            user_input: User's input message

        Returns:
            Tuple of (needs_clarification, list_of_unclear_aspects)
        """
        unclear_aspects = []
        user_lower = user_input.lower()

        # Check for vague price mentions
        if any(word in user_lower for word in ['cheap', 'expensive', 'affordable', 'budget']) and \
           not any(char.isdigit() for char in user_input):
            unclear_aspects.append('budget')

        # Check for vague body type mentions
        if 'car' in user_lower and not any(body_type in user_lower for body_type in
                                          ['sedan', 'hatchback', 'crossover', 'suv', 'coupe', 'convertible', 'van']):
            unclear_aspects.append('body_type')

        # Check for vague feature requests
        if any(word in user_lower for word in ['good', 'nice', 'best', 'quality']) and \
           len(user_input.split()) < 5:
            unclear_aspects.append('features')

        # Check if input is too short or vague
        if len(user_input.split()) < 3 and not any(char.isdigit() for char in user_input):
            unclear_aspects.append('general')

        return len(unclear_aspects) > 0, unclear_aspects

    def get_refined_criteria(self, new_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine search criteria based on user preferences and conversation history.

        Args:
            new_criteria: New search criteria from current query

        Returns:
            Refined criteria incorporating user preferences
        """
        refined = new_criteria.copy()

        # Apply learned preferences if not explicitly specified
        if not refined.get('max_price') and 'preferred_max_price' in self.user_preferences:
            refined['max_price'] = self.user_preferences['preferred_max_price']

        if not refined.get('min_price') and 'preferred_min_price' in self.user_preferences:
            refined['min_price'] = self.user_preferences['preferred_min_price']

        if not refined.get('transmission') and 'preferred_transmission' in self.user_preferences:
            refined['transmission'] = self.user_preferences['preferred_transmission']

        # Apply consistent exclusions
        if not refined.get('exclude_origin') and 'excluded_origins' in self.user_preferences:
            # Use the most recently excluded origin
            refined['exclude_origin'] = self.user_preferences['excluded_origins'][-1]

        return refined

    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session."""
        session_duration = datetime.now() - self.session_stats['session_start']

        return {
            'duration_minutes': int(session_duration.total_seconds() / 60),
            'total_queries': self.session_stats['total_queries'],
            'successful_searches': self.session_stats['successful_searches'],
            'success_rate': (self.session_stats['successful_searches'] / max(1, self.session_stats['total_queries'])) * 100,
            'clarification_requests': self.session_stats['clarification_requests'],
            'general_questions': self.session_stats['general_questions'],
            'conversation_turns': len(self.history),
            'user_preferences': self.user_preferences
        }

    def clear_conversation(self) -> None:
        """Clear conversation history but keep user preferences."""
        self.history.clear()
        self.session_stats = {
            'total_queries': 0,
            'successful_searches': 0,
            'clarification_requests': 0,
            'general_questions': 0,
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
                'user_preferences': self.user_preferences,
                'history': []
            }

            for turn in self.history:
                turn_data = {
                    'timestamp': turn.timestamp.isoformat(),
                    'user_input': turn.user_input,
                    'bot_response': turn.bot_response,
                    'sql_query': turn.sql_query,
                    'results_count': turn.results_count,
                    'criteria': turn.criteria,
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