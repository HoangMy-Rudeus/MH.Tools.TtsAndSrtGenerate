# Setup Guide

Complete guide to set up and run TTS & SRT Generator on your system.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Steps](#installation-steps)
3. [GPU Setup (Recommended)](#gpu-setup-recommended)
4. [Voice Sample Preparation](#voice-sample-preparation)
5. [Configuration](#configuration)
6. [Verify Installation](#verify-installation)
7. [Run Your First Generation](#run-your-first-generation)
8. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10/11, Linux (Ubuntu 20.04+), macOS 12+ |
| **Python** | 3.10 or higher |
| **RAM** | 8 GB minimum, 16 GB recommended |
| **Storage** | 10 GB free space (for models) |
| **CPU** | 4+ cores recommended |

### For GPU Acceleration (Recommended)

| Component | Requirement |
|-----------|-------------|
| **GPU** | NVIDIA with CUDA support |
| **VRAM** | 4 GB minimum, 6 GB+ recommended |
| **CUDA** | 11.8 or 12.x |
| **cuDNN** | 8.x |

### Software Dependencies

| Software | Purpose | Required |
|----------|---------|----------|
| **Python 3.10+** | Runtime | Yes |
| **FFmpeg** | Audio encoding | Yes |
| **Git** | Clone repository | Yes |
| **CUDA Toolkit** | GPU acceleration | Optional |

---

## Installation Steps

### Step 1: Install Prerequisites

#### Windows

```powershell
# Install Python 3.10+ from python.org
# Download from: https://www.python.org/downloads/

# Install FFmpeg using winget
winget install FFmpeg

# Or download from: https://ffmpeg.org/download.html
# Add to PATH: C:\ffmpeg\bin

# Verify installations
python --version   # Should be 3.10+
ffmpeg -version    # Should show FFmpeg version
```

#### Linux (Ubuntu/Debian)

```bash
# Update packages
sudo apt update

# Install default Python 3 with venv and pip
sudo apt install python3 python3-venv python3-pip

# Install FFmpeg
sudo apt install ffmpeg

# Install audio libraries
sudo apt install libsndfile1 portaudio19-dev

# Verify
python3 --version
ffmpeg -version
```

#### macOS

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install FFmpeg
brew install ffmpeg

# Verify
python3 --version
ffmpeg -version
```

### Step 2: Clone the Repository

```bash
# Clone the project
git clone https://github.com/your-org/TtsAndSrtGenerate.git
cd TtsAndSrtGenerate
```

### Step 3: Create Virtual Environment

#### Windows (PowerShell)

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

#### Windows (Command Prompt)

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

**You should see `(venv)` in your terminal prompt.**

### Step 4: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

This will install:
- `TTS` (Coqui TTS with XTTS v2)
- `torch` (PyTorch)
- `pydub` (Audio processing)
- `openai-whisper` (Alignment)
- `pydantic` (Data validation)
- Other utilities

**Note**: First run will download XTTS v2 model (~2GB).

---

## GPU Setup (Recommended)

GPU acceleration makes synthesis 5-10x faster.

### GPU Support Overview

| GPU Brand | Technology | OS Support | Status |
|-----------|------------|------------|--------|
| **NVIDIA** | CUDA | Windows, Linux, macOS | Full support |
| **AMD** | ROCm | Linux only | Partial support |
| **Intel** | OneAPI | Linux, Windows | Experimental |
| **Apple Silicon** | MPS | macOS | Supported |

---

### Option A: NVIDIA GPU (CUDA)

#### Check if CUDA is Available

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

#### Install CUDA (if not available)

#### Windows

1. **Check your GPU**: Open Device Manager → Display Adapters
2. **Download CUDA Toolkit**: https://developer.nvidia.com/cuda-downloads
3. **Install cuDNN**: https://developer.nvidia.com/cudnn (requires NVIDIA account)
4. **Restart** your computer

#### Linux

```bash
# Ubuntu 22.04 example
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install cuda-toolkit-12-1

# Add to PATH (add to ~/.bashrc)
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

### Install PyTorch with CUDA

```bash
# Uninstall CPU-only PyTorch
pip uninstall torch torchaudio

# Install CUDA version (check your CUDA version first)
# For CUDA 11.8:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Verify GPU Setup

```bash
python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
"
```

Expected output (with GPU):
```
PyTorch version: 2.1.0+cu118
CUDA available: True
CUDA version: 11.8
GPU: NVIDIA GeForce RTX 3080
VRAM: 10.0 GB
```

---

### Option B: AMD GPU (ROCm) - Linux Only

> **Important**: ROCm only works on Linux. Windows AMD GPU users should use CPU mode.

#### Supported AMD GPUs

| Series | Support |
|--------|---------|
| RX 7000 (RDNA 3) | ROCm 5.7+ |
| RX 6000 (RDNA 2) | ROCm 5.2+ |
| RX 5000 (RDNA 1) | Limited |
| Older GPUs | Not supported |

#### Step 1: Install ROCm (Linux)

```bash
# Ubuntu 22.04 example
# Check: https://rocm.docs.amd.com for latest instructions

# Add ROCm repository
wget https://repo.radeon.com/amdgpu-install/6.0/ubuntu/jammy/amdgpu-install_6.0.60000-1_all.deb
sudo apt install ./amdgpu-install_6.0.60000-1_all.deb
sudo amdgpu-install --usecase=rocm

# Add user to groups
sudo usermod -aG video $USER
sudo usermod -aG render $USER

# Reboot required
sudo reboot
```

#### Step 2: Verify ROCm Installation

```bash
# Check ROCm installation
rocm-smi

# Should show your AMD GPU
```

#### Step 3: Install PyTorch with ROCm

```bash
# Uninstall existing PyTorch
pip uninstall torch torchaudio torchvision

# Install ROCm version of PyTorch
# For ROCm 5.7:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/rocm5.7

# For ROCm 6.0:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/rocm6.0
```

#### Step 4: Verify AMD GPU Setup

```bash
python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'ROCm available: {torch.cuda.is_available()}')  # Returns True for ROCm too
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
"
```

#### Step 5: Update Configuration

```yaml
# config/default.yaml
tts:
  device: "cuda"  # ROCm uses "cuda" device string too
```

#### AMD GPU Troubleshooting

**"No GPU detected" on ROCm**:
```bash
# Check if GPU is recognized
rocm-smi
lspci | grep -i amd

# Set environment variable
export HSA_OVERRIDE_GFX_VERSION=10.3.0  # Adjust for your GPU
```

**Performance issues**:
- ROCm may be slower than CUDA for some operations
- Consider using CPU mode if ROCm is unstable

---

### Option C: AMD GPU on Windows - Use CPU Mode

> **AMD GPUs on Windows do not have PyTorch support.** Use CPU mode instead.

```yaml
# config/default.yaml
tts:
  device: "cpu"
```

**Alternative for Windows AMD users**:
1. Use **DirectML** (experimental, limited TTS support)
2. Use **WSL2 with Linux** (ROCm may work)
3. Use **CPU mode** (recommended for stability)

#### WSL2 Option for Windows AMD Users

```powershell
# Enable WSL2
wsl --install -d Ubuntu-22.04

# Inside WSL2, follow Linux ROCm setup
# Note: ROCm in WSL2 has limited support
```

---

### Option D: Apple Silicon (M1/M2/M3)

macOS with Apple Silicon uses **MPS** (Metal Performance Shaders).

#### Verify MPS Support

```bash
python -c "
import torch
print(f'MPS available: {torch.backends.mps.is_available()}')
print(f'MPS built: {torch.backends.mps.is_built()}')
"
```

#### Update Configuration for MPS

```yaml
# config/default.yaml
tts:
  device: "mps"  # Use Metal Performance Shaders
```

> **Note**: Some TTS operations may fall back to CPU on MPS.

---

### Option E: CPU Only (All Platforms)

If GPU setup is problematic, CPU mode always works.

```yaml
# config/default.yaml
tts:
  device: "cpu"
```

**CPU Performance Tips**:
- Expect 5-10x slower than GPU
- Works reliably on all systems
- Good for testing and small batches

---

## Voice Sample Preparation

### Create Voice Directory

```bash
mkdir -p voices
```

### Record or Obtain Voice Samples

**Requirements for voice samples:**

| Attribute | Requirement |
|-----------|-------------|
| **Duration** | 6-12 seconds |
| **Format** | WAV |
| **Channels** | Mono (1 channel) |
| **Sample Rate** | 22050 Hz or 24000 Hz |
| **Bit Depth** | 16-bit |
| **Quality** | Clear, no background noise |

### Recording Tips

1. **Environment**: Quiet room, no echo
2. **Microphone**: Any decent USB mic or headset
3. **Content**: Read naturally, varied sentences
4. **Software**: Audacity (free), Adobe Audition, etc.

### Convert Audio to Correct Format

Using FFmpeg:

```bash
# Convert any audio to correct format
ffmpeg -i input_audio.mp3 -ar 24000 -ac 1 -acodec pcm_s16le voices/male_us_1.wav

# Options explained:
# -ar 24000   : Sample rate 24kHz
# -ac 1       : Mono (1 channel)
# -acodec pcm_s16le : 16-bit PCM WAV
```

### Sample Voice Files

For testing, you can use free voice samples:

```bash
# Download sample voices (example URLs - replace with actual sources)
# Or record your own 10-second clips

# Place in voices directory:
# voices/male_us_1.wav
# voices/female_us_1.wav
```

### Verify Voices

```bash
python main.py list-voices
```

Expected output:
```
Available voices:
  - male_us_1: voices/male_us_1.wav
  - female_us_1: voices/female_us_1.wav
```

---

## Configuration

### Default Configuration

The default config is at `config/default.yaml`:

```yaml
tts:
  model: "xtts_v2"
  device: "cuda"        # Change to "cpu" if no GPU

audio:
  sample_rate: 24000
  output_format: "mp3"
  mp3_bitrate: 192
  normalization_target: -16

synthesis:
  temperature: 0.7
  default_pause_ms: 400
  initial_silence_ms: 300

alignment:
  enabled: true
  drift_threshold_ms: 200

voices:
  directory: "./voices"
```

### Configuration for CPU-Only Systems

Edit `config/default.yaml`:

```yaml
tts:
  model: "xtts_v2"
  device: "cpu"          # Changed from "cuda"

# Optionally disable alignment for faster processing
alignment:
  enabled: false
```

### Create Custom Configuration

```bash
# Copy default config
cp config/default.yaml config/my_config.yaml

# Edit as needed
# Use with: python main.py generate script.json -c config/my_config.yaml
```

---

## Verify Installation

### Run Verification Script

Create a test script to verify everything works:

```bash
python -c "
print('Checking installation...')

# Check Python version
import sys
print(f'Python: {sys.version}')
assert sys.version_info >= (3, 10), 'Python 3.10+ required'

# Check PyTorch
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')

# Check TTS
from TTS.api import TTS
print('TTS: OK')

# Check Whisper
import whisper
print('Whisper: OK')

# Check pydub
from pydub import AudioSegment
print('pydub: OK')

# Check pydantic
import pydantic
print(f'Pydantic: {pydantic.__version__}')

# Check project modules
from src.models.config import AppConfig
from src.pipeline.lesson_pipeline import LessonPipeline
print('Project modules: OK')

print()
print('All checks passed!')
"
```

### Expected Output

```
Checking installation...
Python: 3.11.5 (main, Sep 11 2023, 13:54:46)
PyTorch: 2.1.0+cu118
CUDA available: True
TTS: OK
Whisper: OK
pydub: OK
Pydantic: 2.5.0
Project modules: OK

All checks passed!
```

---

## Run Your First Generation

### Step 1: Check Sample Script

View the example script:

```bash
cat examples/sample_script.json
```

### Step 2: Validate Script

```bash
python main.py validate examples/sample_script.json
```

Expected output:
```
Validation passed!
```

Or with warnings:
```
Validation passed!

Warnings:
  - speaker (line 1): Speaker 'male_us_1' not found in voice registry
```

### Step 3: Generate Audio

```bash
# Create output directory
mkdir -p output

# Generate lesson
python main.py generate examples/sample_script.json -o ./output -v
```

**First run will download the XTTS v2 model (~2GB). This takes a few minutes.**

### Step 4: Check Output

```bash
# List generated files
ls -la output/

# Expected files:
# coffee_shop_001.mp3   - Audio file
# coffee_shop_001.srt   - Subtitles
# coffee_shop_001.json  - Timeline data
```

### Step 5: Play the Audio

```bash
# Windows
start output/coffee_shop_001.mp3

# macOS
open output/coffee_shop_001.mp3

# Linux
xdg-open output/coffee_shop_001.mp3
# or
ffplay output/coffee_shop_001.mp3
```

---

## Troubleshooting

### Issue: "No module named 'TTS'"

**Cause**: TTS package not installed correctly.

**Solution**:
```bash
pip uninstall TTS
pip install TTS --no-cache-dir
```

### Issue: "CUDA out of memory"

**Cause**: GPU doesn't have enough VRAM.

**Solutions**:

1. Use CPU mode:
```yaml
# config/default.yaml
tts:
  device: "cpu"
```

2. Close other GPU applications

3. Use smaller batch sizes (process fewer lines)

### Issue: "FFmpeg not found"

**Cause**: FFmpeg not in system PATH.

**Windows Solution**:
```powershell
# Add FFmpeg to PATH
$env:PATH += ";C:\ffmpeg\bin"

# Or permanently via System Properties > Environment Variables
```

**Linux Solution**:
```bash
sudo apt install ffmpeg
```

### Issue: "Voice not found in registry"

**Cause**: Voice WAV file missing or wrong location.

**Solution**:
```bash
# Check voices directory
ls voices/

# Should show .wav files
# File names become voice IDs:
# voices/male_us_1.wav -> speaker: "male_us_1"
```

### Issue: "Model download fails"

**Cause**: Network issues or disk space.

**Solution**:
```bash
# Clear cache and retry
rm -rf ~/.cache/huggingface/
rm -rf ~/.local/share/tts/

# Ensure enough disk space (need ~5GB)
df -h

# Retry
python main.py generate examples/sample_script.json -o ./output
```

### Issue: "Torch not compiled with CUDA enabled"

**Cause**: CPU-only PyTorch installed.

**Solution**:
```bash
# Uninstall current PyTorch
pip uninstall torch torchaudio torchvision

# Install CUDA version
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Issue: "Permission denied" on Windows

**Cause**: File locked or permission issue.

**Solution**:
```powershell
# Run PowerShell as Administrator
# Or change output directory
python main.py generate script.json -o C:\Users\YourName\output
```

### Issue: Slow generation on CPU

**Expected**: CPU mode is 5-10x slower than GPU.

**Tips**:
- Use shorter scripts for testing
- Disable alignment for previews:
```yaml
alignment:
  enabled: false
```

### Issue: "No voices found"

**Cause**: Empty or missing voices directory.

**Solution**:
```bash
# Create directory
mkdir -p voices

# Add voice samples (6-12 second WAV files)
# Record your own or use sample voice packs

# Verify
python main.py list-voices
```

---

## Quick Start Checklist

```
[ ] Python 3.10+ installed
[ ] FFmpeg installed
[ ] Repository cloned
[ ] Virtual environment created and activated
[ ] Dependencies installed (pip install -r requirements.txt)
[ ] GPU setup (optional but recommended)
[ ] Voice samples added to voices/
[ ] Configuration reviewed
[ ] Verification script passed
[ ] First generation successful
```

---

## Next Steps

After successful setup:

1. **Create Custom Voices**: Record 10-second samples of different speakers
2. **Write Scripts**: Create JSON scripts for your lessons
3. **Tune Settings**: Adjust config for quality vs speed
4. **Batch Processing**: Generate multiple lessons

See the [User Guide](user-guide.md) for detailed usage instructions.
