"""Seinfeld - Chatbot using Google Gemini API

This implementation of Seinfeld uses the Google Gemini API to provide chat capabilities
through a Discord bot interface.
"""
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, Content, Part
from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image
from io import BytesIO
import uuid
import datetime

load_dotenv()

GOOGLE_KEY = os.getenv("GOOGLE_KEY")
SEINFELD_TOKEN = os.getenv("SEINFELD_TOKEN")
SEINFELD_CHANNEL_ID = int(os.getenv("SEINFELD_CHANNEL_ID"))

# Create images directory if it doesn't exist
IMAGES_DIR = "./images"
os.makedirs(IMAGES_DIR, exist_ok=True)

# Use separate models for text chat and image generation
chat_model_id = "gemini-2.5-pro-exp-03-25"
image_model_id = "imagen-3.0-generate-002"

# Initialize Google Search tool
google_search_tool = Tool(
    google_search = GoogleSearch()
)

# Validate configuration
print("Environment variable check:")
print(f"SEINFELD_TOKEN present: {bool(SEINFELD_TOKEN)}")
print(f"GOOGLE_KEY present: {bool(GOOGLE_KEY)}")
print(f"SEINFELD_CHANNEL_ID: {SEINFELD_CHANNEL_ID}")

# Initialize Discord bot and Google client
bot = commands.Bot(command_prefix="~", intents=discord.Intents.all())
google_client = genai.Client(api_key=GOOGLE_KEY)


