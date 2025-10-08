#!/usr/bin/env python3
"""
Simple launcher script for the Car Selection Chatbot.
Run this script to start the interactive chatbot.
"""

import sys
import os

# Add current directory to path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot.car_chatbot import main

if __name__ == "__main__":
    print("Starting the Egyptian Car Market Chatbot...")
    print("Please wait while we initialize all components...\n")
    main()