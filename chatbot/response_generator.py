"""
Utility functions for formatting car data.

This module provides optional utility functions that the LLM can reference.
The LLM now crafts all responses naturally - these are just helpers if needed.

"""

from typing import Optional


def format_price(price: Optional[int]) -> str:
    """
    Format price with proper EGP formatting.

    Args:
        price: Price value in EGP

    Returns:
        Formatted price string (e.g., "1,500,000 EGP")
    """
    if price is None:
        return "N/A"
    return f"{price:,} EGP"


