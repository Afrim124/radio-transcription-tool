# Logging configuration for Radio Transcription Tool
import os
import sys
import logging
from config import RECORDINGS_DIR, LOG_FILE

def setup_logging():
    """Setup simple logging to Recordings+transcriptions directory"""
    try:
        # Find the recordings directory
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        recordings_dir = os.path.join(app_dir, RECORDINGS_DIR)
        os.makedirs(recordings_dir, exist_ok=True)
        
        log_file = os.path.join(recordings_dir, LOG_FILE)
        
        # Configure simple logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # Also show in console when running as script
            ]
        )
        return True
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        return False

def log_recording_start(recording_name):
    """Log the start of a recording"""
    logging.info(f"RECORDING START: {recording_name}")

def log_transcript_info(word_count, char_count):
    """Log transcript information"""
    logging.info(f"TRANSCRIPT: {word_count} words, {char_count} chars")

def log_fallback_info(keybert_available, found_count):
    """Log fallback information"""
    logging.info(f"FALLBACK: KeyBERT={keybert_available}, Found={found_count}")

def log_recording_complete(recording_name, keypoint_count):
    """Log recording completion"""
    logging.info(f"RECORDING COMPLETE: {recording_name} - Found {keypoint_count} keypoints")

def log_results(keypoint_count, word_count, phrase_count):
    """Log final results"""
    logging.info(f"RESULTS: {keypoint_count} keypoints ({word_count} words, {phrase_count} phrases)")

def log_success():
    """Log successful completion"""
    logging.info("SUCCESS: Adequate keypoints found")

def log_error(message):
    """Log error messages"""
    logging.info(f"ERROR: {message}")

def log_debug(message):
    """Log debug messages"""
    logging.info(f"DEBUG: {message}")
