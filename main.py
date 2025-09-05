# Radio Transcription Tool v3.7 - Powered by Bluvia (Dutch Language & Music Filtering)
# 
# To make this script an executable, run:
#   pyinstaller Radio_transcription_tool_Bluvia_v3.7_Optimized.spec
# (Make sure ffmpeg.exe and ffplay.exe are in the bin/ subdirectory)
#
# This will create a professional executable with:
# - Bluvia branding and logo
# - Professional icon (Bluebird app icon 2a.ico)
# - Enhanced GUI with menu system
# - Help and About dialogs
# - All Bluvia images included
# - Optimized build with size reduction (excludes heavy ML packages)
# - Dutch language optimization for radio recordings
# - Music transcription filtering
#
# The executable will be named "Radio_transcription_tool_Bluvia_v3.7_Optimized.exe"

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import math
import openai
from datetime import datetime

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import our modules
from config import VERSION
from logging_config import setup_logging
from utils import load_openai_api_key
from gui import RadioRecorderApp

# Import pydub for audio processing
try:
    from pydub import AudioSegment
except ImportError:
    print("pydub not available")

# Import KeyBERT for keyword extraction
try:
    from keybert import KeyBERT
    keybert_available = True
    print("KeyBERT successfully imported in main.py")
except ImportError as e:
    keybert_available = False
    print(f"KeyBERT import failed in main.py: {e}")
except Exception as e:
    keybert_available = False
    print(f"KeyBERT import error in main.py: {e}")

# Configure pydub to use ffmpeg from bin directory
bin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
ffmpeg_path = os.path.join(bin_dir, 'ffmpeg.exe')
if os.path.exists(ffmpeg_path):
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
else:
    AudioSegment.converter = "ffmpeg"
    AudioSegment.ffmpeg = "ffmpeg"

def main():
    """Main entry point for the Radio Transcription Tool"""
    # Setup logging
    setup_logging()
    
    # Load OpenAI API key (will be checked again in GUI)
    api_key = load_openai_api_key()
    if not api_key:
        print("DEBUG: OpenAI API key not found. User will be prompted in the application.")
    
    # Create and run the main application
    root = tk.Tk()
    app = RadioRecorderApp(root)
    
    # Center the window
    app.center_window()
    
    # Start the main event loop
    root.mainloop()

if __name__ == "__main__":
    main()
