# AI Interview Assistant

Real-time voice transcription app that answers programming and technical interview questions using AI.

## Features

- Live audio transcription via AssemblyAI
- AI-powered responses for programming/technical questions using Gemini
- Clean GUI with separate transcription and response areas
- Freeze/unfreeze AI responses
- Markdown and code block formatting

## Requirements

- Python 3.8+
- AssemblyAI API key
- Google Gemini API key
- Audio input device

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set environment variables:

```bash
export ASSEMBLYAI_API_KEY="your_assemblyai_key"
export GOOGLE_API_KEY="your_gemini_key"
```

Update `DEVICE_ID` in `record_and_transcribe.py` to match your audio device.

## Usage

```bash
python record_and_transcribe.py
```

The app will:
1. List available audio devices
2. Verify the selected device
3. Launch the GUI

### Controls

- **Start Recording** - Begin capturing audio
- **Stop Recording** - Stop audio capture
- **Clear** - Clear all text areas
- **Freeze AI** - Pause/resume AI responses

## Project Structure

```
├── record_and_transcribe.py  # Main application
├── ui_components.py          # GUI components
├── audio_handler.py          # Audio streaming
├── ai_handler.py             # AI processing
├── utils.py                  # Device utilities
└── requirements.txt          # Dependencies
```

## How It Works

1. Audio is captured from the selected device
2. AssemblyAI transcribes speech in real-time
3. Gemini classifies if the question is technical/programming-related
4. If relevant, Gemini provides a detailed answer
5. Responses are formatted and displayed in the GUI
