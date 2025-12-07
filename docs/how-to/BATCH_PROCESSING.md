# Batch Processing

Process multiple scripts at once for efficient workflow.

## Using the Batch Command

### Basic Usage

Process all JSON scripts in a directory:

```bash
python main.py batch scripts/ -o output/
```

### With Options

```bash
python main.py batch scripts/ -o output/ --engine edge -c config/custom.yaml
```

## Organizing Scripts

### Recommended Directory Structure

```
project/
├── scripts/
│   ├── unit_01/
│   │   ├── lesson_01.json
│   │   ├── lesson_02.json
│   │   └── lesson_03.json
│   ├── unit_02/
│   │   ├── lesson_01.json
│   │   └── lesson_02.json
│   └── extras/
│       └── practice.json
├── output/
├── config/
│   └── default.yaml
└── main.py
```

### Processing Subdirectories

The batch command processes only the immediate directory. For subdirectories, use a script:

**Windows (PowerShell):**
```powershell
Get-ChildItem -Path scripts -Recurse -Filter *.json | ForEach-Object {
    python main.py generate $_.FullName -o output/
}
```

**Linux/macOS:**
```bash
find scripts -name "*.json" -exec python main.py generate {} -o output/ \;
```

## Python API for Batch Processing

### Basic Batch Processing

```python
from pathlib import Path
from src.pipeline import Pipeline
from src.models.config import Config

# Initialize pipeline
config = Config()
config.engine = "edge"
pipeline = Pipeline(config=config)

# Process all scripts
scripts_dir = Path("scripts")
output_dir = Path("output")

for script_path in scripts_dir.glob("*.json"):
    print(f"Processing: {script_path.name}")

    result = pipeline.generate(
        script_path=script_path,
        output_dir=output_dir
    )

    if result.success:
        print(f"  OK: {result.duration_ms}ms")
    else:
        print(f"  FAILED: {result.error}")

# Cleanup
pipeline.cleanup()
```

### Parallel Processing

For faster processing with multiple CPU cores:

```python
import concurrent.futures
from pathlib import Path
from src.pipeline import Pipeline
from src.models.config import Config

def process_script(script_path: Path, output_dir: Path) -> dict:
    """Process a single script."""
    # Create a new pipeline for each thread
    config = Config()
    config.engine = "edge"
    pipeline = Pipeline(config=config)

    try:
        result = pipeline.generate(
            script_path=script_path,
            output_dir=output_dir
        )
        return {
            "file": script_path.name,
            "success": result.success,
            "duration_ms": result.duration_ms,
            "error": result.error
        }
    finally:
        pipeline.cleanup()

# Get all scripts
scripts = list(Path("scripts").glob("*.json"))
output_dir = Path("output")

# Process in parallel (max 4 workers)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = {
        executor.submit(process_script, script, output_dir): script
        for script in scripts
    }

    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        status = "OK" if result["success"] else f"FAILED: {result['error']}"
        print(f"{result['file']}: {status}")
```

### Progress Tracking

```python
from pathlib import Path
from src.pipeline import Pipeline
from src.models.config import Config

def process_with_progress(scripts_dir: str, output_dir: str):
    """Process scripts with detailed progress tracking."""
    config = Config()
    pipeline = Pipeline(config=config)

    scripts = list(Path(scripts_dir).glob("*.json"))
    total = len(scripts)

    results = {
        "success": [],
        "failed": []
    }

    for i, script_path in enumerate(scripts, 1):
        print(f"\n[{i}/{total}] Processing: {script_path.name}")

        def on_line_progress(current, total_lines, line_result):
            print(f"  Line {current}/{total_lines}: {line_result.result.duration_ms}ms")

        result = pipeline.generate(
            script_path=script_path,
            output_dir=output_dir,
            on_progress=on_line_progress
        )

        if result.success:
            results["success"].append(script_path.name)
            print(f"  Completed: {result.duration_ms}ms")
        else:
            results["failed"].append((script_path.name, result.error))
            print(f"  Failed: {result.error}")

    # Summary
    print(f"\n{'='*50}")
    print(f"Processed: {total} scripts")
    print(f"Success: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")

    if results["failed"]:
        print("\nFailed scripts:")
        for name, error in results["failed"]:
            print(f"  - {name}: {error}")

    pipeline.cleanup()
    return results

# Run
process_with_progress("scripts", "output")
```

## Batch Processing Workflows

### Development Workflow

1. **Preview Phase**: Quick generation with Edge TTS
```bash
python main.py batch scripts/ -o preview/ --engine edge
```

2. **Review**: Check preview outputs

3. **Final Phase**: High-quality with Kokoro
```bash
python main.py batch scripts/ -o final/ --engine kokoro
```

### Production Workflow

```bash
#!/bin/bash
# production_batch.sh

# Set variables
SCRIPTS_DIR="scripts"
OUTPUT_DIR="output/$(date +%Y%m%d)"
CONFIG="config/production.yaml"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Validate all scripts first
echo "Validating scripts..."
for script in "$SCRIPTS_DIR"/*.json; do
    python main.py validate "$script"
    if [ $? -ne 0 ]; then
        echo "Validation failed for: $script"
        exit 1
    fi
done

# Process all scripts
echo "Processing scripts..."
python main.py batch "$SCRIPTS_DIR" -o "$OUTPUT_DIR" -c "$CONFIG"

# Generate manifest
echo "Generating manifest..."
python -c "
import json
from pathlib import Path

output_dir = Path('$OUTPUT_DIR')
manifest = []

for timeline in output_dir.glob('*_timeline.json'):
    with open(timeline) as f:
        data = json.load(f)
        manifest.append({
            'lesson_id': data['lesson_id'],
            'title': data['title'],
            'duration_ms': data['duration_ms'],
            'audio_file': data['audio_file'],
            'srt_file': data['srt_file']
        })

with open(output_dir / 'manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)
"

echo "Done! Output in: $OUTPUT_DIR"
```

## Error Handling

### Continue on Error

```python
from pathlib import Path
from src.pipeline import Pipeline

pipeline = Pipeline()
scripts = list(Path("scripts").glob("*.json"))

for script in scripts:
    try:
        result = pipeline.generate(script, "output/")
        if not result.success:
            print(f"Warning: {script.name} failed: {result.error}")
    except Exception as e:
        print(f"Error processing {script.name}: {e}")
        continue  # Continue with next script
```

### Retry Failed Scripts

```python
import time
from pathlib import Path
from src.pipeline import Pipeline

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def process_with_retry(pipeline, script_path, output_dir):
    for attempt in range(MAX_RETRIES):
        result = pipeline.generate(script_path, output_dir)

        if result.success:
            return result

        print(f"  Attempt {attempt + 1} failed: {result.error}")

        if attempt < MAX_RETRIES - 1:
            print(f"  Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)

    return result  # Return last failed result

# Usage
pipeline = Pipeline()
for script in Path("scripts").glob("*.json"):
    result = process_with_retry(pipeline, script, "output/")
```

## Performance Tips

1. **Use Edge TTS for large batches**: Faster than local Kokoro
2. **Parallel processing**: Use thread pool for independent scripts
3. **Pre-validate**: Validate all scripts before batch processing
4. **Monitor network**: Edge TTS requires stable internet
5. **Disk space**: Ensure enough space for output files

## Next Steps

- [Configuration](CONFIGURATION.md) - Optimize settings
- [Python API Reference](../reference/API_REFERENCE.md) - Full API docs
- [Architecture](../explanation/ARCHITECTURE.md) - How it works
