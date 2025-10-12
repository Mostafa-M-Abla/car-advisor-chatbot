"""
Gradio Web Interface for Egyptian Car Market AI Chatbot

This script creates a user-friendly web interface for the car chatbot using Gradio.
Users can interact with the chatbot through a modern chat interface with example prompts.
"""

import os
import yaml
import gradio as gr
from chatbot.car_chatbot import CarChatbot

# Determine correct config path
project_root = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(project_root, "chatbot", "chatbot_config.yaml")

# Load configuration to get greeting
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
    greeting = config.get('conversation', {}).get('greeting', 'Welcome!')

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
    description=greeting,
    examples=[
        "What is the most affordable non chinese sedan with automatic transmission?",
        "I want a japanese crossover under 2 million LE",
        "Should I buy a Corolla or an Elantra?",
        "What is the most affordable crossover with sunroof?",
        "What is the cheapest 7 seater in Egypt?",
        "Suggest an electric car with at least 500 km range under 2,000,000 EGP"
    ],
    cache_examples=False,  # Don't cache examples for better performance
    theme=gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
    ),
    chatbot=gr.Chatbot(
        height="60vh",  # Use viewport height for dynamic sizing
        show_copy_button=True,
        #avatar_images=(None, "🚗"),  # User: default, Bot: car emojiclaude.md
        type="messages",  # Use modern messages format instead of deprecated tuples
    ),
    #save_history = True,
    css="""
    /* Make the chat interface responsive and ensure input is always visible */
    .gradio-container {
        max-height: 100vh !important;
        overflow-y: auto !important;
    }

    /* Make chatbot area responsive with viewport height */
    .chatbot {
        height: 60vh !important;
        min-height: 300px !important;
        max-height: 70vh !important;
        overflow-y: auto !important;
    }

    /* Ensure the input box and submit button are always visible - multiple selectors for robustness */
    .input-row,
    [class*="input"],
    form[class*="form"] {
        position: sticky !important;
        bottom: 0 !important;
        background: white !important;
        z-index: 100 !important;
        padding: 10px 0 !important;
    }

    /* Ensure proper layout for the entire chat interface */
    [class*="ChatInterface"] {
        display: flex !important;
        flex-direction: column !important;
        height: 100vh !important;
        max-height: 100vh !important;
    }

    /* Make example buttons larger and arrange in 3 columns */
    .examples {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        grid-auto-rows: 1fr !important;  /* Make all rows same height */
        gap: 12px !important;
        margin-top: 16px !important;
    }
    .examples > button {
        padding: 16px 20px !important;
        font-size: 15px !important;
        line-height: 1.5 !important;
        min-height: 80px !important;
        height: 100% !important;  /* Fill grid cell to match tallest button */
        white-space: normal !important;
        text-align: left !important;
        /* Flexbox for vertical centering */
        display: flex !important;
        align-items: center !important;
        /* Make buttons look clickable */
        border: 2px solid #d1d5db !important;
        border-radius: 8px !important;
        background: #f9fafb !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    }
    .examples > button:hover {
        background: #e0e7ff !important;
        border-color: #6366f1 !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-2px) !important;
    }
    .examples > button:active {
        transform: translateY(0) !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
    }

    /* Tablet breakpoint (768px - 1024px) */
    @media (max-width: 1024px) and (min-width: 769px) {
        .chatbot {
            height: 55vh !important;
            min-height: 280px !important;
        }
        .examples {
            grid-template-columns: repeat(2, 1fr) !important;
        }
        .examples > button {
            font-size: 14px !important;
            padding: 14px 16px !important;
        }
    }

    /* Mobile breakpoint (phones and small tablets) */
    @media (max-width: 768px) {
        .chatbot {
            height: 50vh !important;
            min-height: 250px !important;
        }
        .examples {
            grid-template-columns: 1fr !important;
        }
        .examples > button {
            min-height: 60px !important;
            padding: 12px 16px !important;
        }
    }

    /* Small phone breakpoint (< 600px height) */
    @media (max-height: 600px) {
        .chatbot {
            height: 40vh !important;
            min-height: 200px !important;
        }
        .examples > button {
            min-height: 50px !important;
            padding: 10px 12px !important;
            font-size: 13px !important;
        }
    }

    /* Very small phones (< 400px width) */
    @media (max-width: 400px) {
        .chatbot {
            min-height: 180px !important;
        }
        .examples > button {
            font-size: 12px !important;
            padding: 8px 10px !important;
        }
    }

    /* Hide Gradio footer buttons (Use via API, Built with Gradio, Settings) */
    footer {
        display: none !important;
    }
    .footer {
        display: none !important;
    }
    [class*="footer"] {
        display: none !important;
    }
    """
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
