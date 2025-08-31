# Radio Transcription Tool v3.5 - Powered by Bluvia (Dutch Language & Music Filtering)
# 
# To make this script an executable, run:
#   pyinstaller Radio_transcription_tool_Bluvia_v3.5_Optimized.spec
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
# The executable will be named "Radio_transcription_tool_Bluvia_v3.5_Optimized.exe"

import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import time
import openai
import logging
from datetime import datetime

# Try to import PIL for image processing (optional)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
try:
    from pydub import AudioSegment
    # Configure pydub to use ffmpeg from bin directory
    bin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin')
    ffmpeg_path = os.path.join(bin_dir, 'ffmpeg.exe')
    if os.path.exists(ffmpeg_path):
        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffmpeg = ffmpeg_path
    else:
        # Fallback to system PATH
        AudioSegment.converter = "ffmpeg"
        AudioSegment.ffmpeg = "ffmpeg"
except ImportError:
    AudioSegment = None
import math
# Make keybert truly optional - only import if explicitly available
keybert_available = False
KeyBERT = None
try:
    from keybert import KeyBERT
    keybert_available = True
except ImportError:
    pass
import sys

# Version information
VERSION = "3.5"

def setup_logging():
    """Setup simple logging to Recordings+transcriptions directory"""
    try:
        # Find the recordings directory
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        recordings_dir = os.path.join(app_dir, "Recordings+transcriptions")
        os.makedirs(recordings_dir, exist_ok=True)
        
        log_file = os.path.join(recordings_dir, "transcription.log")
        
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

# Global stopwords definition - more robust and comprehensive
DUTCH_STOPWORDS = {
    'de', 'het', 'een', 'en', 'van', 'in', 'te', 'dat', 'die', 'is', 'op', 'met', 'als', 'voor', 'aan', 'er', 'door', 'om', 'tot', 'ook', 'maar', 'uit', 'bij', 'over', 'nog', 'naar', 'dan', 'of', 'je', 'ik', 'ze', 'zij', 'hij', 'wij', 'jij', 'u', 'hun', 'ons', 'mijn', 'jouw', 'zijn', 'haar', 'hun', 'dit', 'dat', 'deze', 'die',
    'niet', 'hebben', 'daar', 'heeft', 'eigenlijk', 'heel', 'gaat', 'gaan', 'toch', 'want', 'elkaar', 'even', 'waar', 'natuurlijk', 'veel', 'meer', 'moet', 'kunnen', 'wordt', 'gewoon', 'worden', 'echt', 'komen', 'komt', 'hier', 'niks', 'gevonden',
    'twee', 'drie', 'vier', 'vijf', 'zes', 'zeven', 'acht', 'negen', 'tien', 'goed', 'doen', 'moeten', 'maken', 'soort', 'onze', 'omdat', 'kwam', 'iemand', 'blijven', 'vaak', 'jaar', 'denk', 'weer', 'staat', 'waren', 'geen', 'vandaag', 'bijvoorbeeld', 'zeggen', 'grote', 'tijd', 'muziek', 'iets', 'eigen', 'vooral', 'toen', 'eerste', 'tweede', 'derde', 'vierde', 'vijfde',
    'zesde', 'zevende', 'achtste', 'negende', 'tiende', 'vind', 'laten', 'altijd', 'andere', 'alle', 'woord', 'gebruiken', 'moment', 'woord', 'zelf', 'zien', 'jullie', 'terug', 'kijken', 'hebt', 'weet', 'hele', 'dingen', 'helemaal', 'verschillende', 'inderdaad', 'beter', 'misschien', 'manier', 'dacht', 'uiteindelijk',
    'beetje', 'ging', 'gemaakt', 'vanuit', 'werd', 'vond', 'best', 'alleen', 'groep', 'honderd', 'iedereen', 'weken', 'groot', 'allemaal', 'gedaan', 'lang', 'zeker', 'meter', 'dagen', 'gegeven', 'leuk', 'keer', 'zaten', 'mooi', 'deden', 'willen', 'begint', 'ervoor', 'minder', 'weten', 'onder', 'steeds', 'stellen',
    'anders', 'alles', 'hadden', 'zegt', 'juist', 'oude', 'bent', 'vindt', 'volgend', 'laatste', 'minuten', 'vanaf', 'tegen', 'samen', 'laag', 'zoals', 'tevoren', 'eerder', 'tegen', 'zoals', 'steeds', 'maakt', 'vorig', 'nieuwe', 'ligt', 'jonge', 'staan', 'zich', 'ziet', 'kijk', 'week', 'eens', 'klein',
    'volgende', 'lijkt', 'tussen', 'stuk', 'geworden', 'dus', 'zo', 'snel', 'elke', 'we', 'it', 'have', 'had', 'you', 'ja', 'we', 'ben', 'zo', 'kan', 'wel', 'nou', 'elke', 'waarom', 'denken', 'leren', 'paar', 'soms', 'kan', 'best', 'wat', 'was', 'er', 'wil', 'zeer', 'zeg', 'hem', 'zie', 'heb', 'liever', 'er', 'bijna',
    'heb', 'hebt', 'heeft', 'had', 'hadden', 'zou', 'zouden', 'moet', 'moeten', 'kan', 'kunnen', 'wil', 'willen', 'ga', 'gaan', 'kom', 'komen', 'doe', 'doen', 'maak', 'maken', 'zeg', 'zeggen', 'zie', 'zien', 'weet', 'weten', 'denk', 'denken', 'vind', 'vinden', 'heb', 'hebt', 'heeft', 'had', 'hadden',
    'mij', 'me', 'mijn', 'jou', 'jouw', 'hem', 'zijn', 'haar', 'ons', 'onze', 'jullie', 'hun', 'u', 'uw', 'zij', 'ze', 'hij', 'wij', 'we', 'ik', 'je', 'jij', 'dit', 'dat', 'deze', 'die', 'welke', 'welk', 'wat', 'wie', 'waar', 'wanneer', 'waarom', 'hoe', 'wel', 'niet', 'geen', 'al', 'alle', 'alleen', 'maar', 'ook',
    'toch', 'wel', 'nou', 'hoor', 'zeg', 'kijk', 'zie', 'hè', 'hé'
}

# Music filtering patterns for Dutch radio recordings
MUSIC_FILTER_PATTERNS = {
    'song_titles': [
        'intro', 'outro', 'jingle', 'theme', 'song', 'lied', 'nummer', 'hit', 'single', 'album',
        'artiest', 'zanger', 'zangeres', 'band', 'groep', 'muziek', 'melodie', 'ritme', 'beat',
        'refrein', 'couplet', 'bridge', 'solo', 'instrumentaal', 'acapella', 'karaoke'
    ],
    'music_indicators': [
        'speelt', 'zingt', 'zong', 'gezongen', 'gespeeld', 'muziek', 'melodie', 'ritme',
        'instrumenten', 'gitaar', 'piano', 'drums', 'bas', 'viool', 'trompet', 'saxofoon',
        'orkest', 'koor', 'ensemble', 'concert', 'optreden', 'festival', 'muziekwinkel'
    ],
    'radio_specific': [
        'radio', 'zender', 'frequentie', 'fm', 'am', 'uitzending', 'programma', 'show',
        'dj', 'presentator', 'omroep', 'nederlandse', 'vlaamse', 'belgische', 'hollandse'
    ]
}

def filter_music_transcription(text):
    """
    Filter out music-related transcriptions to focus on speech content.
    Returns filtered text with music segments removed or marked.
    """
    if not text:
        return text
    
    # Convert to lowercase for pattern matching
    text_lower = text.lower()
    
    # Check for music indicators in the text
    music_score = 0
    music_indicators = []
    
    # Score based on music-related words
    for pattern in MUSIC_FILTER_PATTERNS['song_titles']:
        if pattern in text_lower:
            music_score += 2
            music_indicators.append(pattern)
    
    for pattern in MUSIC_FILTER_PATTERNS['music_indicators']:
        if pattern in text_lower:
            music_score += 1
            music_indicators.append(pattern)
    
    # Check for repetitive patterns that suggest music
    words = text.split()
    if len(words) > 10:
        # Check for repetitive word patterns (common in songs)
        word_counts = {}
        for word in words:
            word_lower = word.lower()
            if word_lower not in DUTCH_STOPWORDS and len(word_lower) > 2:
                word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
        
        # If any word appears more than 3 times in a short segment, it might be music
        for word, count in word_counts.items():
            if count > 3 and len(words) < 50:
                music_score += 1
                music_indicators.append(f"repetitive_{word}")
    
    # If music score is high, mark this segment
    if music_score >= 3:
        print(f"DEBUG: Music detected in transcript segment (score: {music_score})")
        print(f"DEBUG: Music indicators: {music_indicators}")
        # Return filtered text with music markers
        return f"[MUSIC_FILTERED] {text}"
    
    return text

def is_whisper_artifact(text):
    """
    Check if a text segment contains Whisper prompt artifacts.
    
    Args:
        text: Text segment to check
    
    Returns:
        True if the text contains Whisper prompt artifacts, False otherwise
    """
    if not text or not isinstance(text, str):
        return False
    
    text_lower = text.lower().strip()
    
    # Check for common Whisper prompt artifacts
    whisper_prompt_indicators = [
        "deze transcriptie moet alle belangrijke woorden en zinnen bevatten",
        "maar muziekteksten en jingles kunnen worden overgeslagen",
        "transcriptie moet alle belangrijke woorden en zinnen bevatten",
        "muziekteksten en jingles kunnen worden overgeslagen",
        "transcriptie",
        "whisper",
        "openai",
        "api",
        "prompt",
        "instruction",
        "alle belangrijke woorden",
        "zinnen bevatten",
        "muziekteksten en jingles",
        "kunnen worden overgeslagen",
        "radio-uitzending",
        "nieuws discussies interviews",
        "focus op spraak",
        "niet op muziek",
        "belangrijke woorden en zinnen",
        "muziekteksten en jingles kunnen worden overgeslagen"
    ]
    
    # Check if any of the indicators are present in the text
    for indicator in whisper_prompt_indicators:
        if indicator in text_lower:
            return True
    
    # Check for suspicious patterns that might indicate artifacts
    suspicious_patterns = [
        "deze transcriptie",
        "transcriptie moet",
        "muziekteksten en jingles",
        "belangrijke woorden",
        "zinnen bevatten",
        "overgeslagen",
        "focus op spraak",
        "niet op muziek",
        "nederlandse radio-uitzending",
        "nieuws discussies interviews",
        "radio-uitzending met nieuws",
        "discussies interviews en gesprekken",
        "focus op spraak en gesprekken",
        "transcriptie moet alle belangrijke",
        "woorden en zinnen bevatten",
        "maar muziekteksten en jingles",
        "kunnen worden overgeslagen"
    ]
    
    for pattern in suspicious_patterns:
        if pattern in text_lower:
            return True
    
    # Check for repeated prompt-like text (common in artifacts)
    words = text_lower.split()
    if len(words) > 3:
        # Check if the same phrase appears multiple times in the text
        text_without_spaces = text_lower.replace(" ", "")
        if len(text_without_spaces) > 20:  # Only check longer texts
            # Look for repeated substrings that might indicate artifacts
            for i in range(len(words) - 2):
                phrase = " ".join(words[i:i+3])
                if len(phrase) > 10 and text_lower.count(phrase) > 1:
                    return True
    
    # Check for excessive repetition of specific words (common in artifacts)
    word_counts = {}
    for word in words:
        if len(word) > 3:  # Only count meaningful words
            word_counts[word] = word_counts.get(word, 0) + 1
            if word_counts[word] > 3:  # If a word appears more than 3 times
                return True
    
    # Check for very long repeated sequences (common in corrupted artifacts)
    if len(text) > 100:
        # Look for sequences that repeat more than twice
        for i in range(len(text) - 20):
            sequence = text[i:i+20]
            if text.count(sequence) > 2:
                return True
    
    return False

def deduplicate_phrases(phrases_with_times):
    """
    Remove duplicate and similar phrases while preserving timestamps.
    
    Args:
        phrases_with_times: List of tuples (phrase, [timestamps])
    
    Returns:
        Deduplicated list with merged timestamps
    """
    if not phrases_with_times:
        return phrases_with_times
    
    # Create a dictionary to merge duplicates and similar phrases
    phrase_dict = {}
    
    for phrase, timestamps in phrases_with_times:
        # Normalize phrase for comparison (remove extra spaces, lowercase)
        normalized_phrase = " ".join(phrase.lower().split())
        
        # Check for exact duplicates first
        if normalized_phrase in phrase_dict:
            # Merge timestamps and keep the longer/original phrase
            existing_phrase, existing_times = phrase_dict[normalized_phrase]
            merged_times = existing_times + timestamps
            
            # Keep the longer phrase if it's more meaningful
            if len(phrase) > len(existing_phrase):
                phrase_dict[normalized_phrase] = (phrase, merged_times)
            else:
                phrase_dict[normalized_phrase] = (existing_phrase, merged_times)
            continue
        
        # Check for similar phrases (one is contained within the other)
        merged = False
        for existing_norm, (existing_phrase, existing_times) in list(phrase_dict.items()):
            # Check if one phrase is contained within the other
            if normalized_phrase in existing_norm or existing_norm in normalized_phrase:
                # Merge timestamps
                merged_times = existing_times + timestamps
                
                # Keep the longer phrase as it's more complete
                if len(phrase) > len(existing_phrase):
                    # Remove the shorter one and add the longer one
                    del phrase_dict[existing_norm]
                    phrase_dict[normalized_phrase] = (phrase, merged_times)
                else:
                    # Update the existing one with merged timestamps
                    phrase_dict[existing_norm] = (existing_phrase, merged_times)
                
                merged = True
                break
        
        # If no similar phrase found, add as new
        if not merged:
            phrase_dict[normalized_phrase] = (phrase, timestamps)
    
    # Convert back to list and sort by phrase length (longer phrases first)
    deduplicated = list(phrase_dict.values())
    deduplicated.sort(key=lambda x: len(x[0]), reverse=True)
    
    return deduplicated