@bot.tree.command(name="clear")
@app_commands.describe(limit="Number of messages to delete (default: 100)")
async def clear(interaction: discord.Interaction, limit: int = 100):
    """Clears messages from the current channel."""
    # Check if the user has the required permissions
    if not interaction.channel.permissions_for(interaction.user).manage_messages:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    # Defer the response to allow for longer processing time
    await interaction.response.defer(ephemeral=True)

    try:
        # Delete messages from the channel
        deleted = await interaction.channel.purge(limit=limit)
        await interaction.followup.send(f"Successfully deleted {len(deleted)} messages.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("I don't have permission to delete messages in this channel.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.followup.send(f"Failed to delete messages: {str(e)}", ephemeral=True)

@bot.tree.command(name="model")
@app_commands.describe(new_model_id="New model ID to use for Gemini API")
async def change_model(interaction: discord.Interaction, new_model_id: str):
    """Changes the Gemini chat model being used."""
    global chat_model_id

    # Check if the user has the required permissions (admin only)
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only administrators can change the model.", ephemeral=True)
        return

    old_model = chat_model_id
    chat_model_id = new_model_id

    await interaction.response.send_message(f"Chat model changed from `{old_model}` to `{new_model_id}`", ephemeral=True)

@bot.tree.command(name="image")
@app_commands.describe(prompt="Description of the image you want to generate")
async def generate_image(interaction: discord.Interaction, prompt: str):
    """Generates an image using Gemini API based on the provided prompt."""
    await interaction.response.defer(thinking=True)

    try:
        image_path = await generate_and_save_image(prompt)
        await interaction.followup.send(f"Generated image based on: {prompt}", file=discord.File(image_path))
    except Exception as e:
        print(f"Error generating image: {e}")
        await interaction.followup.send(file=discord.File(os.path.join(IMAGES_DIR, "no.jpg")))

@bot.event
async def on_ready():
    """Called when the client is done preparing data received from Discord."""
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_message(message):
    """Handle incoming messages and respond to queries in the target channel."""
    # Always process commands first
    await bot.process_commands(message)

    if message.channel.id == SEINFELD_CHANNEL_ID:
        if message.author == bot.user:
            return
        if message.content.startswith('!') or message.content.startswith('~'):
            return
        if message.content.strip() == "":
            return

        query = message.content

        # Check if this is an image generation request
        if query.lower().startswith("generate image:") or query.lower().startswith("create image:"):
            async with message.channel.typing():
                prompt = query.split(":", 1)[1].strip()
                try:
                    image_path = await generate_and_save_image(prompt)
                    await message.reply(f"Here's your image:", file=discord.File(image_path))
                except Exception as e:
                    print(f"Error generating image: {e}")
                    await message.reply(file=discord.File(os.path.join(IMAGES_DIR, "no.jpg")))
            return

        previous_messages = [msg async for msg in message.channel.history(limit=15)]
        previous_messages.reverse()  # Chronological order

        # Format history for Gemini API
        formatted_history = []
        for msg in previous_messages:
            if msg.author == bot.user:
                role = "model"
            else:
                role = "user"

            formatted_history.append(
                Content(
                    role=role,
                    parts=[Part(text=msg.content)]
                )
            )

        # Ensure history starts with a user message
        if not formatted_history or formatted_history[0].role != "user":
            # If no history or first message is not from a user,
            # we don't send any history to the API
            formatted_history = []

        try:
            chat = google_client.chats.create(
                model=chat_model_id,
                history=formatted_history,
                config=GenerateContentConfig(
                    system_instruction=(
                        """You are now acting as Jerry Seinfeld. You are not an impersonator; you *are* Jerry Seinfeld.
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
                    ),
                    tools=[google_search_tool],
                    response_modalities=["TEXT"]
                )
            )

            async with message.channel.typing():
                try:
                    response = chat.send_message(query)
                    response_content = response.text
                    await send_sectioned_response(message, response_content)
                except Exception as e:
                    print(f"Error generating response: {e}")
                    await message.reply("I'm sorry, I encountered an error while generating a response.")
        except ValueError as e:
            print(f"Error with chat history: {e}")
            # Try again with no history
            chat = google_client.chats.create(
                model=chat_model_id,
                config=GenerateContentConfig(
                    tools=[google_search_tool],
                    response_modalities=["TEXT"]
                )
            )
            async with message.channel.typing():
                try:
                    response = chat.send_message(query)
                    response_content = response.text
                    await send_sectioned_response(message, response_content)
                except Exception as e:
                    print(f"Error generating response (retry): {e}")
                    await message.reply("I'm sorry, I encountered an error while generating a response.")

async def generate_and_save_image(prompt):
    """Generate an image using Gemini API and save it to the images directory.

    Args:
        prompt (str): The text description of the image to generate

    Returns:
        str: The file path of the saved image

    Raises:
        Exception: If no image was generated or an error occurred
    """
    try:
        response = google_client.models.generate_images(
            model=image_model_id,
            prompt=prompt,
            config=genai.types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9"
            )
        )

        # Create a unique filename with timestamp and UUID
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}.png"
        image_path = os.path.join(IMAGES_DIR, filename)

        # Save the image
        for generated_image in response.generated_images:
            image = Image.open(BytesIO(generated_image.image.image_bytes))
            image.save(image_path)
            return image_path

        # If we get here, no images were generated
        print("ERROR: No images were generated in the response")
        print(f"Full API response: {response}")
        print(f"Response object details: {dir(response)}")
        raise Exception("No image was generated in the response")
    except Exception as e:
        print(f"Exception in image generation: {type(e).__name__}: {str(e)}")
        if "'NoneType' object is not iterable" in str(e):
            print(f"Full API response that caused NoneType error: {response}")
            print(f"Response object details: {dir(response)}")
        if hasattr(e, 'response'):
            print(f"Response in exception: {e.response}")
        raise

async def send_sectioned_response(message, response_content, max_length=1500):
    """Split and send a response in sections if it exceeds Discord's message length limit.

    Args:
        message (discord.Message): The original message to reply to
        response_content (str): The content to send
        max_length (int, optional): Maximum length per message. Defaults to 1999.
    """
    # Split on double newlines to preserve formatting
    sections = response_content.split('\n\n')
    current_section = ""

    for i, section in enumerate(sections):
        # If adding this section would exceed the limit
        if len(current_section) + len(section) + 2 > max_length:
            if current_section:
                try:
                    await message.reply(current_section.strip())
                except Exception as e:
                    print(f"Error sending section: {e}")
            current_section = section
        else:
            if current_section:
                current_section += "\n\n" + section
            else:
                current_section = section

    if current_section:
        try:
            await message.reply(current_section.strip())
        except Exception as e:
            print(f"Error sending final section: {e}")

def main():
    """Initialize and run the Discord bot for Seinfeld."""
    print("Starting Seinfeld with Gemini...")

    try:
        # Run the Discord bot
        bot.run(SEINFELD_TOKEN)
    except KeyboardInterrupt:
        print("Stopping bot due to keyboard interrupt...")
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__":
    main()
