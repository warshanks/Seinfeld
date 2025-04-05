# 🎭 Seinfeld Discord Bot

A Discord bot that impersonates Jerry Seinfeld using Google's Gemini API, providing observational humor and image generation capabilities.

## ✨ Features

- 🎙️ **Jerry Seinfeld Chat**: Responds to messages in the signature observational humor style of Jerry Seinfeld
- 🔍 **Web Search Integration**: Uses Google Search to provide up-to-date information in responses
- 🖼️ **Image Generation**: Creates images based on text prompts using Gemini's image API
- 🧹 **Message Management**: Commands to clear conversation history

## 📋 Requirements

- Python 3.8+
- Discord Bot Token
- Google Gemini API Key

## 🚀 Setup

1. Clone this repository:
   ```
   git clone https://github.com/warshanks/Seinfeld.git
   cd Seinfeld
   ```

2. Create and activate a virtual environment (recommended):
   ```
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   GOOGLE_KEY=your_google_gemini_api_key
   SEINFELD_TOKEN=your_discord_bot_token
   SEINFELD_CHANNEL_ID=your_discord_channel_id
   ```

## 📝 Usage

1. Run the bot:
   ```
   python seinfeld.py
   ```

2. Chat with the bot in your designated Discord channel

## 🤖 Commands

- `/clear [limit=100]` - Delete a number of messages from the current channel
- `/model [new_model_id]` - Change the Gemini model being used (admin only)
- `/image [prompt]` - Generate an image based on a text prompt

## 🎨 Image Generation

You can also generate images by starting a message with:
- `generate image: [prompt]`
- `create image: [prompt]`

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