def merge_similar_segments(segments, similarity_threshold=0.7, target_timestamp=None):
    """
    Merge segments that have similar content and the same timestamp.
    This helps eliminate duplicate transcriptions that often occur with Whisper.
    
    Args:
        segments: List of segment dictionaries with 'start', 'end', 'text' keys
        similarity_threshold: Threshold for considering sentences similar (0.0-1.0)
        target_timestamp: Optional specific timestamp to focus on (e.g., 0.0 for start of recording)
    
    Returns:
        List of merged segments
    """
    if not segments or len(segments) <= 1:
        return segments
    
    # If target_timestamp is specified, focus on segments near that timestamp
    if target_timestamp is not None:
        print(f"DEBUG: Focusing on segments near timestamp {target_timestamp}s")
        # Filter segments within 0.5 seconds of target timestamp
        target_segments = []
        for seg in segments:
            if isinstance(seg, dict) and 'start' in seg:
                if abs(seg['start'] - target_timestamp) <= 0.5:
                    target_segments.append(seg)
        
        if target_segments:
            print(f"DEBUG: Found {len(target_segments)} segments near timestamp {target_timestamp}s")
            segments = target_segments
        else:
            print(f"DEBUG: No segments found near timestamp {target_timestamp}s")
            return segments
    else:
        print(f"DEBUG: Processing ALL segments across all timestamps")
    
    # First try to merge segments with similar content regardless of timestamp
    print(f"DEBUG: Looking for similar content across all segments...")
    
    # Create a list of all valid segments, filtering out Whisper prompt artifacts
    valid_segments = []
    whisper_prompt_indicators = [
        "deze transcriptie moet alle belangrijke woorden en zinnen bevatten",
        "maar muziekteksten en jingles kunnen worden overgeslagen",
        "transcriptie moet alle belangrijke woorden en zinnen bevatten",
        "muziekteksten en jingles kunnen worden overgeslagen"
    ]
    
    for seg in segments:
        if isinstance(seg, dict) and 'text' in seg and seg['text'].strip():
            # Check if this segment contains Whisper prompt artifacts
            if not is_whisper_artifact(seg['text']):
                valid_segments.append(seg)
            else:
                print(f"DEBUG: Filtered out Whisper prompt artifact: '{seg['text'][:100]}...'")
    
    print(f"DEBUG: Processing {len(valid_segments)} valid segments for content similarity (filtered out Whisper artifacts)")
    
    # Find and merge similar content segments
    processed_indices = set()
    merged_segments = []
    
    for i, seg1 in enumerate(valid_segments):
        if i in processed_indices:
            continue
        
        # Find similar segments to merge
        similar_segments = [seg1]
        processed_indices.add(i)
        
        for j, seg2 in enumerate(valid_segments[i+1:], i+1):
            if j in processed_indices:
                continue
            
            # Calculate similarity between segments
            similarity = calculate_text_similarity(seg1['text'], seg2['text'])
            
            if similarity >= similarity_threshold:
                print(f"DEBUG: Found similar content (similarity: {similarity:.2f}):")
                print(f"DEBUG:   Text1: '{seg1['text'][:80]}...'")
                print(f"DEBUG:   Text2: '{seg2['text'][:80]}...'")
                similar_segments.append(seg2)
                processed_indices.add(j)
        
        # Merge similar segments
        if len(similar_segments) > 1:
            merged_text = merge_text_segments([seg['text'] for seg in similar_segments])
            # Use the earliest timestamp from the group
            earliest_start = min(seg['start'] for seg in similar_segments)
            latest_end = max(seg['end'] for seg in similar_segments)
            
            merged_segment = {
                'start': earliest_start,
                'end': latest_end,
                'text': merged_text
            }
            merged_segments.append(merged_segment)
            print(f"DEBUG: Merged {len(similar_segments)} similar segments into: '{merged_text[:100]}...'")
        else:
            merged_segments.append(seg1)
    
    print(f"DEBUG: Content-based merging complete. Found {len(merged_segments)} merged segments")
    return merged_segments
    


def calculate_text_similarity(text1, text2):
    """
    Calculate similarity between two text segments using word overlap.
    Enhanced to better detect overlapping phrases and partial matches.
    
    Args:
        text1: First text segment
        text2: Second text segment
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize texts
    text1_lower = text1.lower().strip()
    text2_lower = text2.lower().strip()
    
    # Check if one is substring of another (high similarity)
    if text1_lower in text2_lower or text2_lower in text1_lower:
        return 0.9  # Very high similarity for substring matches
    
    # Split into words
    words1 = set(text1_lower.split())
    words2 = set(text2_lower.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    base_similarity = intersection / union
    
    # Bonus for longer overlapping sequences
    # Check for consecutive word matches
    words1_list = text1_lower.split()
    words2_list = text2_lower.split()
    
    # Find longest common subsequence
    max_common_length = 0
    for i in range(len(words1_list)):
        for j in range(len(words2_list)):
            common_length = 0
            while (i + common_length < len(words1_list) and 
                   j + common_length < len(words2_list) and
                   words1_list[i + common_length] == words2_list[j + common_length]):
                common_length += 1
            max_common_length = max(max_common_length, common_length)
    
    # Boost similarity if there are long consecutive matches
    if max_common_length >= 3:
        base_similarity += 0.2
    
    return min(1.0, base_similarity)

def merge_text_segments(texts):
    """
    Intelligently merge multiple text segments into one coherent sentence.
    
    Args:
        texts: List of text strings to merge
    
    Returns:
        Merged text string
    """
    if not texts:
        return ""
    
    if len(texts) == 1:
        return texts[0]
    
    # Remove duplicates and empty texts
    unique_texts = [text.strip() for text in texts if text.strip()]
    if not unique_texts:
        return ""
    
    if len(unique_texts) == 1:
        return unique_texts[0]
    
    # Find the longest text as base
    base_text = max(unique_texts, key=len)
    
    # Try to find complementary parts from other texts
    merged_parts = [base_text]
    
    for text in unique_texts:
        if text == base_text:
            continue
        
        # Check if this text adds new information
        if not is_substring_or_similar(text, base_text):
            # Add as separate part if it's not redundant
            merged_parts.append(text)
    
    # Join parts intelligently
    if len(merged_parts) == 1:
        return merged_parts[0]
    
    # Try to create a coherent sentence by combining parts
    # Remove common prefixes/suffixes and combine
    final_text = " ".join(merged_parts)
    
    # Clean up common transcription artifacts
    final_text = final_text.replace("  ", " ")  # Remove double spaces
    final_text = final_text.strip()
    
    return final_text

def is_substring_or_similar(text1, text2):
    """
    Check if one text is a substring of another or very similar.
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        True if one is substring of another or very similar
    """
    if not text1 or not text2:
        return False
    
    text1_lower = text1.lower().strip()
    text2_lower = text2.lower().strip()
    
    # Check if one is substring of another
    if text1_lower in text2_lower or text2_lower in text1_lower:
        return True
    
    # Check if they are very similar (high overlap)
    similarity = calculate_text_similarity(text1_lower, text2_lower)
    return similarity > 0.8

# OpenAI API key will be set dynamically via popup
OPENAI_API_KEY = None

# Function to get the path to ffmpeg and ffplay executables
def get_executable_path(executable_name):
    """Get the path to ffmpeg or ffplay executable, preferring bin/ subdirectory"""
    try:
        # First try the bin/ subdirectory relative to the script
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        bin_path = os.path.join(base_path, 'bin', executable_name)
        if os.path.exists(bin_path):
            return bin_path
        
        # Fallback to system PATH
        return executable_name
    except Exception:
        # Ultimate fallback
        return executable_name

# Function to create silent subprocess parameters
def get_silent_subprocess_params():
    """Get subprocess parameters to hide console windows on Windows"""
    try:
        startupinfo = None
        creationflags = 0
        if sys.platform.startswith('win'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW
        return startupinfo, creationflags
    except Exception:
        return None, 0

def get_openai_api_key():
    """Get OpenAI API key from user input or saved file"""
    global OPENAI_API_KEY

    # First try to load from saved file
    # Use the same path logic as get_output_filename for PyInstaller compatibility
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running as Python script
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    config_file = os.path.join(app_dir, 'openai_config.txt')

    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                saved_key = f.read().strip()
                if saved_key and saved_key.startswith('sk-'):
                    OPENAI_API_KEY = saved_key
                    os.environ['OPENAI_API_KEY'] = saved_key
                    return saved_key
    except Exception:
        pass

    # If no saved key, show popup
    return show_api_key_popup()

def show_api_key_popup():
    """Show popup to get OpenAI API key from user"""
    global OPENAI_API_KEY
    
    # Create popup window
    popup = tk.Tk()
    popup.title("OpenAI API Key Required")
    popup.geometry("500x300")
    popup.resizable(False, False)
    popup.transient()
    popup.grab_set()
    
    # Center the popup
    popup.eval('tk::PlaceWindow . center')
    
    # Main frame
    main_frame = ttk.Frame(popup, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="OpenAI API Key Required", 
                           font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 20))
    
    # Explanation
    explanation = """This application requires an OpenAI API key to transcribe audio.

Please enter your OpenAI API key below. You can get one from:
https://platform.openai.com/api-keys

