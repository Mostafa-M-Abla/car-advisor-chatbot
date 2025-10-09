"""
Gradio Web Interface for Egyptian Car Market AI Chatbot

This script creates a user-friendly web interface for the car chatbot using Gradio.
Users can interact with the chatbot through a modern chat interface with example prompts.
"""

import os
import gradio as gr
from chatbot.car_chatbot import CarChatbot

# Determine correct config path
project_root = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(project_root, "chatbot", "chatbot_config.yaml")

# Initialize chatbot
print("Initializing car chatbot...")
chatbot = CarChatbot(config_path=config_path)
print("Chatbot initialized successfully!")


def chat_response(message, history):
    """
    Process user message and return chatbot response.

    Args:
        message: User's input message
        history: Chat history (automatically managed by Gradio)

    Returns:
        Chatbot's response
    """
    try:
        response = chatbot.process_message(message)
        return response
    except Exception as e:
        error_msg = f"I encountered an error: {str(e)}. Please try again."
        return error_msg


# Create Gradio ChatInterface
demo = gr.ChatInterface(
    fn=chat_response,
    title="🚗 Egyptian Car Market AI Assistant",
    description="""
    **Welcome to your AI-powered car advisor for the Egyptian automotive market!**

    I have access to detailed information about **900+ new cars** in Egypt with comprehensive specs, prices, and features.

    Ask me about:
    • Cars within your budget (in EGP)
    • Specific features (automatic transmission, ESP, sunroof, etc.)
    • Body types (sedan, hatchback, crossover/SUV)
    • Brand preferences or exclusions (e.g., "non-Chinese cars")
    • Car reliability, comparisons, and reviews

    Try the example prompts below or ask your own questions!
    """,
    examples=[
        "What's the cheapest car under 1 million EGP?",
        "Show me non-Chinese crossovers with automatic transmission and ESP",
        "I want a sedan between 1.5 and 2.5 million EGP",
        "Is the Toyota Corolla reliable?",
        "Compare Honda Civic vs Hyundai Elantra",
        "What's the cheapest electric car with at least 400km range?",
        "Show me German cars with sunroof under 3 million EGP"
    ],
    theme=gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
    ),
    chatbot=gr.Chatbot(
        height=500,
        show_copy_button=True,
        avatar_images=(None, "🚗"),  # User: default, Bot: car emoji
        type="messages",  # Use modern messages format instead of deprecated tuples
    ),
)

# Launch the interface
if __name__ == "__main__":
    demo.launch(
        share=False,  # Set to True to create a public link
        server_name="0.0.0.0",  # Allow external access
        server_port=7860,
        show_error=True,
        inbrowser=True,  # Automatically open in browser
    )
