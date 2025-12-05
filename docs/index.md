# Documentation Index

Welcome to the TTS & SRT Generator documentation.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Setup Guide](guides/setup.md) | **Start here** - Install and configure the project |
| [User Guide](guides/user-guide.md) | How to use the tool effectively |
| [Configuration Reference](guides/configuration.md) | All configuration options explained |
| [API Reference](api/reference.md) | Technical API documentation |
| [Architecture](architecture.md) | System design and diagrams |
| [Code Explained](guides/code-explained.md) | Deep-dive into how the code works |

---

## Getting Started

### 1. Setup (15-30 minutes)

Follow the [Setup Guide](guides/setup.md) to:
- Install Python and dependencies
- Configure GPU (optional)
- Add voice samples
- Verify installation

### 2. First Generation (5 minutes)

```bash
# Activate virtual environment
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows

# Generate sample lesson
python main.py generate examples/sample_script.json -o ./output

# Check output
ls output/
# coffee_shop_001.mp3  coffee_shop_001.srt  coffee_shop_001.json
```

### 3. Create Your Own Lessons

See the [User Guide](guides/user-guide.md) for:
- Writing scripts
- Recording voice samples
- Customizing output

---

## Documentation Structure

```
docs/
├── index.md                  # This file
├── architecture.md           # System architecture diagrams
├── api/
│   └── reference.md          # Complete API reference
├── guides/
│   ├── setup.md              # Installation & setup
│   ├── user-guide.md         # Usage guide
│   ├── configuration.md      # Config reference
│   └── code-explained.md     # Code walkthroughs
└── plan/
    ├── readme.md             # Original planning
    └── implementation-plan.md
```

---

## By Use Case

### "I want to generate audio lessons"
1. [Setup Guide](guides/setup.md) → Install everything
2. [User Guide](guides/user-guide.md) → Learn the workflow

### "I want to understand the code"
1. [Architecture](architecture.md) → System overview
2. [Code Explained](guides/code-explained.md) → Detailed walkthrough
3. [API Reference](api/reference.md) → Technical details

### "I want to configure the tool"
1. [Configuration Reference](guides/configuration.md) → All options

### "I want to integrate this into my project"
1. [API Reference](api/reference.md) → Classes and methods
2. [Architecture](architecture.md) → Design patterns used

---

## Command Reference

```bash
# Generate audio from script
python main.py generate <script.json> -o <output_dir>

# Validate script without generating
python main.py validate <script.json>

# List available voices
python main.py list-voices

# Show version
python main.py --version

# Show help
python main.py --help
```

---

## Support

- **Issues**: Check [Troubleshooting](guides/setup.md#troubleshooting)
- **Configuration**: See [Configuration Guide](guides/configuration.md)
- **API Questions**: See [API Reference](api/reference.md)