Your key will be saved locally for future use."""
    
    explanation_label = ttk.Label(main_frame, text=explanation, 
                                wraplength=450, justify=tk.CENTER)
    explanation_label.pack(pady=(0, 20))
    
    # API Key entry
    key_frame = ttk.Frame(main_frame)
    key_frame.pack(pady=(0, 20))
    
    ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT)
    key_entry = ttk.Entry(key_frame, width=50, show="*")
    key_entry.pack(side=tk.LEFT, padx=(10, 0))
    
    # Buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=(0, 20))
    
    def save_key():
        key = key_entry.get().strip()
        if key and key.startswith('sk-'):
            global OPENAI_API_KEY
            OPENAI_API_KEY = key
            os.environ['OPENAI_API_KEY'] = key
            
            # Save to file
            try:
                # Use the same path logic for PyInstaller compatibility
                if getattr(sys, 'frozen', False):
                    # Running as compiled executable
                    app_dir = os.path.dirname(sys.executable)
                else:
                    # Running as Python script
                    app_dir = os.path.dirname(os.path.abspath(__file__))
                
                config_file = os.path.join(app_dir, 'openai_config.txt')
                with open(config_file, 'w') as f:
                    f.write(key)
            except Exception:
                pass
            
            popup.destroy()
        else:
            messagebox.showerror("Invalid Key", "Please enter a valid OpenAI API key that starts with 'sk-'")
    
    def cancel():
        popup.destroy()
        sys.exit(1)  # Exit if no key provided
    
    ttk.Button(button_frame, text="Save & Continue", command=save_key).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)
    
    # Focus on entry
    key_entry.focus_set()
    
    # Handle Enter key
    popup.bind('<Return>', lambda e: save_key())
    
    # Wait for popup to close
    popup.wait_window()
    
    return OPENAI_API_KEY

def remove_openai_api_key():
    """Remove the OpenAI API key by deleting the config file"""
    try:
        # Determine the correct path for the config file
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            app_dir = os.path.dirname(sys.executable)
        else:
            # Running as Python script
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        config_file = os.path.join(app_dir, "openai_config.txt")
        
        if os.path.exists(config_file):
            os.remove(config_file)
            messagebox.showinfo("Success", "OpenAI API key has been removed successfully.")
            # Clear the environment variable
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
        else:
            messagebox.showinfo("Info", "No OpenAI API key configuration file found.")
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to remove OpenAI API key: {str(e)}")

# Robust phrase filtering function
def filter_phrases_robust(phrases, stopwords, max_stopword_ratio=0.8):
    """
    Filter phrases based on stopword content with robust error handling.
    Optimized to prioritize longer, more meaningful phrases and minimize 2-word phrases.
    
    Strategy:
    - Much more lenient stopword filtering to keep meaningful longer phrases
    - Post-processing to limit 2-word phrases to maximum 15% of total
    - Prioritizes 4+ word phrases first, then 3-word phrases, minimal 2-word phrases
    
    Args:
        phrases: List of phrase tuples (phrase, score)
        stopwords: Set of stopwords
        max_stopword_ratio: Maximum allowed ratio of stopwords in a phrase
    
    Returns:
        List of filtered phrases with better length distribution
    """
    if not phrases or not stopwords:
        return []
    
    filtered_phrases = []
    
    try:
        for kw in phrases:
            if not isinstance(kw, (list, tuple)) or len(kw) == 0:
                continue
                
            phrase = str(kw[0]) if kw[0] is not None else ""
            if not phrase or ' ' not in phrase:
                continue
                
            # Split phrase safely
            try:
                words_in_phrase = phrase.split()
                if not words_in_phrase:
                    continue
            except Exception:
                continue
            
            # Count stopwords safely
            try:
                stopword_count = sum(1 for word in words_in_phrase if word in stopwords)
                total_words = len(words_in_phrase)
                
                # MUCH MORE LENIENT filtering to preserve almost all meaningful phrases
                if total_words >= 6:
                    # Allow max 5 stopwords for very long phrases (almost anything goes)
                    max_allowed = 5.0 / total_words
                elif total_words == 5:
                    # Allow max 4 stopwords for 5-word phrases
                    max_allowed = 4.0 / 5.0
                elif total_words == 4:
                    # Allow max 3 stopwords for 4-word phrases
                    max_allowed = 3.0 / 4.0
                elif total_words == 3:
                    # Allow max 2 stopwords for 3-word phrases
                    max_allowed = 2.0 / 3.0
                else:
                    # Allow max 1 stopword for 2-word phrases
                    max_allowed = 1.0 / 2.0
                
                # Apply the balanced filtering
                if total_words > 0 and stopword_count / total_words <= max_allowed:
                    # Additional check: ensure phrase is not just stopwords
                    if stopword_count == total_words:
                        continue  # Skip phrases that are only stopwords
                    
                    # Additional check: for 2-word phrases, ensure at least one word is meaningful
                    if total_words == 2 and stopword_count == 1:
                        # Check if the non-stopword word is substantial (not just 1-2 characters)
                        non_stopword = next((w for w in words_in_phrase if w not in stopwords), "")
                        if len(non_stopword) < 3:
                            continue  # Skip if non-stopword is too short
                    
                    filtered_phrases.append(phrase)
            except Exception:
                # If counting fails, skip the phrase (don't keep it)
                continue
                
    except Exception:
        # If filtering fails completely, return original phrases
        return [kw[0] for kw in phrases if isinstance(kw, (list, tuple)) and len(kw) > 0 and kw[0] is not None]
    
    # Post-process to prioritize longer phrases and minimize 2-word phrases
    try:
        if len(filtered_phrases) > 20:  # Only if we have many phrases
            # Count phrase lengths
            phrase_lengths = [len(phrase.split()) for phrase in filtered_phrases]
            
            # Separate phrases by length for better prioritization
            long_phrases = [p for p in filtered_phrases if len(p.split()) >= 4]  # 4+ word phrases
            medium_phrases = [p for p in filtered_phrases if len(p.split()) == 3]  # 3-word phrases
            two_word_phrases = [p for p in filtered_phrases if len(p.split()) == 2]  # 2-word phrases
            
            # Prioritize longer phrases: 4+ words get highest priority, then 3 words, reasonable 2 words
            # Limit 2-word phrases to maximum 35% of total (more generous for better coverage)
            max_two_word = min(len(filtered_phrases) * 0.35, len(two_word_phrases))
            if len(two_word_phrases) > max_two_word:
                two_word_phrases = two_word_phrases[:int(max_two_word)]
            
            # Combine with priority to longer phrases: 4+ words first, then 3 words, then limited 2 words
            filtered_phrases = long_phrases + medium_phrases + two_word_phrases
            
            # Merge overlapping phrases into longer, more complete phrases
            filtered_phrases = merge_overlapping_phrases(filtered_phrases)
            
            # Remove true sub-phrases that are completely contained within longer phrases
            filtered_phrases = remove_true_subphrases(filtered_phrases)
    except Exception:
        pass  # If post-processing fails, return original filtered phrases
    
    return filtered_phrases

# Function to merge overlapping phrases into longer, more complete phrases
def merge_overlapping_phrases(phrases):
    """
    Merge phrases that have overlapping words into longer, more complete phrases.
    This creates more meaningful content by combining related phrases.
    Phrases that cannot be merged are kept as-is.
    
    Args:
        phrases: List of phrases to merge
    
    Returns:
        List of merged phrases and unique phrases that couldn't be merged
    """
    if not phrases or len(phrases) <= 1:
        return phrases
    
    # Sort phrases by length (longest first) for better merging
    sorted_phrases = sorted(phrases, key=lambda x: len(x.split()), reverse=True)
    
    merged_phrases = []
    used_indices = set()
    
    for i, phrase in enumerate(sorted_phrases):
        if i in used_indices:
            continue
            
        phrase_lower = phrase.lower().strip()
        phrase_words = phrase_lower.split()
        best_merge = phrase
        best_merge_length = len(phrase_words)
        merged_with = []
        
        # Look for phrases to merge with
        for j, other_phrase in enumerate(sorted_phrases):
            if i == j or j in used_indices:
                continue
                
            other_lower = other_phrase.lower().strip()
            other_words = other_lower.split()
            
            # Check for overlapping words with more lenient requirements
            # Allow more merging to find more phrases
            min_overlap = 2 if min(len(phrase_words), len(other_words)) <= 4 else 3
            
            if len(phrase_words) >= 3 and len(other_words) >= 3:
                # Find common word sequences
                common_sequence = find_common_sequence(phrase_words, other_words)
                
                if len(common_sequence) >= min_overlap:  # More lenient overlap requirement
                    # Additional check: the overlap should be reasonable relative to phrase length
                    overlap_ratio = len(common_sequence) / min(len(phrase_words), len(other_words))
                    
                    # Allow merging with more lenient overlap (at least 40% of the shorter phrase)
                    if overlap_ratio >= 0.4:
                        # Try to merge the phrases
                        merged = merge_two_phrases(phrase, other_phrase, common_sequence)
                        if merged and len(merged.split()) > best_merge_length:
                            # Allow merging if the result is at least 1 word longer
                            if len(merged.split()) > best_merge_length + 1:
                                best_merge = merged
                                best_merge_length = len(merged.split())
                                merged_with.append(j)
        
        # Add the best merged phrase and mark used phrases
        merged_phrases.append(best_merge)
        used_indices.add(i)
        used_indices.update(merged_with)
    
    # Also add any phrases that weren't used (unique phrases with no overlaps)
    # But be more selective - only add phrases that are truly unique
    for i, phrase in enumerate(sorted_phrases):
        if i not in used_indices:
            # Check if this phrase is truly unique or just a failed merge attempt
            phrase_words = phrase.lower().strip().split()
            
            # Add more phrases to ensure better coverage
            if len(phrase_words) >= 3:
                merged_phrases.append(phrase)
            elif len(phrase_words) >= 2:
                # For 2-word phrases, check if they're meaningful
                # Look for meaningful content (not just common words)
                common_words = {'de', 'het', 'een', 'van', 'in', 'op', 'met', 'als', 'voor', 'aan', 'er', 'door', 'om', 'tot', 'ook', 'maar', 'uit', 'bij', 'over', 'nog', 'naar', 'dan', 'of', 'je', 'ik', 'ze', 'zij', 'hij', 'wij', 'jij', 'u', 'hun', 'ons', 'mijn', 'jouw', 'zijn', 'haar', 'hun', 'dit', 'dat', 'deze', 'die'}
                meaningful_words = [w for w in phrase_words if w not in common_words and len(w) >= 3]
                
                # Add if it has at least 1 meaningful word
                if len(meaningful_words) >= 1:
                    merged_phrases.append(phrase)
    
    return merged_phrases

def find_common_sequence(words1, words2):
    """Find the longest common continuous sequence of words between two lists."""
    if not words1 or not words2:
        return []
    
    # Convert to lowercase for comparison
    words1_lower = [w.lower() for w in words1]
    words2_lower = [w.lower() for w in words2]
    
    max_length = 0
    best_sequence = []
    
    # Check all possible starting positions
    for i in range(len(words1_lower)):
        for j in range(len(words2_lower)):
            if words1_lower[i] == words2_lower[j]:
                # Found a match, check how long the sequence is
                length = 0
                while (i + length < len(words1_lower) and 
                       j + length < len(words2_lower) and
                       words1_lower[i + length] == words2_lower[j + length]):
                    length += 1
                
                if length > max_length:
                    max_length = length
                    best_sequence = words1_lower[i:i + length]
    
    return best_sequence

def merge_two_phrases(phrase1, phrase2, common_sequence):
    """Merge two phrases based on their common word sequence."""
    if not common_sequence:
        return None
    
    # Find the position of the common sequence in both phrases
    phrase1_lower = phrase1.lower()
    phrase2_lower = phrase2.lower()
    common_text = ' ' + ' '.join(common_sequence) + ' '
    
    # Find start and end positions of common sequence in both phrases
    start1 = phrase1_lower.find(common_text)
    start2 = phrase2_lower.find(common_text)
    
    if start1 == -1 or start2 == -1:
        return None
    
    end1 = start1 + len(common_text) - 1  # -1 to remove leading space
    end2 = start2 + len(common_text) - 1
    
    # Extract unique parts
    before1 = phrase1[:start1].strip()
    after1 = phrase1[end1:].strip()
    before2 = phrase2[:start2].strip()
    after2 = phrase2[end2:].strip()
    
    # Build merged phrase: before1 + common + after1 + after2 (or before2 + common + after1)
    # Choose the combination that makes most sense
    if len(before1) > 0 and len(after2) > 0:
        merged = f"{before1} {common_text.strip()} {after2}".strip()
    elif len(before2) > 0 and len(after1) > 0:
        merged = f"{before2} {common_text.strip()} {after1}".strip()
    elif len(before1) > 0:
        merged = f"{before1} {common_text.strip()} {after1}".strip()
    elif len(before2) > 0:
        merged = f"{before2} {common_text.strip()} {after2}".strip()
    else:
        merged = common_text.strip()
    
    return merged

# Function to remove true sub-phrases that are completely contained within longer phrases
def remove_true_subphrases(phrases):
    """
    Remove shorter phrases that are completely contained within longer phrases.
    This eliminates redundancy by keeping only the longest, most complete phrases.
    
    Args:
        phrases: List of phrases to filter
    
    Returns:
        List of phrases with true sub-phrases removed
    """
    if not phrases or len(phrases) <= 1:
        return phrases
    
    # Sort phrases by length (longest first)
    sorted_phrases = sorted(phrases, key=lambda x: len(x.split()), reverse=True)
    
    filtered_phrases = []
    
    for phrase in sorted_phrases:
        phrase_lower = phrase.lower().strip()
        phrase_words = phrase_lower.split()
        
        # Check if this phrase is completely contained within any existing phrase
        is_subphrase = False
        
        for existing_phrase in filtered_phrases:
            existing_lower = existing_phrase.lower().strip()
            
            # Remove if the current phrase is a complete continuous sub-sequence of a longer phrase
            if len(phrase_words) < len(existing_lower.split()):
                phrase_with_spaces = ' ' + phrase_lower + ' '
                existing_with_spaces = ' ' + existing_lower + ' '
                if phrase_with_spaces in existing_with_spaces:
                    is_subphrase = True
                    break
        
        # Only add if it's not a true subphrase
        if not is_subphrase:
            filtered_phrases.append(phrase)
    
    return filtered_phrases

# Robust word filtering function
def filter_words_robust(words, stopwords):
    """
    Filter single words based on stopwords with robust error handling.
    
    Args:
        words: List of word tuples (word, score)
        stopwords: Set of stopwords
    
    Returns:
        List of filtered words
    """
    if not words or not stopwords:
        return []
    
    filtered_words = []
    
    try:
        for kw in words:
            if not isinstance(kw, (list, tuple)) or len(kw) == 0:
                continue
                
            word = str(kw[0]) if kw[0] is not None else ""
            if not word or ' ' in word:
                continue
                
            if word not in stopwords:
                filtered_words.append(word)
                
    except Exception:
        # If filtering fails completely, return original words
        return [kw[0] for kw in words if isinstance(kw, (list, tuple)) and len(kw) > 0 and kw[0] is not None and ' ' not in str(kw[0])]
    
    return filtered_words

# List of Dutch and Belgian Dutch (Flemish) radio stations (excluding Radio 4, music-only stations, 538 Top XXXX, and Radio 5 stations)
RADIO_STATIONS = {
    # Public Broadcasting (NPO) - News and Talk Focus
    'Radio 1 (Netherlands)': 'https://icecast.omroep.nl/radio1-bb-mp3',
    'Radio 2 (Netherlands)': 'https://icecast.omroep.nl/radio2-bb-mp3',
    'Radio 3FM': 'https://icecast.omroep.nl/3fm-bb-mp3',
    'Radio 6 (Netherlands)': 'https://icecast.omroep.nl/radio6-bb-mp3',
    
    # Regional Public Broadcasting - News and Local Content
    'Radio Rijnmond': 'http://d2e9xgjjdd9cr5.cloudfront.net/icecast/rijnmond/radio-mp3',
    
    
    # Commercial Radio Stations - News and Talk
    'BNR Nieuwsradio': 'https://stream.bnr.nl/bnr_mp3_128_20',
    'Radio 538': 'https://25583.live.streamtheworld.com/RADIO538.mp3',
    'Sky Radio': 'https://25583.live.streamtheworld.com/SKYRADIO.mp3',
    'Qmusic': 'https://25583.live.streamtheworld.com/QMUSIC.mp3',
    'Veronica': 'https://25583.live.streamtheworld.com/VERONICA.mp3',
    'Radio 10': 'https://25583.live.streamtheworld.com/RADIO10.mp3',
    
    # Alternative and Specialized - News and Talk Content
    'KINK': 'https://icecast.omroep.nl/kink-bb-mp3',
       
    # Belgian Dutch (Flemish) Radio Stations - News and Talk
    'Radio 1 (Belgium)': 'https://icecast.vrtcdn.be/radio1-high.mp3',
    'Klara': 'https://icecast.vrtcdn.be/klara-high.mp3',
    'MNM': 'https://icecast.vrtcdn.be/mnm-high.mp3',
    'Studio Brussel': 'https://icecast.vrtcdn.be/stubru-high.mp3',
    'VRT NWS': 'https://icecast.vrtcdn.be/vrtnws-high.mp3',
    
    # Flemish Regional Radio Stations
    'Radio 2 Antwerpen': 'https://icecast.vrtcdn.be/radio2_antw-high.mp3',
    'Radio 2 Limburg': 'https://icecast.vrtcdn.be/radio2_limb-high.mp3',
    'Radio 2 Oost-Vlaanderen': 'https://icecast.vrtcdn.be/radio2_ovl-high.mp3',
    'Radio 2 Vlaams-Brabant': 'https://icecast.vrtcdn.be/radio2_vbr-high.mp3',
    'Radio 2 West-Vlaanderen': 'https://icecast.vrtcdn.be/radio2_wvl-high.mp3',
    
    # Flemish Commercial Radio - News and Talk
    'Qmusic (Belgium)': 'https://25583.live.streamtheworld.com/QMUSIC_BE.mp3',
    'JOE FM': 'https://25583.live.streamtheworld.com/JOEFM.mp3',
    'Radio Contact': 'https://25583.live.streamtheworld.com/RADIOCONTACT.mp3',
    'TOPradio': 'https://25583.live.streamtheworld.com/TOPRADIO.mp3',
    
    # Flemish News and Current Affairs
    'Radio 1 Nieuws': 'https://icecast.vrtcdn.be/radio1-high.mp3',
    'Radio 2 Nieuws': 'https://icecast.vrtcdn.be/radio2-high.mp3',
    
    # Flemish Cultural and Educational
    'Klara Continuo': 'https://icecast.vrtcdn.be/klaracontinuo-high.mp3',
    'Klara Jazz': 'https://icecast.vrtcdn.be/klarajazz-high.mp3',
    'Sporza Radio': 'https://icecast.vrtcdn.be/sporza-high.mp3',
    
    # Flemish Local and Community Radio
    'Radio Scorpio': 'https://25583.live.streamtheworld.com/RADIOSCORPIO.mp3',
    'Radio Centraal': 'https://25583.live.streamtheworld.com/RADIOCENTRAAL.mp3',
    'Urgent.fm': 'https://25583.live.streamtheworld.com/URGENTFM.mp3',
    'Radio Campus': 'https://25583.live.streamtheworld.com/RADIOCAMPUS.mp3',
    


}

# Output file for recording
def get_output_filename(station_name):
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    
    # Try to use the executable's directory (works for both .py and .exe)
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running as Python script
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    base_folder = os.path.join(app_dir, "Recordings+transcriptions")
    
    # Create subfolder structure: YYYYMMDD_HHMMSS_StationName/
    station_sanitized = station_name.replace(" ", "_").replace("(", "").replace(")", "")
    folder_name = f"{timestamp}_{station_sanitized}"
    
    # Create the full path with subfolder
    full_path = os.path.join(base_folder, folder_name)
    os.makedirs(full_path, exist_ok=True)
    
    # Return path to MP3 file inside the subfolder
    return os.path.join(full_path, f"radio_recording_{timestamp}.mp3")

# Function to record stream using ffmpeg
def record_stream(stream_url, output_file, stop_event):
    ffmpeg_path = get_executable_path('ffmpeg.exe')
    cmd = [
        ffmpeg_path,
        '-y',
        '-i', stream_url,
        '-acodec', 'mp3',
        '-vn',
        output_file
    ]
    
    startupinfo, creationflags = get_silent_subprocess_params()
    
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        startupinfo=startupinfo,
        creationflags=creationflags
    )
    
    while not stop_event.is_set():
        time.sleep(1)
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

# GUI for selecting radio station and starting/stopping recording
class RadioRecorderApp:
    def __init__(self, master):
        self.master = master
        master.title(f"Radio Transcription Tool v{VERSION} - Powered by Bluvia (Dutch Language & Music Filtering)")
        
        # Set window icon if available
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Bluebird app icon 2a.ico')
            if os.path.exists(icon_path):
                master.iconbitmap(icon_path)
        except Exception:
            pass  # Icon setting is optional
        
        # Create menu bar
        self.create_menu()
        
        # Create main content frame
        main_frame = ttk.Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add Bluvia logo at the top
        self.create_logo_section(main_frame)
        
        self.station_var = tk.StringVar(value=list(RADIO_STATIONS.keys())[0])
        self.is_recording = False
        self.stop_event = threading.Event()
        self.recording_thread = None
        self.output_file = None
        self.is_listening = False
        self.listen_process = None
        
        # Audio cleanup setting (default: True - auto cleanup)
        self.auto_cleanup_audio = tk.BooleanVar(value=True)
        self.load_audio_cleanup_setting()

        ttk.Label(main_frame, text="Select a radio station:", font=('Arial', 12, 'bold')).pack(pady=10)
        self.dropdown = ttk.Combobox(main_frame, textvariable=self.station_var, values=list(RADIO_STATIONS.keys()), state='readonly', width=50)
        self.dropdown.pack(pady=5)

        # Create button frame for better layout
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=15)
        
        self.start_button = ttk.Button(button_frame, text="● Start Recording", command=self.start_recording, style='Accent.TButton')
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = ttk.Button(button_frame, text="■ Stop Recording", command=self.stop_recording, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.listen_button = ttk.Button(button_frame, text="► Listen Live", command=self.toggle_listen)
        self.listen_button.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(main_frame, text="Ready to record", font=('Arial', 10))
        self.status_label.pack(pady=15)
        
        # Add footer with Bluvia branding
        self.create_footer(main_frame)
    
    def show_api_key_popup(self):
        """Show popup to set OpenAI API key"""
        popup = tk.Toplevel(self.master)
        popup.title("Set OpenAI API Key")
        popup.geometry("400x200")
        popup.resizable(False, False)
        popup.transient(self.master)
        popup.grab_set()
        
        # Center the window
        popup.geometry("+%d+%d" % (self.master.winfo_rootx() + 100, self.master.winfo_rooty() + 100))
        
        # Main frame
        main_frame = ttk.Frame(popup, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(main_frame, text="Please enter your OpenAI API key:", font=('Arial', 10, 'bold')).pack(pady=(0, 10))
        ttk.Label(main_frame, text="The key will be saved locally for future use.", font=('Arial', 9)).pack(pady=(0, 20))
        
        # Key entry
        key_var = tk.StringVar()
        key_entry = ttk.Entry(main_frame, textvariable=key_var, width=50, show="*")
        key_entry.pack(pady=(0, 20))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        def save_key():
            key = key_var.get().strip()
            if key and key.startswith('sk-'):
                try:
                    # Determine the correct path for the config file
                    if getattr(sys, 'frozen', False):
                        # Running as compiled executable
                        app_dir = os.path.dirname(sys.executable)
                    else:
                        # Running as Python script
                        app_dir = os.path.dirname(os.path.abspath(__file__))
                    
                    config_file = os.path.join(app_dir, "openai_config.txt")
                    
                    with open(config_file, 'w') as f:
                        f.write(key)
                    
                    # Set environment variable
                    os.environ['OPENAI_API_KEY'] = key
                    
                    messagebox.showinfo("Success", "OpenAI API key has been saved successfully!")
                    popup.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save API key: {str(e)}")
            else:
                messagebox.showerror("Invalid Key", "Please enter a valid OpenAI API key that starts with 'sk-'")
        
        def cancel():
            popup.destroy()
        
        ttk.Button(button_frame, text="Save", command=save_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)
        
        # Focus on entry
        key_entry.focus_set()
        
        # Handle Enter key
        popup.bind('<Return>', lambda e: save_key())
    
    def remove_openai_api_key(self):
        """Remove the OpenAI API key by deleting the config file"""
        try:
            # Determine the correct path for the config file
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                app_dir = os.path.dirname(sys.executable)
            else:
                # Running as Python script
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            config_file = os.path.join(app_dir, "openai_config.txt")
            
            if os.path.exists(config_file):
                os.remove(config_file)
                messagebox.showinfo("Success", "OpenAI API key has been removed successfully.")
                # Clear the environment variable
                if 'OPENAI_API_KEY' in os.environ:
                    del os.environ['OPENAI_API_KEY']
            else:
                messagebox.showinfo("Info", "No OpenAI API key configuration file found.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove OpenAI API key: {str(e)}")
    
    def load_audio_cleanup_setting(self):
        """Load audio cleanup setting from config file"""
        try:
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            config_file = os.path.join(app_dir, "audio_cleanup_config.txt")
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    setting = f.read().strip().lower()
                    if setting == 'false':
                        self.auto_cleanup_audio.set(False)
            else:
                # Create default config file
                with open(config_file, 'w') as f:
                    f.write('true')
                    
        except Exception as e:
            print(f"Warning: Could not load audio cleanup setting: {e}")
            # Keep default value (True)
    
    def create_menu(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.master.quit)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Set OpenAI API Key", command=self.show_api_key_popup)
        settings_menu.add_command(label="Remove OpenAI API Key", command=self.remove_openai_api_key)
        settings_menu.add_separator()
        settings_menu.add_command(label="Audio Cleanup Settings", command=self.show_audio_cleanup_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label="Transcribe Recent Recordings", command=self.transcribe_recent_recordings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_separator()
        help_menu.add_command(label="Bluvia Website", command=self.open_bluvia_website)
    
    def create_logo_section(self, parent):
        """Create the logo section at the top of the application"""
        logo_frame = ttk.Frame(parent)
        logo_frame.pack(fill=tk.X, pady=(0, 20))
        
        try:
            # Try to load and display the Bluebird favicon (medium-large size)
            favicon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Bluvia images', 'Bluebird favicon.jpeg')
            if os.path.exists(favicon_path):
                from PIL import Image, ImageTk
                # Load and resize favicon to medium-large size
                img = Image.open(favicon_path)
                img = img.resize((64, 64), Image.Resampling.LANCZOS)  # Medium-large size
                photo = ImageTk.PhotoImage(img)
                
                # Create favicon label
                favicon_label = ttk.Label(logo_frame, image=photo)
                favicon_label.image = photo  # Keep a reference
                favicon_label.pack(side=tk.LEFT, padx=(0, 20))
                
                # Add title next to favicon
                title_label = ttk.Label(logo_frame, text="Radio Transcription Tool", 
                                      font=('Arial', 18, 'bold'), foreground='#2E86AB')
                title_label.pack(side=tk.LEFT, pady=20)
                
        except Exception as e:
            # Fallback if favicon can't be loaded
            title_label = ttk.Label(logo_frame, text="Radio Transcription Tool", 
                                  font=('Arial', 18, 'bold'), foreground='#2E86AB')
            title_label.pack(pady=20)
    
    def create_footer(self, parent):
        """Create footer with Bluvia branding"""
        footer_frame = ttk.Frame(parent)
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Add separator
        separator = ttk.Separator(footer_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=10)
        
        # Footer text
        footer_text = ttk.Label(footer_frame, text="Powered by Bluvia - Dutch Language & Music Filtering Solutions", 
                               font=('Arial', 9), foreground='#666666')
        footer_text.pack()
        
        # Version in footer
        version_footer = ttk.Label(footer_frame, text=f"v{VERSION}", 
                                  font=('Arial', 8), foreground='#999999')
        version_footer.pack()
        
        # Add favicon if available
        try:
            favicon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Bluvia images', 'Bluebird favicon.jpeg')
            if os.path.exists(favicon_path):
                from PIL import Image, ImageTk
                # Load and resize favicon
                img = Image.open(favicon_path)
                img = img.resize((16, 16), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                favicon_label = ttk.Label(footer_frame, image=photo)
                favicon_label.image = photo
                favicon_label.pack(side=tk.RIGHT, padx=10)
                
        except Exception:
            pass  # Favicon is optional
    
    def show_about(self):
        """Show the About dialog with Bluvia information"""
        # Create custom about dialog with logo
        about_window = tk.Toplevel(self.master)
        about_window.title("About - Radio Transcription Tool")
        about_window.geometry("500x520")
        about_window.resizable(False, False)
        about_window.transient(self.master)
        about_window.grab_set()
        
        # Center the window
        about_window.geometry("+%d+%d" % (self.master.winfo_rootx() + 50, self.master.winfo_rooty() + 50))
        
        # Main frame
        main_frame = ttk.Frame(about_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Try to load and display the Bluvia logo
        try:
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Bluvia images', 'Bluvia logo.jpeg')
            if os.path.exists(logo_path):
                from PIL import Image, ImageTk
                # Load and resize logo
                img = Image.open(logo_path)
                img = img.resize((300, 120), Image.Resampling.LANCZOS)  # Larger size for about dialog
                photo = ImageTk.PhotoImage(img)
                
                # Create logo label
                logo_label = ttk.Label(main_frame, image=photo)
                logo_label.image = photo  # Keep a reference
                logo_label.pack(pady=(0, 20))
        except Exception:
            # Fallback if logo can't be loaded
            pass
        
        # Title
        title_label = ttk.Label(main_frame, text=f"Radio Transcription Tool v{VERSION}", 
                              font=('Arial', 16, 'bold'), foreground='#2E86AB')
        title_label.pack(pady=(0, 15))
        
        # Description
        desc_label = ttk.Label(main_frame, text="A professional-grade application for recording and transcribing radio broadcasts with advanced keyword extraction and analysis.", 
                             font=('Arial', 10), wraplength=450, justify='center')
        desc_label.pack(pady=(0, 15))
        
        # Features
        features_text = """Features:
