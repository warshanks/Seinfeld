"""Seinfeld - Chatbot using Google Gemini API

This implementation of Seinfeld uses the Google Gemini API to provide chat capabilities
through a Discord bot interface.
"""
from google import genai
from dotenv import load_dotenv
import os

# Import utility functions from our library
from utils import run_bot, initialize_bot, register_model_command, register_clear_command, register_generic_on_message_handler

load_dotenv()

GOOGLE_KEY = os.getenv("GOOGLE_KEY")
DISCORD_TOKEN = os.getenv("SEINFELD_TOKEN")

SEINFELD_CHANNEL_ID = int(os.getenv("SEINFELD_CHANNEL_ID"))
# Check if additional channel IDs are specified
ADDITIONAL_CHANNELS = os.getenv("SEINFELD_ADDITIONAL_CHANNELS", "")
# Parse additional channel IDs and add to list
TARGET_CHANNEL_IDS = [SEINFELD_CHANNEL_ID]
if ADDITIONAL_CHANNELS:
    ADDITIONAL_IDS = [int(channel_id.strip()) for channel_id in ADDITIONAL_CHANNELS.split(",") if channel_id.strip()]
    TARGET_CHANNEL_IDS.extend(ADDITIONAL_IDS)

# Create images directory if it doesn't exist
IMAGES_DIR = "./images"
os.makedirs(IMAGES_DIR, exist_ok=True)

# Use separate models for text chat and image generation
chat_model_id = "gemini-2.5-pro-exp-03-25"
image_model_id = "imagen-3.0-generate-002"

# Initialize Google client
google_client = genai.Client(api_key=GOOGLE_KEY)

def main():
    """Initialize and run the Discord bot for KC."""
    # Initialize bot and tools
    bot, genai_client, google_search_tool = initialize_bot(
        bot_name="Seinfeld",
        discord_token=DISCORD_TOKEN,
        google_key=GOOGLE_KEY,
        target_channel_id=SEINFELD_CHANNEL_ID,  # Keep for backwards compatibility
        google_client=google_client,
        chat_model_id=chat_model_id,
        image_model_id=image_model_id
    )
        # Register model change command
    register_model_command(bot, globals())

    # Register clear command
    register_clear_command(bot, TARGET_CHANNEL_IDS)

    # Seinfeld-specific system instruction
    system_instruction = """You are now acting as Jerry Seinfeld. You are not an impersonator; you *are* Jerry Seinfeld.
You are giving your observational humor stand-up routine. Your focus is on the absurdity and minutiae of everyday life.
Topics include, but are not limited to: relationships, food, technology, social conventions, and the general frustrations
of living in a modern world.

Your humor is characterized by:

*   **Observation:** Pointing out things that everyone notices but rarely comments on.
*   **Relatability:** Situations and experiences that are common and easily understood.
*   **Sarcasm & Irony:** A dry, understated delivery that highlights the ridiculousness of things.
*   **"What's the deal with..."**: Use this phrase frequently to introduce a new observation.
*   **No Grand Conclusions:** You don't offer solutions or morals; you simply highlight the absurdity.
*   **Emphasis on the Specific:** Focus on very specific, sometimes trivial details.

Avoid:

*   **Political Commentary:** Stay away from overtly political topics.
*   **Offensive or Mean-Spirited Jokes:** Your humor is observational, not mean-spirited.
*   **Explanations of Your Own Humor:** Don't break the fourth wall or analyze your own jokes.

When responding to a prompt, always answer as if you are performing standup. Start with a joke, then elaborate on it."""

    # Register message handler
    register_generic_on_message_handler(
        bot=bot,
        target_channel_ids=TARGET_CHANNEL_IDS,
        google_client=google_client,
        chat_model_id=chat_model_id,
        image_model_id=image_model_id,
        system_instruction=system_instruction,
        google_search_tool=google_search_tool
    )

    # Run the bot
    run_bot(bot, DISCORD_TOKEN, bot_name="Seinfeld")

if __name__ == "__main__":
    main()