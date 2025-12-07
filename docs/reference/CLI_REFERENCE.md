# CLI Reference

Complete command-line interface documentation.

## Global Options

```bash
python main.py [OPTIONS] COMMAND [ARGS]
```

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable verbose/debug output |
| `--help` | Show help message |

## Commands

### generate

Generate audio and subtitles from a conversation script.

```bash
python main.py generate [OPTIONS] SCRIPT
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `SCRIPT` | Path to the JSON script file (required) |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output PATH` | Output directory | `output/` |
| `-e, --engine [edge\|kokoro]` | TTS engine to use | From config or `edge` |
| `-c, --config PATH` | Configuration file path | None |
| `-f, --format [mp3\|wav]` | Output audio format | `mp3` |

**Examples:**

```bash
# Basic usage
python main.py generate script.json -o output/

# Use Kokoro engine with WAV output
python main.py generate script.json --engine kokoro --format wav -o output/

# Use custom configuration
python main.py generate script.json -c config/production.yaml -o output/

# Verbose output
python main.py -v generate script.json -o output/
```

**Output:**

On success:
```
Using engine: edge
Output format: mp3
Output directory: output/

  [1/5] Line 1: 2500ms
  [2/5] Line 2: 1800ms
  ...

Generation successful!
  Audio: output/lesson_001.mp3
  SRT: output/lesson_001.srt
  Timeline: output/lesson_001_timeline.json
  Duration: 15000ms (15.0s)
```

---

### validate

Validate a conversation script without generating audio.

```bash
python main.py validate SCRIPT
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `SCRIPT` | Path to the JSON script file (required) |

**Examples:**

```bash
python main.py validate script.json
```

**Output (valid):**
```
Script is valid!
  Lesson ID: lesson_001
  Title: My Lesson
  Lines: 10
  Language: en
```

**Output (invalid):**
```
Validation failed:
  - lesson_id is required
  - Line 3 (id=3): Duplicate line ID
  - Line 5 (id=5): Invalid emotion 'angry'. Valid: neutral, friendly, cheerful, serious, excited
```

---

### voices

List available voices for a TTS engine.

```bash
python main.py voices [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-e, --engine [edge\|kokoro]` | TTS engine | `edge` |
| `-l, --language TEXT` | Language filter | `en` |

**Examples:**

```bash
# List Edge TTS voices
python main.py voices --engine edge

# List Kokoro voices
python main.py voices --engine kokoro

# Filter by language
python main.py voices --engine edge --language en
```

**Output:**
```
Edge TTS voices:

Speaker ID mappings:
  female_us_1: en-US-AriaNeural
  female_us_2: en-US-JennyNeural
  male_us_1: en-US-GuyNeural
  ...

All available Edge TTS voices (filtered by language):
  en-US-AriaNeural: Female, en-US
  en-US-GuyNeural: Male, en-US
  ...
  ... and 45 more

Total: 65 voices
```

---

### batch

Process all JSON scripts in a directory.

```bash
python main.py batch [OPTIONS] DIRECTORY
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `DIRECTORY` | Directory containing JSON script files (required) |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output PATH` | Output directory | `output/` |
| `-e, --engine [edge\|kokoro]` | TTS engine | `edge` |
| `-c, --config PATH` | Configuration file path | None |

**Examples:**

```bash
# Process all scripts in a directory
python main.py batch scripts/ -o output/

# Use specific engine
python main.py batch scripts/ --engine kokoro -o output/

# Use custom configuration
python main.py batch scripts/ -c config/production.yaml -o output/
```

**Output:**
```
Found 5 scripts to process

Processing: lesson_01.json
  OK - 12500ms
Processing: lesson_02.json
  OK - 8300ms
Processing: lesson_03.json
  FAILED - Invalid speaker 'unknown'
...

Completed: 4 success, 1 failed
```

---

### init-config

Generate a default configuration file.

```bash
python main.py init-config [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output PATH` | Output path for config file | `config/default.yaml` |

**Examples:**

```bash
# Generate default config
python main.py init-config

# Generate at custom path
python main.py init-config -o config/my-config.yaml
```

**Output:**
```
Configuration file created: config/default.yaml
```

---

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Error (validation failed, generation failed, etc.) |

## Environment Variables

Currently, no environment variables are used. All configuration is done via config files or command-line options.

## File Paths

- **Relative paths**: Resolved relative to current working directory
- **Absolute paths**: Used as-is
- **Tilde expansion**: `~` is expanded to home directory (Unix-like systems)

## Logging

Enable verbose logging with `-v`:

```bash
python main.py -v generate script.json -o output/
```

Log format:
```
HH:MM:SS - LEVEL - message
```

## Tips

### Quick Preview

```bash
# Fast check with Edge TTS
python main.py generate script.json -o preview/ --engine edge
```

### Validation First

```bash
# Always validate before batch processing
for f in scripts/*.json; do python main.py validate "$f"; done
```

### Combining Options

```bash
# Full example with all options
python main.py -v generate script.json \
    --engine kokoro \
    --format wav \
    --config config/production.yaml \
    --output output/final/
```