• Live radio recording from Dutch stations
• AI-powered transcription using OpenAI Whisper
• Dutch language optimization for radio content
• Music transcription filtering
• Intelligent keyword and phrase extraction
• Support for multiple audio formats
• Professional output formatting"""
        
        features_label = ttk.Label(main_frame, text=features_text, font=('Arial', 9), justify='left')
        features_label.pack(pady=(0, 15))
        
        # Powered by
        powered_label = ttk.Label(main_frame, text="Powered by Bluvia Technology", 
                                font=('Arial', 12, 'bold'), foreground='#2E86AB')
        powered_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="Dutch Language & Music Filtering Solutions", 
                                 font=('Arial', 9), foreground='#666666')
        subtitle_label.pack(pady=(0, 15))
        
        # Copyright
        copyright_label = ttk.Label(main_frame, text="© 2024 Bluvia. All rights reserved.", 
                                  font=('Arial', 8), foreground='#999999')
        copyright_label.pack(pady=(0, 20))
        
        # Close button
        close_button = ttk.Button(main_frame, text="Close", command=about_window.destroy)
        close_button.pack()
        
        # Focus on the about window
        about_window.focus_set()
    
    def show_user_guide(self):
        """Show the user guide dialog with proper width"""
        # Create a custom dialog instead of messagebox for better width control
        guide_window = tk.Toplevel(self.master)
        guide_window.title("Radio Transcription Tool - User Guide")
        guide_window.geometry("600x500")  # Much more compact height
        guide_window.resizable(True, True)
        
        # Center the window
        guide_window.transient(self.master)
        guide_window.grab_set()
        
        # Create main frame with padding
        main_frame = ttk.Frame(guide_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Radio Transcription Tool - User Guide", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Guide text with proper formatting
        guide_text = """1. SELECT A STATION
   Choose from the dropdown menu of available Dutch radio stations.

2. START RECORDING
   Click "Start Recording" to begin capturing the radio stream.
   The recording will continue until you click "Stop Recording".

3. LISTEN LIVE
   Use "Listen Live" to preview the station before recording.

4. TRANSCRIPTION
   After stopping the recording, the tool automatically:
   - Transcribes the audio using AI
   - Extracts key talking points
   - Identifies important phrases
   - Saves results to a text file

5. OUTPUT
   Results are saved in the same folder as your recording.
   The folder will automatically open when transcription is complete.

