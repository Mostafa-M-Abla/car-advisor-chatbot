"""
Gradio Web Interface for Egyptian Car Market AI Chatbot

This script creates a user-friendly web interface for the car chatbot using Gradio.
Users can interact with the chatbot through a modern chat interface with example prompts.
"""

import os
import yaml
import gradio as gr
from chatbot.car_chatbot import CarChatbot
import base64, mimetypes

# Determine correct config path
project_root = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(project_root, "chatbot", "chatbot_config.yaml")
logo_path = os.path.join(project_root, "logo.png")

def _data_uri(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if mime is None:
        mime = "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"

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


# Create Gradio interface using Blocks for more control
with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate"),
) as demo:

    # Small CSS + shared container
    gr.HTML("""
    <style>
      #app-container { max-width: 1200px; margin: 0 auto; }
      #app-logo-wrap { display:flex; justify-content:flex-end; padding: 8px 12px 0 12px; }
      #app-logo-wrap img { height: 60px; object-fit: contain; }
      @media (max-width: 640px) { #app-logo-wrap img { height: 44px; } }
    </style>
    """)

    with gr.Column(elem_id="app-container"):
        # Logo (served as data URI so the browser can load it)
        gr.HTML(f"""
        <div id="app-logo-wrap">
          <img src="{_data_uri(logo_path)}" alt="Logo" />
        </div>
        """)

        # Your existing chat (unchanged)
        gr.ChatInterface(
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
            cache_examples=False,
            chatbot=gr.Chatbot(
                height="60vh",
                show_copy_button=True,
                type="messages",
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
