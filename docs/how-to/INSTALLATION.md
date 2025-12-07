# Installation Guide

Detailed installation instructions for different environments and use cases.

## System Requirements

- **Python**: 3.10 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 2GB RAM minimum (4GB recommended for Kokoro local TTS)
- **Disk Space**: 500MB for Edge TTS, 1GB+ for Kokoro TTS (includes model files)
- **Network**: Required for Edge TTS (cloud-based)

## Installing FFmpeg

FFmpeg is required for audio processing. Install it for your operating system:

### Windows

**Option 1: Using Chocolatey (Recommended)**
```bash
choco install ffmpeg
```

**Option 2: Using winget**
```bash
winget install FFmpeg
```

**Option 3: Manual Installation**
1. Download from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your PATH environment variable

### macOS

```bash
brew install ffmpeg
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install ffmpeg
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install ffmpeg
```

### Verify Installation

```bash
ffmpeg -version
```

## Basic Installation (Edge TTS Only)

For cloud-based TTS using Microsoft Edge voices:

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Full Installation (Including Kokoro Local TTS)

For high-quality local TTS:

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
pip install kokoro-onnx
```

### Step 2: Download Kokoro Model Files

```bash
# Create models directory
mkdir models

# Download model files (Windows PowerShell)
Invoke-WebRequest -Uri "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx" -OutFile "models/kokoro-v1.0.onnx"
Invoke-WebRequest -Uri "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin" -OutFile "models/voices-v1.0.bin"

# Download model files (macOS/Linux)
wget -P models https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
wget -P models https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

**Alternative: Download from Hugging Face**
- [kokoro-v1.0.onnx](https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX)
- [voices-v1.0.bin](https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX)

### Step 3: Verify Kokoro Installation

```bash
python main.py voices --engine kokoro
```

## Development Installation

For contributors and developers:

```bash
# Clone repository
git clone <repository-url>
cd TtsAndSrtGenerate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/
```

## Docker Installation

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set entrypoint
ENTRYPOINT ["python", "main.py"]
```

Build and run:

```bash
# Build image
docker build -t tts-generator .

# Run with mounted volumes
docker run -v $(pwd)/scripts:/app/scripts -v $(pwd)/output:/app/output tts-generator generate scripts/lesson.json -o output/
```

## Troubleshooting Installation

### "FFmpeg not found"

**Windows:**
1. Verify FFmpeg is in PATH: `where ffmpeg`
2. Restart your terminal after adding to PATH
3. Try running `ffmpeg` directly

**macOS/Linux:**
1. Verify installation: `which ffmpeg`
2. Check if PATH includes FFmpeg: `echo $PATH`

### "No module named 'edge_tts'"

```bash
pip install edge-tts
```

### "No module named 'kokoro_onnx'"

```bash
pip install kokoro-onnx
```

### "Model file not found" (Kokoro)

Ensure model files are in the correct location:
```
models/
├── kokoro-v1.0.onnx
└── voices-v1.0.bin
```

Or update `config/default.yaml` with correct paths:
```yaml
kokoro:
  model_path: "/path/to/kokoro-v1.0.onnx"
  voices_path: "/path/to/voices-v1.0.bin"
```

### Permission Denied

**Windows:**
Run Command Prompt as Administrator

**macOS/Linux:**
```bash
chmod +x main.py
```

### SSL Certificate Errors (Edge TTS)

```bash
pip install --upgrade certifi
```

## Verifying Installation

Run the verification script:

```bash
# Check CLI
python main.py --help

# Validate sample script
python main.py validate docs/conversation_1.json

# Generate test audio
python main.py generate docs/conversation_1.json -o test_output/

# Check output files
ls test_output/
```

Expected output files:
- `office_intro_003.mp3`
- `office_intro_003.srt`
- `office_intro_003_timeline.json`

## Next Steps

- [Getting Started](../tutorials/GETTING_STARTED.md) - First-time setup
- [Configuration](CONFIGURATION.md) - Customize settings
- [Custom Voices](CUSTOM_VOICES.md) - Set up voice mappings