For technical support or questions, visit the Bluvia website."""
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10), 
                             padx=10, pady=10, relief=tk.SUNKEN, borderwidth=1)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert guide text
        text_widget.insert(tk.END, guide_text)
        text_widget.config(state=tk.DISABLED)  # Make read-only
        
        # Close button
        close_button = ttk.Button(main_frame, text="Close", 
                                 command=guide_window.destroy)
        close_button.pack(pady=(20, 0))
        
        # Focus on the window
        guide_window.focus_set()
    
    def open_bluvia_website(self):
        """Open the Bluvia website in the default browser"""
        try:
            import webbrowser
            webbrowser.open("https://bluvia.nl")  # Bluvia website
        except Exception:
            messagebox.showinfo("Website", "Please visit https://bluvia.nl in your web browser.")

    def save_audio_cleanup_setting(self):
        """Save audio cleanup setting to config file"""
        try:
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            config_file = os.path.join(app_dir, "audio_cleanup_config.txt")
            
            with open(config_file, 'w') as f:
                f.write(str(self.auto_cleanup_audio.get()).lower())
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save audio cleanup setting: {str(e)}")
    
    def show_audio_cleanup_settings(self):
        """Show audio cleanup settings dialog"""
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Audio Cleanup Settings")
        settings_window.geometry("400x250")
        settings_window.resizable(False, False)
        settings_window.transient(self.master)
        settings_window.grab_set()
        
        # Center the window
        settings_window.geometry("+%d+%d" % (self.master.winfo_rootx() + 100, self.master.winfo_rooty() + 100))
        
        # Main frame
        main_frame = ttk.Frame(settings_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Audio Cleanup Settings", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_label = ttk.Label(main_frame, text="Choose whether to automatically delete audio files after successful transcription:", 
                              font=('Arial', 10), wraplength=350, justify='center')
        desc_label.pack(pady=(0, 20))
        
        # Checkbox frame
        checkbox_frame = ttk.Frame(main_frame)
        checkbox_frame.pack(pady=10)
        
        # Checkbox
        cleanup_checkbox = ttk.Checkbutton(checkbox_frame, text="Automatically delete audio files after transcription", 
                                          variable=self.auto_cleanup_audio, 
                                          command=self.save_audio_cleanup_setting)
        cleanup_checkbox.pack()
        
        # Info text
        info_label = ttk.Label(main_frame, text="When enabled: Audio files are automatically deleted after successful transcription\nWhen disabled: Audio files are kept for manual review", 
                              font=('Arial', 9), foreground='#666666', wraplength=350, justify='center')
        info_label.pack(pady=20)
        
        # Close button
        close_button = ttk.Button(main_frame, text="Close", command=settings_window.destroy)
        close_button.pack()
        
        # Focus on the settings window
        settings_window.focus_set()

    def toggle_listen(self):
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        station = self.station_var.get()
        stream_url = RADIO_STATIONS[station]
        try:
            ffplay_path = get_executable_path('ffplay.exe')
            ffplay_cmd = [
                ffplay_path, '-nodisp', '-autoexit', '-loglevel', 'quiet', stream_url
            ]
            
            startupinfo, creationflags = get_silent_subprocess_params()
            
            self.listen_process = subprocess.Popen(
                ffplay_cmd,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            self.is_listening = True
            self.listen_button.config(text="❚❚ Stop Listening")
            self.status_label.config(text=f"Listening: {station}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play stream: {e}")

    def stop_listening(self):
        if self.listen_process:
            self.listen_process.terminate()
            try:
                self.listen_process.wait(timeout=3)
            except Exception:
                self.listen_process.kill()
            self.listen_process = None
        self.is_listening = False
        self.listen_button.config(text="► Listen Live")
        self.status_label.config(text="Idle")

    def start_recording(self):
        if self.is_recording:
            return
        station = self.station_var.get()
        stream_url = RADIO_STATIONS[station]
        self.output_file = get_output_filename(station)
        self.stop_event.clear()
        self.recording_thread = threading.Thread(target=record_stream, args=(stream_url, self.output_file, self.stop_event))
        self.recording_thread.start()
        self.is_recording = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text=f"Recording: {station}")

    def stop_recording(self):
        if not self.is_recording:
            return
        self.stop_event.set()
        if self.recording_thread is not None:
            self.recording_thread.join()
        self.is_recording = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text=f"Recording saved to {self.output_file}. Starting transcription...")
        
        # Start transcription immediately without blocking message box
        transcription_thread = threading.Thread(target=self.transcribe_and_extract, args=(self.output_file,))
        transcription_thread.daemon = True
        transcription_thread.start()

    def transcribe_and_extract(self, audio_path):
        # Setup logging
        setup_logging()
        
        # Log recording start
        recording_name = os.path.basename(audio_path)
        logging.info(f"RECORDING START: {recording_name}")
        
        print("DEBUG: Starting transcription process...")
        print("DEBUG: This should be visible in console/terminal")
        
        if AudioSegment is None:
            # Use after() to schedule GUI updates in the main thread
            self.master.after(0, lambda: messagebox.showerror("Dependency Error", "pydub is not installed. Please install it with 'pip install pydub'."))
            return
        
        # Update status in main thread
        self.master.after(0, lambda: self.status_label.config(text="Transcribing audio with Dutch language optimization and music filtering..."))
        
        print("DEBUG: Status updated in GUI")
        print("DEBUG: About to override subprocess for transcription")
        
        # Override subprocess globally for this entire transcription process
        import subprocess
        original_popen = subprocess.Popen
        startupinfo, creationflags = get_silent_subprocess_params()
        
        def silent_popen(*args, **kwargs):
            # Add silent parameters to all subprocess calls
            kwargs['startupinfo'] = startupinfo
            kwargs['creationflags'] = creationflags
            kwargs['stdout'] = subprocess.PIPE
            kwargs['stderr'] = subprocess.PIPE
            return original_popen(*args, **kwargs)
        
        # Replace subprocess.Popen globally for the entire transcription
        subprocess.Popen = silent_popen
        
        try:
            # Split audio into 5-minute chunks (300000 ms) for better transcription quality
            chunk_length_ms = 5 * 60 * 1000
            
            # Load audio with error handling
            try:
                audio = AudioSegment.from_file(audio_path)
                duration_ms = len(audio)
            except Exception as audio_error:
                self.master.after(0, lambda: messagebox.showerror("Audio Error", f"Failed to load audio file: {str(audio_error)}\n\nThis could be due to:\n- Corrupted audio file\n- Unsupported audio format\n- File access issues\n\nPlease try recording again."))
                self.master.after(0, lambda: self.status_label.config(text="Failed to load audio file"))
                return
            
            num_chunks = math.ceil(duration_ms / chunk_length_ms)
            all_segments = []
            
            # Check if audio is valid
            if duration_ms == 0:
                self.master.after(0, lambda: messagebox.showerror("Audio Error", "The recorded audio file has zero duration. This could be due to:\n- Recording was too short\n- Audio file corruption\n- Recording failed\n\nPlease try recording again."))
                self.master.after(0, lambda: self.status_label.config(text="Audio file has zero duration"))
                return
            
            for i in range(num_chunks):
                try:
                    # Update progress in main thread
                    self.master.after(0, lambda i=i: self.status_label.config(text=f"Transcribing chunk {i+1}/{num_chunks}..."))
                    
                    start_ms = i * chunk_length_ms
                    end_ms = min((i + 1) * chunk_length_ms, duration_ms)
                    chunk = audio[start_ms:end_ms]
                    
                    # Create chunk file in same folder as recording
                    recording_dir = os.path.dirname(audio_path)
                    chunk_path = os.path.join(recording_dir, f"chunk_{i}.mp3")
                    
                    # Use regular export since subprocess is already overridden
                    try:
                        chunk.export(chunk_path, format="mp3")
                    except Exception as export_error:
                        print(f"Failed to export chunk {i+1}: {export_error}")
                        self.master.after(0, lambda i=i: self.status_label.config(text=f"Chunk {i+1} export failed, continuing..."))
                        continue
                    
                    # Add timeout and retry logic for OpenAI API calls
                    max_retries = 3
                    response = None
                    for retry in range(max_retries):
                        try:
                            with open(chunk_path, "rb") as f:
                                client = openai.OpenAI()
                                response = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=f,
                                    response_format="verbose_json",
                                    language="nl",
                                    prompt="Dit is een Nederlandse radio-uitzending met nieuws, discussies, interviews en gesprekken. Focus op spraak en gesprekken, niet op muziek. De transcriptie moet alle belangrijke woorden en zinnen bevatten, maar muziekteksten en jingles kunnen worden overgeslagen.",
                                    temperature=0.0,  # More consistent transcription
                                )
                            break  # Success, exit retry loop
                        except Exception as api_error:
                            if retry < max_retries - 1:
                                # Update status to show retry
                                self.master.after(0, lambda i=i, retry=retry: self.status_label.config(text=f"Chunk {i+1} failed, retrying ({retry+1}/3)..."))
                                time.sleep(2)  # Wait before retry
                            else:
                                # Final retry failed, log error and continue
                                print(f"Failed to transcribe chunk {i+1} after {max_retries} retries: {api_error}")
                                self.master.after(0, lambda i=i: self.status_label.config(text=f"Chunk {i+1} failed, continuing..."))
                                response = None
                    
                    # Process response if we got one
                    if response:
                        # Handle both dict and object types for segments
                        segments = None
                        if hasattr(response, 'segments'):
                            segments = response.segments
                        elif isinstance(response, dict) and "segments" in response:
                            segments = response["segments"]
                        
                        if segments:
                            # Convert segments to dicts if needed
                            seg_dicts = []
                            for seg in segments:
                                if isinstance(seg, dict):
                                    seg_dicts.append(seg)
                                else:
                                    # Try to convert object to dict
                                    seg_dicts.append({
                                        "start": getattr(seg, "start", 0),
                                        "end": getattr(seg, "end", 0),
                                        "text": getattr(seg, "text", "")
                                    })
                            
                            # Adjust timestamps for each chunk
                            for seg in seg_dicts:
                                seg["start"] += start_ms / 1000
                                seg["end"] += start_ms / 1000
                            all_segments.extend(seg_dicts)
                    
                    # Clean up chunk file
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                        
                except Exception as chunk_error:
                    # Log chunk error and continue with next chunk
                    print(f"Error processing chunk {i+1}: {chunk_error}")
                    self.master.after(0, lambda i=i: self.status_label.config(text=f"Chunk {i+1} error, continuing..."))
                    # Clean up chunk file if it exists
                    chunk_path = os.path.join(os.path.dirname(audio_path), f"chunk_{i}.mp3")
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                    continue
            
            # Extract key points and phrases
            try:
                # First, merge similar sentences with the same timestamp to eliminate duplicates
                print(f"DEBUG: Before merging: {len(all_segments)} segments")
                # Merge similar sentences across ALL timestamps, not just 0.0s
                print(f"DEBUG: Starting merge process...")
                merged_segments = merge_similar_segments(all_segments, similarity_threshold=0.4)
                print(f"DEBUG: After merging: {len(merged_segments)} segments")
                
                # Apply music filtering to each segment before joining
                filtered_segments = []
                print(f"DEBUG: Processing {len(merged_segments)} segments for transcript creation")
                for seg_idx, seg in enumerate(merged_segments):
                    if seg and isinstance(seg, dict):
                        text = seg.get("text", "")
                        if text.strip():
                            # Apply music filtering to this segment
                            filtered_text = filter_music_transcription(text)
                            if filtered_text != text:
                                print(f"DEBUG: Music filtered from segment: {text[:100]}...")
                            filtered_segments.append(filtered_text)
                            if seg_idx < 3:  # Show first 3 segments for debugging
                                print(f"DEBUG: Segment {seg_idx+1}: '{text[:100]}...'")
                        else:
                            print(f"DEBUG: Empty segment {seg_idx+1} skipped")
                
                transcript = " ".join(filtered_segments)
                print(f"DEBUG: Applied music filtering to {len(merged_segments)} segments")
                print(f"DEBUG: TRANSCRIPT CREATED - Length: {len(transcript)} characters, Words: {len(transcript.split())}")
                print(f"DEBUG: First 200 chars of transcript: '{transcript[:200]}...'")
                print(f"DEBUG: Last 200 chars of transcript: '...{transcript[-200:]}'")
                
                # Log transcript creation
                logging.info(f"TRANSCRIPT: {len(transcript.split())} words, {len(transcript)} chars")
            except Exception as transcript_error:
                print(f"Error creating transcript: {transcript_error}")
                transcript = ""
            
            # Use global keybert_available variable
            global keybert_available
            
            # Check if transcript is empty or too short
            if not transcript.strip():
                # Show error message in GUI
                self.master.after(0, lambda: messagebox.showwarning("No Speech Detected", "No speech was detected in the recording. This could be due to:\n- Silence or background noise only\n- Audio quality issues\n- Transcription service problems\n\nPlease try recording again with clearer audio."))
                self.master.after(0, lambda: self.status_label.config(text="No speech detected in recording"))
                return
            
            # Debug: Show transcript length for troubleshooting
            transcript_length = len(transcript.split())
            print(f"DEBUG: Transcript contains {transcript_length} words")
            if transcript_length < 100:
                print(f"DEBUG: Warning - transcript seems very short for a 1-hour recording")
            
            if keybert_available:
                try:
                    # Check if transcript is too short for KeyBERT
                    if len(transcript.split()) < 50:
                        keybert_available = False
                    else:
                        # Use global stopwords for KeyBERT filtering
                        stopwords = DUTCH_STOPWORDS
                        
                        # Try KeyBERT for phrases first - balanced approach with focus on longer phrases
                        kw_model = KeyBERT()
                        keywords_phrases = kw_model.extract_keywords(transcript, keyphrase_ngram_range=(2,8), top_n=60)
                        
                        # Also get medium-length phrases (2-4 words) as backup for better coverage
                        keywords_medium = kw_model.extract_keywords(transcript, keyphrase_ngram_range=(2,4), top_n=50)
                        
                        # Try KeyBERT for single words separately - without stopwords to get more results
                        keywords_words = kw_model.extract_keywords(transcript, keyphrase_ngram_range=(1,1), top_n=20)
                        

                        
                        # Apply frequency filtering to KeyBERT results - only keep phrases that appear multiple times
                        from collections import Counter
                        transcript_words = transcript.lower().split()
                        
                        # ESSENTIAL DEBUG: Check if variables are properly initialized

                        
                        # Count phrase occurrences in transcript - FLEXIBLE VERSION
                        def count_phrase_occurrences(phrase, transcript_words):
                            # Normalize both phrase and transcript for better matching
                            phrase_normalized = ' '.join(phrase.lower().split())
                            transcript_text = ' '.join(transcript_words).lower()
                            

                            
                            # Count exact matches first
                            count = transcript_text.count(phrase_normalized)
                            
                            # If no exact matches, try flexible word-by-word matching
                            if count == 0:
                                phrase_words = phrase.lower().split()
                                # Look for sequences of words that match (allowing for minor variations)
                                for i in range(len(transcript_words) - len(phrase_words) + 1):
                                    window = transcript_words[i:i+len(phrase_words)]
                                    window_text = ' '.join(window).lower()
                                    
                                    # Exact match
                                    if window_text == phrase_normalized:
                                        count += 1
        
                                    # Flexible match: check if most words match (at least 80% of words for longer phrases)
                                    elif len(phrase_words) >= 4:
                                        matching_words = sum(1 for j, word in enumerate(phrase_words) 
                                                           if j < len(window) and word == window[j])
                                        if matching_words >= len(phrase_words) * 0.8:
                                            count += 1
    
                            

                            return count
                        
                        # Filter phrases by score first, then frequency (MORE LENIENT approach for better coverage)
                        filtered_keywords_phrases = []
                        for phrase, score in keywords_phrases:
                            occurrences = count_phrase_occurrences(phrase, transcript_words)
                            # More lenient filtering to capture more phrases
                            # High scores (0.35+) with 1+ occurrence
                            # Medium scores (0.2+) with 1+ occurrence  
                            # Lower scores with 1+ occurrence (more lenient)
                            if (score > 0.35 and occurrences >= 1) or (score > 0.2 and occurrences >= 1) or (score > 0.1 and occurrences >= 1):
                                filtered_keywords_phrases.append((phrase, score))

                        
                        filtered_keywords_medium = []
                        for phrase, score in keywords_medium:
                            occurrences = count_phrase_occurrences(phrase, transcript_words)
                            # More lenient approach for medium phrases: all must occur at least once
                            if (score > 0.3 and occurrences >= 1) or (score > 0.15 and occurrences >= 1) or (score > 0.08 and occurrences >= 1):
                                filtered_keywords_medium.append((phrase, score))

                        

                        
                        # FALLBACK STRATEGY: If frequency filtering still removes too many phrases, use KeyBERT results with more lenient score filtering
                        if len(filtered_keywords_phrases) < 8 or len(filtered_keywords_medium) < 8:  # More lenient threshold

                            # More lenient score filtering to preserve more results
                            filtered_keywords_phrases = [(phrase, score) for phrase, score in keywords_phrases if score > 0.08]
                            filtered_keywords_medium = [(phrase, score) for phrase, score in keywords_medium if score > 0.05]

                            
                            # Extract phrases for stopword filtering
                            filtered_keywords_phrases_text = [phrase for phrase, score in filtered_keywords_phrases]
                            filtered_keywords_medium_text = [phrase for phrase, score in filtered_keywords_medium]
                            
                            # Apply very lenient stopword filtering to preserve more results
                            basic_stopwords = {'de', 'het', 'een', 'en', 'van', 'in', 'te', 'dat', 'die', 'is', 'op', 'met', 'als', 'voor', 'aan', 'er', 'door', 'om', 'tot', 'ook', 'maar', 'uit', 'bij', 'over', 'nog', 'naar', 'dan', 'of', 'je', 'ik', 'ze', 'zij', 'hij', 'wij', 'jij', 'u', 'hun', 'ons', 'mijn', 'jouw', 'zijn', 'haar', 'hun', 'dit', 'dat', 'deze', 'die'}
                            
                            try:
                                filtered_phrases = filter_phrases_robust(filtered_keywords_phrases_text, basic_stopwords)
                                filtered_medium = filter_phrases_robust(filtered_keywords_medium_text, basic_stopwords)
        
                            except Exception as filter_error:

                                # If filtering fails, accept all results
                                filtered_phrases = filtered_keywords_phrases_text
                                filtered_medium = filtered_keywords_medium_text
                            
                            # If still too few, accept all
                            if len(filtered_phrases) < 15:

                                filtered_phrases = filtered_keywords_phrases_text
                            
                            if len(filtered_medium) < 15:

                                filtered_medium = filtered_keywords_medium_text
                        
                        # Combine results with smart filtering
                        keypoints = []
                        
                        # Use the full stopwords list for filtering
                        common_stopwords = DUTCH_STOPWORDS
                        
                        filtered_words = filter_words_robust(keywords_words, common_stopwords)
                        
                        # Filter phrases to remove those with too many stopwords - much more lenient for KeyBERT results
                        # First extract just the phrases from KeyBERT results (remove scores)
                        filtered_keywords_phrases_text = [phrase for phrase, score in filtered_keywords_phrases]
                        filtered_keywords_medium_text = [phrase for phrase, score in filtered_keywords_medium]
                        
                        # Use very basic stopwords only for KeyBERT results to preserve more phrases
                        basic_stopwords = {'de', 'het', 'een', 'en', 'van', 'in', 'te', 'dat', 'die', 'is', 'op', 'met', 'als', 'voor', 'aan', 'er', 'door', 'om', 'tot', 'ook', 'maar', 'uit', 'bij', 'over', 'nog', 'naar', 'dan', 'of', 'je', 'ik', 'ze', 'zij', 'hij', 'wij', 'jij', 'u', 'hun', 'ons', 'mijn', 'jouw', 'zijn', 'haar', 'hun', 'dit', 'dat', 'deze', 'die'}
                        
                        try:
                            filtered_phrases = filter_phrases_robust(filtered_keywords_phrases_text, basic_stopwords)
                            filtered_medium = filter_phrases_robust(filtered_keywords_medium_text, basic_stopwords)
    
                        except Exception as filter_error:

                            # If filtering fails, accept all results
                            filtered_phrases = filtered_keywords_phrases_text
                            filtered_medium = filtered_keywords_medium_text

                        
                        # If still too few phrases, be much more lenient - accept more phrases with lower scores
                        if len(filtered_phrases) < 10:

                            # Much more lenient score filtering to preserve more meaningful content
                            low_score_phrases = [phrase for phrase, score in filtered_keywords_phrases if score > 0.15]  # Lower threshold
                            filtered_phrases = low_score_phrases[:30]  # Accept more phrases

                        
                        if len(filtered_medium) < 10:

                            # Much more lenient score filtering for medium phrases
                            low_score_medium = [phrase for phrase, score in filtered_keywords_medium if score > 0.1]  # Lower threshold
                            filtered_medium = low_score_medium[:25]  # Accept more phrases

                        
                        # If filtering removes too many phrases, be more lenient but still require at least 1 occurrence
                        if len(filtered_phrases) < 8:  # More lenient threshold
                            # Re-extract with higher top_n to get more candidates
                            keywords_phrases_extended = kw_model.extract_keywords(transcript, keyphrase_ngram_range=(2,8), top_n=100)
                            for phrase, score in keywords_phrases_extended:
                                # Be more lenient for long meaningful phrases (likely complete thoughts/ad blocks)
                                if len(phrase.split()) >= 8:
                                    # Long phrases get priority - keep them even with 1 occurrence
                                    filtered_keywords_phrases.append((phrase, score))
                                    print(f"DEBUG: Preserved long phrase from KeyBERT: '{phrase[:100]}...'")
                                elif count_phrase_occurrences(phrase, transcript_words) >= 1:  # More lenient: 1+ occurrence
                                    filtered_keywords_phrases.append((phrase, score))
                                
                                if len(filtered_keywords_phrases) >= 35:  # Increased limit to include more long phrases
                                    break
                            # Re-filter with the extended results - extract phrases first
                            filtered_keywords_phrases_text = [phrase for phrase, score in filtered_keywords_phrases]
                            filtered_phrases = filter_phrases_robust(filtered_keywords_phrases_text, common_stopwords)
                        
                        if len(filtered_medium) < 8:  # More lenient threshold
                            keywords_medium_extended = kw_model.extract_keywords(transcript, keyphrase_ngram_range=(2,8), top_n=80)
                            for phrase, score in keywords_medium_extended:
                                if count_phrase_occurrences(phrase, transcript_words) >= 1:  # More lenient: 1+ occurrence
                                    filtered_keywords_medium.append((phrase, score))
                                    if len(filtered_keywords_medium) >= 20:  # Increased limit
                                        break
                            # Re-filter with the extended results - extract phrases first
                            filtered_keywords_medium_text = [phrase for phrase, score in filtered_keywords_medium]
                            filtered_medium = filter_phrases_robust(filtered_keywords_medium_text, common_stopwords)
                        
                        # If filtering removes too many words, be less strict
                        if len(filtered_words) < 5 and len(keywords_words) > 0:
                            # Only filter out the most basic stopwords
                            basic_stopwords = {'de', 'het', 'een', 'en', 'van', 'in', 'te', 'dat', 'die', 'is', 'op', 'met', 'als', 'voor', 'aan', 'er', 'door', 'om', 'tot', 'ook', 'maar', 'uit', 'bij', 'over', 'nog', 'naar', 'dan', 'of', 'je', 'ik', 'ze', 'zij', 'hij', 'wij', 'jij', 'u', 'hun', 'ons', 'mijn', 'jouw', 'zijn', 'haar', 'hun', 'dit', 'dat', 'deze', 'die'}
                            filtered_words = filter_words_robust(keywords_words, basic_stopwords)
                        
                        # Extract just the phrases from the filtered results (handle strings or (phrase, score) tuples)
                        if isinstance(filtered_phrases, list) and filtered_phrases and isinstance(filtered_phrases[0], (list, tuple)):
                            filtered_phrases_text = [phrase for phrase, score in filtered_phrases]
                        else:
                            filtered_phrases_text = filtered_phrases if isinstance(filtered_phrases, list) else []

                        if isinstance(filtered_medium, list) and filtered_medium and isinstance(filtered_medium[0], (list, tuple)):
                            filtered_medium_text = [phrase for phrase, score in filtered_medium]
                        else:
                            filtered_medium_text = filtered_medium if isinstance(filtered_medium, list) else []
                        
                        keypoints.extend(filtered_words)
                        keypoints.extend(filtered_phrases_text)  # Long phrases first (4-6 words)
                        keypoints.extend(filtered_medium_text)   # Medium phrases second (3-4 words)
                        
                        # Merge overlapping phrases from KeyBERT results
                        if len(keypoints) > 1:
                            # Separate words and phrases for merging
                            words_only = [kp for kp in keypoints if ' ' not in kp]
                            phrases_only = [kp for kp in keypoints if ' ' in kp]
                            
                            # Merge overlapping phrases into longer ones
                            merged_phrases_only = merge_overlapping_phrases(phrases_only)
                            
                            # Recombine with words first, then merged phrases
                            keypoints = words_only + merged_phrases_only
                        
                        # Remove true sub-phrases from the combined results, but preserve long meaningful phrases
                        if len(keypoints) > 1:
                            # Separate words and phrases for filtering
                            words_only_final = [kp for kp in keypoints if ' ' not in kp]
                            phrases_only_final = [kp for kp in keypoints if ' ' in kp]
                            
                            # Preserve long meaningful phrases (like complete ad blocks) before subphrase removal
                            long_meaningful_phrases = []
                            for phrase in phrases_only_final:
                                # Keep phrases that are 8+ words (likely complete thoughts/ad blocks)
                                if len(phrase.split()) >= 8:
                                    long_meaningful_phrases.append(phrase)
                                    print(f"DEBUG: Preserved long meaningful phrase: '{phrase[:100]}...'")
                            
                            # Also preserve medium phrases (5-7 words) that might be meaningful
                            medium_meaningful_phrases = []
                            for phrase in phrases_only_final:
                                if 5 <= len(phrase.split()) < 8:
                                    medium_meaningful_phrases.append(phrase)
                                    print(f"DEBUG: Preserved medium meaningful phrase: '{phrase[:80]}...'")
                            
                            # Remove true sub-phrases from remaining phrases, but be much more lenient
                            remaining_phrases = [kp for kp in phrases_only_final if len(kp.split()) < 5]
                            
                            # Only remove obvious subphrases, keep most content
                            obvious_subphrases = []
                            for phrase in remaining_phrases:
                                # Only remove if it's clearly a subphrase of a longer phrase
                                is_obvious_subphrase = False
                                for longer_phrase in long_meaningful_phrases + medium_meaningful_phrases:
                                    if phrase.lower() in longer_phrase.lower() and len(phrase.split()) < len(longer_phrase.split()) - 2:
                                        is_obvious_subphrase = True
                                        break
                                
                                if not is_obvious_subphrase:
                                    obvious_subphrases.append(phrase)
                            
                            # Recombine: words + long meaningful phrases + medium meaningful phrases + most shorter phrases
                            keypoints = words_only_final + long_meaningful_phrases + medium_meaningful_phrases + obvious_subphrases
                        
                        # If KeyBERT still finds nothing, force fallback
                        if not keypoints:
                            keybert_available = False
                        
                        # Debug: Show what we found
                        print(f"DEBUG: KeyBERT found {len(filtered_keywords_phrases)} long phrases and {len(filtered_keywords_medium)} medium phrases")
                        print(f"DEBUG: After filtering: {len(filtered_phrases)} long phrases and {len(filtered_medium)} medium phrases")
                        print(f"DEBUG: Total keypoints after all processing: {len(keypoints)}")
                        
                        # Show some example phrases that were kept
                        if filtered_phrases:
                            print(f"DEBUG: Example long phrases: {filtered_phrases[:3]}")
                        if filtered_medium:
                            print(f"DEBUG: Example medium phrases: {filtered_medium[:3]}")
                        
                        # Show final keypoints breakdown
                        words_final = [kp for kp in keypoints if ' ' not in kp]
                        phrases_final = [kp for kp in keypoints if ' ' in kp]
                        long_phrases_final = [kp for kp in phrases_final if len(kp.split()) >= 8]
                        print(f"DEBUG: Final breakdown: {len(words_final)} words, {len(phrases_final)} phrases, {len(long_phrases_final)} long phrases (8+ words)")
                        if long_phrases_final:
                            print(f"DEBUG: Example final long phrases: {long_phrases_final[:3]}")
                        
                        # FORCE FALLBACK if KeyBERT didn't find enough meaningful content
                        if len(keypoints) < 20:  # Very aggressive threshold
                            print(f"DEBUG: FORCING FALLBACK - KeyBERT only found {len(keypoints)} keypoints, need at least 20")
                            logging.info(f"FORCE FALLBACK: KeyBERT only found {len(keypoints)} keypoints")
                            keybert_available = False
                        
                        # Clean up audio file after successful transcription
                        try:
                            if os.path.exists(audio_path):
                                # Check user's audio cleanup preference
                                if self.auto_cleanup_audio.get():
                                    # Create central Transcriptions folder in Recordings+transcriptions directory
                                    recordings_root_dir = os.path.dirname(os.path.dirname(audio_path))  # Go up two levels
                                    transcriptions_dir = os.path.join(recordings_root_dir, "Transcriptions")
                                    os.makedirs(transcriptions_dir, exist_ok=True)
                                    
                                    # Extract date and station from the recording folder name
                                    recording_folder_name = os.path.basename(os.path.dirname(audio_path))
                                    # Expected format: YYYYMMDD_HHMMSS_StationName
                                    parts = recording_folder_name.split('_')
                                    
                                    if len(parts) >= 3:
                                        try:
                                            # Extract date (YYYYMMDD)
                                            date_str = parts[0]
                                            date_obj = time.strptime(date_str, '%Y%m%d')
                                            date_folder = time.strftime('%Y-%m-%d', date_obj)
                                            
                                            # Extract station name (everything after the second underscore)
                                            station_name = '_'.join(parts[2:])
                                            # Clean station name for folder use
                                            station_folder = station_name.replace(' ', '_').replace('(', '').replace(')', '')
                                            
                                            # Create date and station subfolders within Transcriptions folder
                                            date_station_dir = os.path.join(transcriptions_dir, f"{date_folder}_{station_folder}")
                                            os.makedirs(date_station_dir, exist_ok=True)
                                            
                                            # Move transcription file to organized subfolder
                                            transcription_filename = os.path.basename(output_txt)
                                            new_transcription_path = os.path.join(date_station_dir, transcription_filename)
                                            
                                            print(f"DEBUG: Organizing transcription by date and station ({date_folder}_{station_folder})")
                                            
                                        except Exception as date_error:
                                            print(f"DEBUG: Could not parse date/station from folder name, using default location: {date_error}")
                                            # Fallback to central Transcriptions folder
                                            new_transcription_path = os.path.join(transcriptions_dir, transcription_filename)
                                    else:
                                        # Fallback if folder name format is unexpected
                                        new_transcription_path = os.path.join(transcriptions_dir, transcription_filename)
                                    
                                    try:
                                        # Copy transcription file to organized location
                                        import shutil
                                        shutil.copy2(output_txt, new_transcription_path)
                                        print(f"DEBUG: Transcription moved to organized location: {os.path.relpath(new_transcription_path, recordings_root_dir)}")
                                        
                                        # Remove original transcription file from recording folder
                                        os.remove(output_txt)
                                        print(f"DEBUG: Original transcription file removed from recording folder")
                                        
                                        # Remove audio file
                                        os.remove(audio_path)
                                        print(f"DEBUG: Audio file cleaned up: {os.path.basename(audio_path)}")
                                        
                                        # Try to remove the original recording folder if it's empty
                                        try:
                                            recording_dir = os.path.dirname(audio_path)
                                            if os.path.exists(recording_dir):
                                                # Check if folder is empty
                                                remaining_items = os.listdir(recording_dir)
                                                if not remaining_items:
                                                    # Remove the entire recording folder
                                                    shutil.rmtree(recording_dir)
                                                    print(f"DEBUG: Empty recording folder removed: {os.path.basename(recording_dir)}")
                                                else:
                                                    print(f"DEBUG: Recording folder kept (contains other items): {os.path.basename(recording_dir)}")
                                        except Exception as folder_cleanup_error:
                                            print(f"DEBUG: Warning - Could not remove recording folder: {folder_cleanup_error}")
                                        
                                        print(f"DEBUG: Transcription saved to central Transcriptions folder: {transcription_filename}")
                                        
                                    except Exception as move_error:
                                        print(f"DEBUG: Warning - Could not move transcription file: {move_error}")
                                        # Fallback: just remove audio file
                                        os.remove(audio_path)
                                        print(f"DEBUG: Audio file cleaned up (fallback): {os.path.basename(audio_path)}")
                                        print(f"DEBUG: Transcription saved: {os.path.basename(output_txt)}")
                                else:
                                    print(f"DEBUG: Audio file preserved (user disabled auto-cleanup): {os.path.basename(audio_path)}")
                            else:
                                print(f"DEBUG: Audio file not found for cleanup: {os.path.basename(audio_path)}")
                        except Exception as cleanup_error:
                            print(f"DEBUG: Warning - Could not clean up audio file: {cleanup_error}")
                        
                except Exception as kb_error:
                    
                    keybert_available = False  # Force fallback
            
            # ALWAYS use fallback if KeyBERT failed or found too few results
            if not keybert_available or (keybert_available and len(keypoints) < 15):  # Lowered threshold from 8 to 15 to trigger fallback more easily
                
                print(f"DEBUG: FALLBACK TRIGGERED - KeyBERT available: {keybert_available}, Keypoints found: {len(keypoints) if 'keypoints' in locals() else 'N/A'}")
                print(f"DEBUG: Transcript length: {len(transcript.split()) if 'transcript' in locals() else 'N/A'} words")
                
                # Log fallback trigger
                logging.info(f"FALLBACK: KeyBERT={keybert_available}, Found={len(keypoints) if 'keypoints' in locals() else 'N/A'}")
                
                # Fallback: most frequent words and phrases with STRICT filtering
                from collections import Counter
                import re
                
                # Reset keypoints for fallback method
                keypoints = []
                
                # Extract single words
                words = re.findall(r'\w+', transcript.lower())
                
                # Use global stopwords for fallback method
                stopwords = DUTCH_STOPWORDS
                filtered_words = [w for w in words if w not in stopwords and len(w) > 3]
                
                # Debug: Show word extraction results
                print(f"DEBUG: Fallback method found {len(filtered_words)} significant words from {len(words)} total words")
                
                # Extract phrases with priority to longer combinations and minimal 2-word phrases
                sentences = re.split(r'[.!?]+', transcript.lower())
                print(f"DEBUG: Fallback processing {len(sentences)} sentences from transcript")
                
                phrases = []
                for sentence_idx, sentence in enumerate(sentences):
                    sentence_words = re.findall(r'\w+', sentence.strip())
                    if len(sentence_words) < 2:  # Skip very short sentences
                        continue
                        
                    print(f"DEBUG: Processing sentence {sentence_idx+1}: '{sentence[:100]}...' ({len(sentence_words)} words)")
                    
                    # Generate 5-word phrases first (highest priority)
                    for i in range(len(sentence_words) - 4):
                        word1, word2, word3, word4, word5 = sentence_words[i], sentence_words[i+1], sentence_words[i+2], sentence_words[i+3], sentence_words[i+4]
                        stopword_count = sum(1 for word in [word1, word2, word3, word4, word5] if word in stopwords)
                        if stopword_count <= 2:  # Allow max 2 stopwords for 5-word phrases
                            non_stopwords = [w for w in [word1, word2, word3, word4, word5] if w not in stopwords]
                            if len(non_stopwords) >= 3 and all(len(w) >= 3 for w in non_stopwords):
                                phrase = f"{word1} {word2} {word3} {word4} {word5}"
                                phrases.append(phrase)
                                print(f"DEBUG: Added 5-word phrase: '{phrase}'")
                    
                    # Generate 4-word phrases (high priority) - MORE LENIENT
                    for i in range(len(sentence_words) - 3):
                        word1, word2, word3, word4 = sentence_words[i], sentence_words[i+1], sentence_words[i+2], sentence_words[i+3]
                        stopword_count = sum(1 for word in [word1, word2, word3, word4] if word in stopwords)
                        if stopword_count <= 3:  # Allow max 3 stopwords for 4-word phrases (more lenient)
                            non_stopwords = [w for w in [word1, word2, word3, word4] if w not in stopwords]
                            if len(non_stopwords) >= 1 and all(len(w) >= 2 for w in non_stopwords):  # More lenient length requirement
                                phrase = f"{word1} {word2} {word3} {word4}"
                                phrases.append(phrase)
                                if len(phrases) <= 10:  # Only show first 10 to avoid spam
                                    print(f"DEBUG: Added 4-word phrase: '{phrase}'")
                    
                    # Generate 3-word phrases (medium priority) - MORE LENIENT
                    for i in range(len(sentence_words) - 2):
                        word1, word2, word3 = sentence_words[i], sentence_words[i+1], sentence_words[i+2]
                        stopword_count = sum(1 for word in [word1, word2, word3] if word in stopwords)
                        if stopword_count <= 2:  # Allow max 2 stopwords for 3-word phrases (more lenient)
                            non_stopwords = [w for w in [word1, word2, word3] if w not in stopwords]
                            if len(non_stopwords) >= 1 and all(len(w) >= 2 for w in non_stopwords):  # More lenient length requirement
                                phrase = f"{word1} {word2} {word3}"
                                phrases.append(phrase)
                                if len(phrases) <= 20:  # Only show first 20 to avoid spam
                                    print(f"DEBUG: Added 3-word phrase: '{phrase}'")
                    
                    # Generate 2-word phrases last (lowest priority, but more generous)
                    if len(phrases) < 30:  # Allow more 2-word phrases to ensure coverage
                        for i in range(len(sentence_words) - 1):
                            word1, word2 = sentence_words[i], sentence_words[i+1]
                            stopword_count = sum(1 for word in [word1, word2] if word in stopwords)
                            if stopword_count <= 1:  # Allow max 1 stopword for 2-word phrases
                                non_stopword = word1 if word1 not in stopwords else word2
                                if len(non_stopword) >= 3:  # Only if non-stopword is meaningful
                                    phrase = f"{word1} {word2}"
                                    phrases.append(phrase)
                                    if len(phrases) >= 55:  # Increased limit for better coverage
                                        break
                
                
                
                # Combine single words and phrases, get most common
                all_terms = filtered_words + phrases
                
                # Debug: Show phrase extraction results
                print(f"DEBUG: Fallback method found {len(phrases)} phrases total")
                if phrases:
                    phrase_lengths = [len(p.split()) for p in phrases]
                    print(f"DEBUG: Phrase lengths: 2w={phrase_lengths.count(2)}, 3w={phrase_lengths.count(3)}, 4w={phrase_lengths.count(4)}, 5w={phrase_lengths.count(5)}")
                
                # Merge overlapping phrases before counting
                if len(all_terms) > 1:
                    words_only = [term for term in all_terms if ' ' not in term]
                    phrases_only = [term for term in all_terms if ' ' in term]
                    
                    # Merge overlapping phrases into longer ones
                    merged_phrases_only = merge_overlapping_phrases(phrases_only)
                    
                    # Recombine
                    all_terms = words_only + merged_phrases_only
                
                # Remove true sub-phrases before counting
                if len(all_terms) > 1:
                    words_only_final = [term for term in all_terms if ' ' not in term]
                    phrases_only_final = [term for term in all_terms if ' ' in term]
                    
                    # Remove true sub-phrases from phrases
                    filtered_phrases_final = remove_true_subphrases(phrases_only_final)
                    
                    # Recombine
                    all_terms = words_only_final + filtered_phrases_final
                
                term_counts = Counter(all_terms)
                
                # Get top terms - 20 significant words and more phrases
                top_single_words = [w for w, _ in term_counts.most_common(100) if ' ' not in w][:20]  # Increased to 20
                # Include phrases that appear multiple times (more reliable and significant)
                top_phrases = [p for p, count in term_counts.most_common(300) if ' ' in p and count >= 1][:35]  # At least 1 occurrence, more phrases
                

                
                # Ensure we have a good mix of words and phrases
                if len(top_single_words) < 5:
                    # Look for more single words in the most common terms
                    all_single_words = [w for w, _ in term_counts.most_common(200) if ' ' not in w and len(w) > 3]
                    top_single_words = all_single_words[:20]
                
                if len(top_phrases) < 10:
                    # Look for more phrases in the most common terms, prioritizing longer ones
                    all_phrases = [p for p, count in term_counts.most_common(300) if ' ' in p and count >= 2]
                    # Sort by length (longer first) and then by frequency
                    all_phrases.sort(key=lambda x: (len(x[0].split()), x[1]), reverse=True)
                    top_phrases = all_phrases[:25]
                    
                    # If still not enough, also include phrases that appear 1+ times but are shorter
                    if len(top_phrases) < 15:
                        multiple_occurrence_phrases = [p for p, count in term_counts.most_common(400) if ' ' in p and count >= 1 and len(p.split()) >= 3]
                        multiple_occurrence_phrases.sort(key=lambda x: (len(x.split()), x[1]), reverse=True)
                        top_phrases.extend(multiple_occurrence_phrases[:15])
                
                keypoints = top_single_words + top_phrases
                print(f"DEBUG: Fallback keypoints created: {len(keypoints)} total (words: {len(top_single_words)}, phrases: {len(top_phrases)})")
                if keypoints:
                    print(f"DEBUG: First 5 fallback keypoints: {keypoints[:5]}")
                
            
            # Final fallback: if no keypoints found at all, use most common words regardless of stopwords
            if not keypoints and transcript.strip():
                print(f"DEBUG: NO KEYPOINTS FOUND - Using ultimate fallback method")
                print(f"DEBUG: This should not happen if fallback mechanism is working properly")
                logging.warning(f"ULTIMATE FALLBACK: No keypoints found, using emergency method")
                
                # Import required modules if not already imported
                if 're' not in globals():
                    import re
                if 'Counter' not in globals():
                    from collections import Counter
                
                # Extract words if not already done
                if 'words' not in locals():
                    words = re.findall(r'\w+', transcript.lower())
                
                # Use all words longer than 2 characters, excluding stopwords
                fallback_words = [w for w in words if w not in stopwords and len(w) > 2]
                fallback_counts = Counter(fallback_words)
                keypoints = [w for w, _ in fallback_counts.most_common(20)]
                print(f"DEBUG: Final fallback created {len(keypoints)} keypoints from words >2 chars")
                
                # If fallback also finds nothing, use all words longer than 3 characters
                if not keypoints:
                    all_words = [w for w in words if len(w) > 3]
                    all_counts = Counter(all_words)
                    keypoints = [w for w, _ in all_counts.most_common(15)]
                    print(f"DEBUG: Ultimate fallback created {len(keypoints)} keypoints from words >3 chars")
            
            # Find when key points are mentioned
            print(f"DEBUG: Processing {len(keypoints)} final keypoints for timestamp analysis")
            if keypoints:
                print(f"DEBUG: Final keypoints: {keypoints[:10]}")
            
            try:
                keypoint_times = {kp: [] for kp in keypoints}
                
                for seg in all_segments:
                    for kp in keypoints:
                        if kp.lower() in seg["text"].lower():
                            keypoint_times[kp].append(seg["start"])
                            
            except Exception as kp_error:
                keypoint_times = {}
            
            # Deduplicate phrases to remove exact duplicates while preserving timestamps
            try:
                if keypoint_times:
                    # Convert to list of tuples for deduplication
                    phrases_with_times = [(kp, times) for kp, times in keypoint_times.items() if times]
                    
                    # Apply deduplication
                    deduplicated_phrases = deduplicate_phrases(phrases_with_times)
                    
                    # Convert back to dictionary
                    keypoint_times = {kp: times for kp, times in deduplicated_phrases}
                    
                    print(f"DEBUG: Deduplication complete. Reduced from {len(phrases_with_times)} to {len(deduplicated_phrases)} unique phrases")
            except Exception as dedup_error:
                print(f"DEBUG: Deduplication failed: {dedup_error}")
                # Continue with original keypoint_times if deduplication fails
            
            # Output to file and GUI - save in same folder as recording
            output_txt = None
            try:
                output_txt = os.path.splitext(audio_path)[0] + "_transcription.txt"
                
                with open(output_txt, "w", encoding="utf-8") as f:
                    f.write("--- Transcript ---\n")
                    for seg in all_segments:
                        try:
                            start_time = seg.get('start', 0)
                            text = seg.get('text', '')
                            f.write(f"[{start_time:.1f}s] {text}\n")
                        except Exception as seg_error:
                            # Skip problematic segments
                            continue
                    
                    f.write("\n--- Key Talking Points & Phrases ---\n")
                    # Separate single words and phrases for better organization
                    try:
                        single_words = [(kp, times) for kp, times in keypoint_times.items() if ' ' not in kp and times]
                        phrases = [(kp, times) for kp, times in keypoint_times.items() if ' ' in kp and times]
                    except Exception as sort_error:
                        single_words = []
                        phrases = []
                    
                    if single_words:
                        f.write("\n📝 Most Mentioned Words (Top 20):\n")
                        for i, (kp, times) in enumerate(single_words, 1):
                            try:
                                f.write(f"  {i:2d}. {kp}: {', '.join([f'{t:.1f}s' for t in times])}\n")
                            except Exception as write_error:
                                continue
                    else:
                        f.write("\n📝 Most Mentioned Words (Top 20):\n  • No significant words encountered\n")
                    
                    if phrases:
                        f.write("\n💬 Most Mentioned Phrases (Improved filtering - more lenient for better coverage):\n")
                        for i, (kp, times) in enumerate(phrases, 1):
                            try:
                                f.write(f"  {i:2d}. \"{kp}\": {', '.join([f'{t:.1f}s' for t in times])}\n")
                            except Exception as write_error:
                                continue
                    else:
                        f.write("\n💬 Most Mentioned Phrases (Improved filtering - more lenient for better coverage):\n  • No significant phrases encountered\n")
                
            except Exception as file_error:
                print(f"Error writing output file: {file_error}")
                output_txt = None
            
            # Clean up audio file after successful transcription (both KeyBERT and fallback methods)
            if output_txt and os.path.exists(output_txt):  # Only cleanup if transcription file was successfully created
                try:
                    if os.path.exists(audio_path):
                        # Check user's audio cleanup preference
                        if self.auto_cleanup_audio.get():
                            # Create central Transcriptions folder in Recordings+transcriptions directory
                            recordings_root_dir = os.path.dirname(os.path.dirname(audio_path))  # Go up two levels
                            transcriptions_dir = os.path.join(recordings_root_dir, "Transcriptions")
                            os.makedirs(transcriptions_dir, exist_ok=True)
                            
                            # Extract date and station from the recording folder name
                            recording_folder_name = os.path.basename(os.path.dirname(audio_path))
                            # Expected format: YYYYMMDD_HHMMSS_StationName
                            parts = recording_folder_name.split('_')
                            
                            if len(parts) >= 3:
                                try:
                                    # Extract date (YYYYMMDD)
                                    date_str = parts[0]
                                    date_obj = time.strptime(date_str, '%Y%m%d')
                                    date_folder = time.strftime('%Y-%m-%d', date_obj)
                                    
                                    # Extract station name (everything after the second underscore)
                                    station_name = '_'.join(parts[2:])
                                    # Clean station name for folder use
                                    station_folder = station_name.replace(' ', '_').replace('(', '').replace(')', '')
                                    
                                    # Create date and station subfolders
                                    date_station_dir = os.path.join(transcriptions_dir, f"{date_folder}_{station_folder}")
                                    os.makedirs(date_station_dir, exist_ok=True)
                                    
                                    # Move transcription file to organized subfolder
                                    transcription_filename = os.path.basename(output_txt)
                                    new_transcription_path = os.path.join(date_station_dir, transcription_filename)
                                    
                                    print(f"DEBUG: Organizing transcription by date and station ({date_folder}_{station_folder})")
                                    
                                except Exception as date_error:
                                    print(f"DEBUG: Could not parse date/station from folder name, using default location: {date_error}")
                                    # Fallback to central Transcriptions folder
                                    new_transcription_path = os.path.join(transcriptions_dir, transcription_filename)
                            else:
                                # Fallback if folder name format is unexpected
                                new_transcription_path = os.path.join(transcriptions_dir, transcription_filename)
                            
                            try:
                                # Copy transcription file to organized location
                                import shutil
                                shutil.copy2(output_txt, new_transcription_path)
                                print(f"DEBUG: Transcription moved to organized location: {os.path.relpath(new_transcription_path, recordings_root_dir)}")
                                
                                # Remove original transcription file from recording folder
                                os.remove(output_txt)
                                print(f"DEBUG: Original transcription file removed from recording folder")
                                
                                # Remove audio file
                                os.remove(audio_path)
                                print(f"DEBUG: Audio file cleaned up: {os.path.basename(audio_path)}")
                                
                                # Try to remove the original recording folder if it's empty
                                try:
                                    recording_dir = os.path.dirname(audio_path)
                                    if os.path.exists(recording_dir):
                                        # Check if folder is empty
                                        remaining_items = os.listdir(recording_dir)
                                        if not remaining_items:
                                            # Remove the entire recording folder
                                            shutil.rmtree(recording_dir)
                                            print(f"DEBUG: Empty recording folder removed: {os.path.basename(recording_dir)}")
                                        else:
                                            print(f"DEBUG: Recording folder kept (contains other items): {os.path.basename(recording_dir)}")
                                except Exception as folder_cleanup_error:
                                    print(f"DEBUG: Warning - Could not remove recording folder: {folder_cleanup_error}")
                                
                                print(f"DEBUG: Transcription saved to organized location: {os.path.basename(transcription_filename)}")
                                
                            except Exception as move_error:
                                print(f"DEBUG: Warning - Could not move transcription file: {move_error}")
                                # Fallback: just remove audio file
                                os.remove(audio_path)
                                print(f"DEBUG: Audio file cleaned up (fallback): {os.path.basename(audio_path)}")
                                print(f"DEBUG: Transcription saved: {os.path.basename(output_txt)}")
                        else:
                            print(f"DEBUG: Audio file preserved (user disabled auto-cleanup): {os.path.basename(audio_path)}")
                            print(f"DEBUG: Transcription saved: {os.path.basename(output_txt)}")
                    else:
                        print(f"DEBUG: Audio file not found for cleanup: {os.path.basename(audio_path)}")
                except Exception as cleanup_error:
                    print(f"DEBUG: Warning - Could not clean up audio file: {cleanup_error}")
            else:
                print(f"DEBUG: Skipping audio cleanup - transcription file not created successfully")
            
            # Show in GUI (in main thread)
            try:
                summary = "--- Key Talking Points & Phrases ---\n"
                # Separate single words and phrases for better organization
                try:
                    single_words = [(kp, times) for kp, times in keypoint_times.items() if ' ' not in kp and times]
                    phrases = [(kp, times) for kp, times in keypoint_times.items() if ' ' in kp and times]
                except Exception as sort_error:
                    single_words = []
                    phrases = []
                
                if single_words:
                    summary += "\n📝 Most Mentioned Words (Top 20):\n"
                    for i, (kp, times) in enumerate(single_words, 1):
                        try:
                            summary += f"  {i:2d}. {kp}: {', '.join([f'{t:.1f}s' for t in times])}\n"
                        except Exception as format_error:
                            continue
                else:
                    summary += "\n📝 Most Mentioned Words (Top 20):\n  • No significant words encountered\n"
                
                if phrases:
                    summary += "\n💬 Most Mentioned Phrases (Improved filtering - more lenient for better coverage):\n"
                    for i, (kp, times) in enumerate(phrases, 1):
                        try:
                            summary += f"  {i:2d}. \"{kp}\": {', '.join([f'{t:.1f}s' for t in times])}\n"
                        except Exception as format_error:
                            continue
                else:
                    summary += "\n💬 Most Mentioned Phrases (Improved filtering - more lenient for better coverage):\n  • No significant phrases encountered\n"
                
            except Exception as summary_error:
                summary = "--- Key Talking Points & Phrases ---\n\nError occurred while processing keypoints."
            
            def show_results():
                # Check if we found enough content
                total_keypoints = len(single_words) + len(phrases)
                print(f"DEBUG: FINAL RESULTS - Total keypoints: {total_keypoints} (words: {len(single_words)}, phrases: {len(phrases)})")
                
                # Log final results
                logging.info(f"RESULTS: {total_keypoints} keypoints ({len(single_words)} words, {len(phrases)} phrases)")
                
                if total_keypoints < 10:
                    print(f"DEBUG: WARNING - Very few keypoints found, this might indicate a problem")
                    logging.warning(f"LOW RESULTS: Only {total_keypoints} keypoints found")
                    self.status_label.config(text=f"Transcription complete but found only {total_keypoints} key points. See {output_txt}")
                    messagebox.showwarning("Limited Results", f"Only {total_keypoints} significant key points found. This might indicate:\n- Audio quality issues\n- Very short speech content\n- Transcription problems\n\nCheck the output file for details.")
                else:
                    print(f"DEBUG: SUCCESS - Adequate keypoints found")
                    logging.info(f"SUCCESS: Adequate keypoints found")
                    self.status_label.config(text=f"Transcription complete. Found {total_keypoints} key points. See {output_txt}")
                    messagebox.showinfo("Key Talking Points", summary)
                
                # Open the folder containing the recording and transcription
                recording_dir = os.path.dirname(audio_path)
                try:
                    if sys.platform.startswith('win'):
                        os.startfile(recording_dir)
                    elif sys.platform.startswith('darwin'):  # macOS
                        subprocess.run(['open', recording_dir])
                    else:  # Linux
                        subprocess.run(['xdg-open', recording_dir])
                except Exception as e:
                    # If opening folder fails, just show a message
                    try:
                        messagebox.showinfo("Folder Location", f"Files saved in: {recording_dir}")
                    except Exception as msg_error:
                        # If even the message box fails, just update status
                        self.status_label.config(text=f"Files saved in: {recording_dir}")
            
            self.master.after(0, show_results)
            
            # Log recording completion
            logging.info(f"RECORDING COMPLETE: {recording_name} - Found {len(single_words) + len(phrases)} keypoints")
            
        except Exception as e:
            # Capture the exception in the closure
            error_msg = str(e)
            logging.error(f"TRANSCRIPTION ERROR: {error_msg}")
            
            def show_error_safe():
                try:
                    messagebox.showerror("Transcription Error", f"An error occurred during transcription: {error_msg}")
                    self.status_label.config(text="Transcription failed")
                except Exception as gui_error:
                    # If message box fails, just update status
                    try:
                        self.status_label.config(text="Transcription failed")
                    except Exception:
                        # Ultimate fallback - do nothing
                        pass
            
            self.master.after(0, show_error_safe)
        finally:
            # Restore original subprocess.Popen
            subprocess.Popen = original_popen

    def transcribe_recent_recordings(self):
        """Transcribe the last 3 untranscribed audio recordings"""
        try:
            # Find the recordings directory
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            recordings_dir = os.path.join(app_dir, "Recordings+transcriptions")
            
            if not os.path.exists(recordings_dir):
                messagebox.showinfo("No Recordings", "No recordings directory found. Please record some audio first.")
                return
            
            # Find all MP3 files in recordings directory and subdirectories
            mp3_files = []
            for root, dirs, files in os.walk(recordings_dir):
                for file in files:
                    if file.endswith('.mp3') and file.startswith('radio_recording_'):
                        file_path = os.path.join(root, file)
                        
                        # Check if transcription file already exists in organized Transcriptions subfolders
                        recording_folder_name = os.path.basename(os.path.dirname(file_path))
                        parts = recording_folder_name.split('_')
                        
                        transcription_found = False
                        if len(parts) >= 3:
                            try:
                                # Check organized location first
                                date_str = parts[0]
                                date_obj = time.strptime(date_str, '%Y%m%d')
                                date_folder = time.strftime('%Y-%m-%d', date_obj)
                                station_name = '_'.join(parts[2:])
                                station_folder = station_name.replace(' ', '_').replace('(', '').replace(')', '')
                                
                                transcriptions_dir = os.path.join(recordings_dir, "Transcriptions")
                                organized_transcription_path = os.path.join(transcriptions_dir, f"{date_folder}_{station_folder}", 
                                                                        os.path.splitext(os.path.basename(file_path))[0] + "_transcription.txt")
                                
                                if os.path.exists(organized_transcription_path):
                                    transcription_found = True
                                    
                            except Exception:
                                pass
                        
                        # Also check old locations for backward compatibility
                        if not transcription_found:
                            # Check central Transcriptions folder
                            transcriptions_dir = os.path.join(recordings_dir, "Transcriptions")
                            central_transcription_file = os.path.join(transcriptions_dir, 
                                                                   os.path.splitext(os.path.basename(file_path))[0] + "_transcription.txt")
                            
                            # Check old location in recording folder
                            old_transcription_file = os.path.splitext(file_path)[0] + "_transcription.txt"
                            
                            if os.path.exists(central_transcription_file) or os.path.exists(old_transcription_file):
                                transcription_found = True
                        
                        if not transcription_found:
                            mp3_files.append((file_path, os.path.getmtime(file_path)))
            
            if not mp3_files:
                messagebox.showinfo("No Untranscribed Files", "All recorded audio files have already been transcribed.")
                return
            
            # Sort by modification time (newest first) and take last 3
            mp3_files.sort(key=lambda x: x[1], reverse=True)
            recent_files = mp3_files[:3]
            
            # Show confirmation dialog with file details
            confirm_window = tk.Toplevel(self.master)
            confirm_window.title("Transcribe Recent Recordings")
            confirm_window.geometry("500x400")
            confirm_window.resizable(False, False)
            confirm_window.transient(self.master)
            confirm_window.grab_set()
            
            # Center the window
            confirm_window.geometry("+%d+%d" % (self.master.winfo_rootx() + 100, self.master.winfo_rooty() + 100))
            
            # Main frame
            main_frame = ttk.Frame(confirm_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            title_label = ttk.Label(main_frame, text="Transcribe Recent Recordings", font=('Arial', 14, 'bold'))
            title_label.pack(pady=(0, 20))
            
            # Description
            desc_label = ttk.Label(main_frame, text="The following untranscribed audio files were found:", 
                                  font=('Arial', 10), wraplength=450, justify='center')
            desc_label.pack(pady=(0, 20))
            
            # File list frame
            file_frame = ttk.Frame(main_frame)
            file_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
            
            # Create text widget with scrollbar for file list
            text_frame = ttk.Frame(file_frame)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 9), 
                                 padx=10, pady=10, relief=tk.SUNKEN, borderwidth=1, height=8)
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Insert file information
            file_info = ""
            for i, (file_path, mtime) in enumerate(recent_files, 1):
                filename = os.path.basename(file_path)
                folder = os.path.basename(os.path.dirname(file_path))
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                
                file_info += f"{i}. {filename}\n"
                file_info += f"   Folder: {folder}\n"
                file_info += f"   Size: {size_mb:.1f} MB\n"
                file_info += f"   Date: {date_str}\n\n"
            
            text_widget.insert(tk.END, file_info)
            text_widget.config(state=tk.DISABLED)  # Make read-only
            
            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(pady=20)
            
            def start_transcription():
                confirm_window.destroy()
                self.process_recent_recordings(recent_files)
            
            def cancel():
                confirm_window.destroy()
            
            # Buttons
            ttk.Button(button_frame, text="Start Transcription", command=start_transcription, 
                      style='Accent.TButton').pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)
            
            # Focus on the window
            confirm_window.focus_set()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to find recent recordings: {str(e)}")

    def process_recent_recordings(self, recent_files):
        """Process the selected recent recordings for transcription"""
        try:
            # Show progress dialog
            progress_window = tk.Toplevel(self.master)
            progress_window.title("Transcribing Recent Recordings")
            progress_window.geometry("400x200")
            progress_window.resizable(False, False)
            progress_window.transient(self.master)
            progress_window.grab_set()
            
            # Center the window
            progress_window.geometry("+%d+%d" % (self.master.winfo_rootx() + 150, self.master.winfo_rooty() + 150))
            
            # Main frame
            main_frame = ttk.Frame(progress_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            title_label = ttk.Label(main_frame, text="Transcribing Recent Recordings", font=('Arial', 12, 'bold'))
            title_label.pack(pady=(0, 20))
            
            # Progress label
            progress_label = ttk.Label(main_frame, text="Preparing transcription...", font=('Arial', 10))
            progress_label.pack(pady=(0, 20))
            
            # Progress bar
            progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
            progress_bar.pack(fill=tk.X, pady=(0, 20))
            progress_bar.start()
            
            # Status label
            status_label = ttk.Label(main_frame, text="", font=('Arial', 9), wraplength=350)
            status_label.pack()
            
            def update_progress(message):
                progress_label.config(text=message)
                progress_window.update()
            
            def update_status(message):
                status_label.config(text=message)
                progress_window.update()
            
            # Start transcription in background thread
            def transcription_worker():
                try:
                    for i, (file_path, mtime) in enumerate(recent_files, 1):
                        filename = os.path.basename(file_path)
                        update_progress(f"Transcribing file {i}/{len(recent_files)}: {filename}")
                        update_status("This may take several minutes depending on file size...")
                        
                        # Start transcription
                        self.master.after(0, lambda: self.status_label.config(
                            text=f"Transcribing recent recording {i}/{len(recent_files)}: {filename}"))
                        
                        # Call transcription function
                        self.transcribe_and_extract(file_path)
                        
                        # Wait a bit between files
                        time.sleep(2)
                    
                    # All done
                    self.master.after(0, lambda: self.status_label.config(
                        text=f"Completed transcription of {len(recent_files)} recent recordings"))
                    
                    # Close progress window and show completion message
                    self.master.after(0, lambda: progress_window.destroy())
                    self.master.after(0, lambda: messagebox.showinfo("Transcription Complete", 
                        f"Successfully transcribed {len(recent_files)} recent recordings!\n\n"
                        "Check the output files in their respective folders."))
                    
                except Exception as e:
                    error_msg = f"Error during transcription: {str(e)}"
                    self.master.after(0, lambda: progress_window.destroy())
                    self.master.after(0, lambda: messagebox.showerror("Transcription Error", error_msg))
                    self.master.after(0, lambda: self.status_label.config(text="Recent transcription failed"))
            
            # Start worker thread
            transcription_thread = threading.Thread(target=transcription_worker, daemon=True)
            transcription_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start transcription: {str(e)}")

    def toggle_listen(self):
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()



if __name__ == "__main__":
    try:
        # Get OpenAI API key first
        api_key = get_openai_api_key()
        if not api_key:
            print("No API key provided. Exiting.")
            sys.exit(1)
        
        root = tk.Tk()
        app = RadioRecorderApp(root)
        root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_listening(), root.destroy()))
        root.mainloop()
    except Exception as main_error:
        print(f"Critical error in main: {main_error}")
        # Try to show error in console if GUI fails
        try:
            import traceback
            traceback.print_exc()
        except:
            pass
