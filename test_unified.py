#!/usr/bin/env python3
"""
Test script for the unified LLM architecture.
Tests database queries, knowledge queries, and hybrid scenarios.
"""

import os
import sys

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from chatbot.car_chatbot import CarChatbot

def test_queries():
    """Test various query types with the unified architecture."""

    # Initialize chatbot
    config_path = os.path.join(project_root, "chatbot", "chatbot_config.yaml")
    chatbot = CarChatbot(config_path=config_path)

    print("=" * 80)
    print("TESTING UNIFIED LLM ARCHITECTURE")
    print("=" * 80)
    print()

    # Test 1: Database query
    print("\n" + "-" * 80)
    print("TEST 1: Database Query - 'Show me crossovers under 2M EGP'")
    print("-" * 80)
    response = chatbot.process_message("Show me crossovers under 2M EGP")
    print(f"\nResponse:\n{response}\n")

    # Test 2: Knowledge query
    print("\n" + "-" * 80)
    print("TEST 2: Knowledge Query - 'Is the Toyota Camry reliable?'")
    print("-" * 80)
    response = chatbot.process_message("Is the Toyota Camry reliable?")
    print(f"\nResponse:\n{response}\n")

    # Test 3: Hybrid query (THIS WAS BROKEN BEFORE!)
    print("\n" + "-" * 80)
    print("TEST 3: Hybrid Query - 'Show me reliable SUVs under 2M EGP'")
    print("-" * 80)
    response = chatbot.process_message("Show me reliable SUVs under 2M EGP")
    print(f"\nResponse:\n{response}\n")

    # Test 4: Broad request that should proceed without excessive clarification
    print("\n" + "-" * 80)
    print("TEST 4: Broad Request - 'Any good sedan'")
    print("-" * 80)
    response = chatbot.process_message("Any good sedan")
    print(f"\nResponse:\n{response}\n")

    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_queries()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
