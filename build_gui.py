import os
import sys
import PyInstaller.__main__
from pathlib import Path
import customtkinter

def build():
    print("Building GUI application with PyInstaller...")
    
    # Get the customtkinter directory to include its assets (themes, etc.)
    ctk_dir = Path(customtkinter.__file__).parent
    
    PyInstaller.__main__.run([
        'run_gui.py',
        '--name=TtsSrtGenerator',
        '--windowed', # No console window
        '--noconfirm', # Overwrite existing build
        '--clean',
        f'--add-data={ctk_dir};customtkinter/', # Include customtkinter data
        '--collect-all=customtkinter',
        # Optional: add an icon if you have one
        # '--icon=assets/icon.ico',
        
        # Add hidden imports if any engines or plugins are dynamically loaded
        '--hidden-import=src.engines.edge',
        '--hidden-import=src.engines.kokoro',
    ])
    
    print("\nBuild complete! You can find the executable in the 'dist' directory.")

if __name__ == "__main__":
    build()
