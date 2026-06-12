import os
import sys
from pathlib import Path

# Ensure the current directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.gui.app import TtsGuiApp
from src.tui.config_io import load_config
from src.models.config import Config

def main():
    config_path = "config/default.yaml"
    output_dir = "output"
    
    # Ensure directories exist
    Path("config").mkdir(parents=True, exist_ok=True)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        if Path(config_path).exists():
            cfg = load_config(config_path)
        else:
            cfg = Config()
    except Exception as e:
        print(f"Error loading config: {e}")
        cfg = Config()
        
    app = TtsGuiApp(config=cfg, config_path=config_path, output_dir=output_dir)
    app.mainloop()

if __name__ == "__main__":
    main()
