# AI Interview Assistant

Real-time voice transcription and image-based question answering app for technical interviews using AI.

## Features

### Audio
- Live audio transcription via AssemblyAI
- AI-powered responses for programming/technical questions using Gemini
- Clean GUI with separate transcription and response areas
- Freeze/unfreeze AI responses
- Markdown and code block formatting

### Image
- Monitor GCP Storage bucket for uploaded question images
- Automatic detection and download of PNG files
- AI analysis of MCQ and coding questions
- Smart prompt engineering for different question types

## Requirements

- Python 3.8+
- AssemblyAI API key (for audio mode)
- Google Gemini API key (required for all modes)
- GCP Storage bucket (for image mode)
- Audio input device (for audio mode)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set environment variables:

```bash
# Required for all modes
export GOOGLE_API_KEY="your_gemini_api_key"

# Required for audio mode
export ASSEMBLYAI_API_KEY="your_assemblyai_key"

# Required for image mode
export GCP_BUCKET_NAME="your_bucket_name"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/gcp_key.json"

# Optional: Image check interval (default: 5 seconds)
export CHECK_INTERVAL="5"
```

Update `DEVICE_ID` in `record_and_transcribe.py` to match your audio device (for audio mode).

## Usage

```bash
python app.py
```

### Audio Mode Controls
- **Start Recording** - Begin capturing audio
- **Stop Recording** - Stop audio capture
- **Clear** - Clear all text areas
- **Freeze AI** - Pause/resume AI responses

### Image Mode
1. Upload PNG images to your GCP bucket
2. The system automatically detects new images
3. Gemini analyzes the question (MCQ or coding)
4. **Image is displayed in the UI (combined mode)**
5. Results are printed to console (standalone) or displayed in UI (combined mode)

## Project Structure

```
├── record_and_transcribe.py  # Audio application
├── gcp_bucket_listener.py    # Image monitoring
├── ui_components.py          # GUI components
├── audio_handler.py          # Audio streaming
├── ai_handler.py             # AI processing (audio + image)
├── utils.py                  # Device utilities
├── requirements.txt          # Dependencies
```

## How It Works

### Audio Processing
1. Audio is captured from the selected device
2. AssemblyAI transcribes speech in real-time
3. Gemini classifies if the question is technical/programming-related
4. If relevant, Gemini provides a detailed answer
5. Responses are formatted and displayed in the GUI

### Image Processing
1. GCP bucket is monitored for new PNG files
2. New images are automatically downloaded
3. Gemini Vision API analyzes the image
4. Smart prompting identifies if it's MCQ or coding question
5. For MCQs: Provides correct answer with explanation
6. For coding: Provides solution approach, Python code, and complexity analysis
7. Results are displayed in UI or printed to console

## Image Question Format Support

The system intelligently handles:
- **Multiple Choice Questions (MCQ)**: Identifies correct answer and explains reasoning
- **Coding Questions**: Provides algorithmic approach, Python solution, and complexity analysis
- **Mixed Questions**: Adapts to question format automatically
