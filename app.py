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
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate")) as demo:
    # --- CSS (keep inside your Blocks, before the header) ---
    gr.HTML("""
    <style>
      /* Shared width so header, logo and chat line up */
      #app-container { max-width: 1200px; margin: 0 auto; }

      /* 20% larger logo */
      :root { --logo-size:120px; }

      /* Header: [spacer] [centered title] [logo] */
      #app-header {
          display: flex;
          align-items: flex-start;
          gap: 16px;
          padding: 0 12px;
          margin-top: -13px;
          margin-bottom: 0;       /* remove bottom gap below title */
      }
      #app-header .spacer { width: var(--logo-size); }

      #app-title { flex: 1; text-align: center; }
      #app-title h1 { margin: 0; font-weight: 800; }

      #app-logo img {
          height: var(--logo-size);
          width: var(--logo-size);
          object-fit: contain;
          display: block;
      }

      /* Description: left-aligned and moved up */
      #app-desc-md {
          text-align: left;
          padding: 0 0 0 12px;
          max-width: 1100px;        /*I increased make line longer*/
          margin-left: 0;
          margin-top: -90px;       /* more negative pull description closer to title */
      }

      /* Remove all top margins from inner markdown elements */
      #app-desc-md .prose,
      #app-desc-md.prose,
      #app-desc-md > *:first-child,
      #app-desc-md p:first-child {
          margin-top: 0 !important;
      }

      @media (max-width: 640px) {
          :root { --logo-size: 70px; }
          #app-desc-md { padding-left: 8px; margin-top: -10px; }
      }
    </style>
    """)

    with gr.Column(elem_id="app-container"):
        gr.HTML(
            f"""
            <div id="app-header">
              <div class="spacer" aria-hidden="true"></div>
              <div id="app-title">
                <h1>🚗 Egyptian Car Market AI Assistant</h1>
              </div>
              <div id="app-logo">
                <img src="{_data_uri(logo_path)}" alt="Logo" />
              </div>
            </div>
            """,
            container=False,
        )

        # Description rendered as Markdown, now anchored left
        gr.Markdown(greeting, elem_id="app-desc-md", container=False)

        # Chat area – keep your existing config; title/description stay None here
        gr.ChatInterface(
            fn=chat_response,
            title=None,
            description=None,
            cache_examples=False,
            chatbot=gr.Chatbot(height="60vh", show_copy_button=True, type="messages"),
            examples=[
                "What is the most affordable non chinese sedan with automatic transmission?",
                "I want a japanese crossover under 2 million LE",
                "Should I buy a Corolla or an Elantra?",
                "What is the most affordable crossover with sunroof?",
                "What is the cheapest 7 seater in Egypt?",
                "Suggest an electric car with at least 500 km range under 2,000,000 EGP"
            ],
        )

# Launch the interface
if __name__ == "__main__":
    demo.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        inbrowser=True,
    )
