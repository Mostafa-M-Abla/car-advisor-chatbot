import logging
from typing import Dict, Any, List, Optional

class ResponseGenerator:
    """Formats car data for user-friendly presentation.

    SIMPLIFIED ARCHITECTURE (post-unification):
    This class now focuses solely on formatting database results.

    Previous responsibilities removed:
    - LLM-based response generation (now in unified prompt in car_chatbot.py)

    Benefits:
    - Pure formatting logic, no AI dependencies
    - Reusable formatting methods
    - Much simpler and focused
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

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

        summary = f"Found **{total_found}** ca{'s' if total_found != 1 else ''} matching your criteria"

        if len(results) < total_found:
            summary += f" (showing top {len(results)})"

        summary += ":\n\n"

        # Add individual car results
        for i, car in enumerate(results, 1):
            summary += self.format_car_result(car, i)
            summary += "\n"

        return summary


