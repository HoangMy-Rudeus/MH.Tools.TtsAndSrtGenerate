# Documentation

Welcome to the TTS & SRT Generator documentation!

## Overview

**TTS & SRT Generator** is a Python application for converting conversation scripts into synchronized audio and subtitle files, designed for English learning applications. It offers both a **command line** and an interactive **console UI (TUI)**.

> 📘 **New here? Start with the [User Manual](USER_MANUAL.md)** — setup, CLI + console UI usage,
> writing scripts, configuration, and troubleshooting in one place.

## Current capabilities

- TTS engines: **Edge** (cloud, free) and **Kokoro-ONNX** (local).
- Outputs per script: `.mp3`/`.wav`, `.srt`, `_subtitles.json` (seconds-based), `_timeline.json`.
- **Console UI (TUI)** with Queue, Editor, Config, and History (incl. audio replay) screens —
  launch via `python main.py tui`.
- CLI commands: `generate`, `batch`, `validate`, `voices`, `init-config`, `tui`.

## Documentation Structure

This documentation follows the **[Diátaxis framework](https://diataxis.fr/)**, organizing content into four categories based on your needs:

### [Tutorials](tutorials/)

*Step-by-step lessons to get you started*

- [Getting Started](tutorials/GETTING_STARTED.md) - Complete setup walkthrough
- [Quick Start](tutorials/QUICK_START.md) - Fast setup guide
- [Your First Script](tutorials/YOUR_FIRST_SCRIPT.md) - Create your first conversation

**Best for**: New users, onboarding, learning the basics

---

### [How-To Guides](how-to/)

*Practical guides for specific tasks*

- [Installation Guide](how-to/INSTALLATION.md) - Detailed installation options
- [Using the Console UI (TUI)](how-to/USING_THE_TUI.md) - Launch, navigate, and use the TUI
- [Creating Scripts](how-to/CREATING_SCRIPTS.md) - Write conversation scripts
- [Custom Voices](how-to/CUSTOM_VOICES.md) - Configure voice mappings
- [Batch Processing](how-to/BATCH_PROCESSING.md) - Process multiple scripts
- [Configuration](how-to/CONFIGURATION.md) - Customize settings

**Best for**: Solving specific problems, task completion

---

### [Reference](reference/)

*Technical specifications and API documentation*

- [CLI Reference](reference/CLI_REFERENCE.md) - Command line interface
- [API Reference](reference/API_REFERENCE.md) - Python API documentation
- [Script Format](reference/SCRIPT_FORMAT.md) - JSON script specification
- [AI JSON Input Guide](reference/AI_JSON_INPUT.md) - AI-readable input spec (for LLM-generated scripts)
- [Voice Reference](reference/VOICE_REFERENCE.md) - Available voices
- [Configuration Reference](reference/CONFIG_REFERENCE.md) - All settings

**Best for**: Looking up specific information, API integration

---

### [Explanation](explanation/)

*Conceptual guides and design decisions*

- [Architecture Overview](explanation/ARCHITECTURE.md) - System design
- [TTS Engines](explanation/TTS_ENGINES.md) - Engine comparison
- [Audio Pipeline](explanation/AUDIO_PIPELINE.md) - How audio is processed

**Best for**: Understanding design, architectural context

---

## Quick Navigation

### I'm new here
Start with [Getting Started](tutorials/GETTING_STARTED.md)

### I need to solve a specific problem
Check [How-To Guides](how-to/)

### I need API details
See [API Reference](reference/API_REFERENCE.md)

### I want to understand how it works
Read [Architecture Overview](explanation/ARCHITECTURE.md)

---

## Quick Links

- **User Manual**: [USER_MANUAL.md](USER_MANUAL.md)
- **Main README**: [README.md](../README.md)
- **Sample Script**: [topics/conversation_1.json](../topics/conversation_1.json)
- **Default Config**: [config/default.yaml](../config/default.yaml)
