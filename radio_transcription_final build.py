# To make this script an executable, run:
#   pyinstaller radio_transcription_final.spec
# (Make sure ffmpeg.exe and ffplay.exe are in the bin/ subdirectory)
#
# This will create a professional executable with:
# - Bluvia branding and logo
# - Professional icon (Bluebird app icon 2.ico)
# - Enhanced GUI with menu system
# - Help and About dialogs
# - All Bluvia images included
#
# The executable will be named "Radio_Transcription_Tool_Bluvia.exe"

import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import time
import openai

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

# Global stopwords definition - more robust and comprehensive
DUTCH_STOPWORDS = {
    'de', 'het', 'een', 'en', 'van', 'in', 'te', 'dat', 'die', 'is', 'op', 'met', 'als', 'voor', 'aan', 'er', 'door', 'om', 'tot', 'ook', 'maar', 'uit', 'bij', 'over', 'nog', 'naar', 'dan', 'of', 'je', 'ik', 'ze', 'zij', 'hij', 'wij', 'jij', 'u', 'hun', 'ons', 'mijn', 'jouw', 'zijn', 'haar', 'hun', 'dit', 'dat', 'deze', 'die',
    'niet', 'hebben', 'daar', 'heeft', 'eigenlijk', 'heel', 'gaat', 'gaan', 'toch', 'want', 'elkaar', 'even', 'waar', 'natuurlijk', 'veel', 'meer', 'moet', 'kunnen', 'wordt', 'gewoon', 'worden', 'echt', 'komen', 'komt', 'hier', 'niks', 'gevonden',
    'twee', 'drie', 'vier', 'vijf', 'zes', 'zeven', 'acht', 'negen', 'tien', 'goed', 'doen', 'moeten', 'maken', 'soort', 'onze', 'omdat', 'kwam', 'iemand', 'blijven', 'vaak', 'jaar', 'denk', 'weer', 'staat', 'waren', 'geen', 'vandaag', 'bijvoorbeeld', 'zeggen', 'grote', 'tijd', 'muziek', 'iets', 'eigen', 'vooral', 'toen', 'eerste', 'tweede', 'derde', 'vierde', 'vijfde',
    'zesde', 'zevende', 'achtste', 'negende', 'tiende', 'vind', 'laten', 'altijd', 'andere', 'alle', 'woord', 'gebruiken', 'moment', 'woord', 'zelf', 'zien', 'jullie', 'terug', 'kijken', 'hebt', 'weet', 'hele', 'dingen', 'helemaal', 'verschillende', 'inderdaad', 'beter', 'misschien', 'manier', 'dacht', 'uiteindelijk',
    'beetje', 'ging', 'gemaakt', 'vanuit', 'werd', 'vond', 'best', 'alleen', 'groep', 'honderd', 'iedereen', 'weken', 'groot', 'allemaal', 'gedaan', 'lang', 'zeker', 'meter', 'dagen', 'gegeven', 'leuk', 'keer', 'zaten', 'mooi', 'deden', 'willen', 'begint', 'ervoor', 'minder', 'weten', 'onder', 'steeds', 'stellen',
    'anders', 'alles', 'hadden', 'zegt', 'juist', 'oude', 'bent', 'vindt', 'volgend', 'laatste', 'minuten', 'vanaf', 'tegen', 'samen', 'laag', 'zoals', 'tevoren', 'eerder', 'tegen', 'zoals', 'steeds', 'maakt', 'vorig', 'nieuwe', 'ligt', 'jonge', 'staan', 'zich', 'ziet', 'kijk', 'week', 'eens', 'klein',
    'volgende', 'lijkt', 'tussen', 'stuk', 'geworden', 'dus', 'zo', 'snel', 'elke', 'we', 'it', 'have', 'had', 'you', 'ja', 'we', 'ben', 'zo', 'kan', 'wel', 'nou', 'elke', 'waarom', 'denken', 'leren', 'paar', 'soms', 'kan', 'best', 'wat', 'was', 'er', 'wil', 'zeer', 'zeg', 'hem', 'zie', 'heb'
}

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
    Improved to favor longer, more meaningful phrases and reduce excessive 2-word phrases.
    
    Strategy:
    - Much more lenient stopword filtering to keep meaningful longer phrases
    - Post-processing to limit 2-word phrases to maximum 40% of total
    - Prioritizes 3+ word phrases for better content extraction
    
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
                
                # MODERATE filtering to eliminate meaningless phrases while keeping meaningful ones
                if total_words >= 6:
                    # Allow max 2 stopwords for very long phrases
                    max_allowed = 2.0 / total_words
                elif total_words == 5:
                    # Allow max 2 stopwords for 5-word phrases
                    max_allowed = 2.0 / 5.0
                elif total_words == 4:
                    # Allow max 2 stopwords for 4-word phrases
                    max_allowed = 2.0 / 4.0
                elif total_words == 3:
                    # Allow max 1 stopword for 3-word phrases
                    max_allowed = 1.0 / 3.0
                else:
                    # Allow max 1 stopword for 2-word phrases (but ensure non-stopword is meaningful)
                    max_allowed = 1.0 / 2.0
                
                # Apply the strict filtering
                if total_words > 0 and stopword_count / total_words <= max_allowed:
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
    
    # Post-process to reduce excessive 2-word phrases and prioritize longer ones
    try:
        if len(filtered_phrases) > 20:  # Only if we have many phrases
            # Count phrase lengths
            phrase_lengths = [len(phrase.split()) for phrase in filtered_phrases]
            
            # If we have too many 2-word phrases, filter some out
            two_word_count = phrase_lengths.count(2)
            if two_word_count > len(filtered_phrases) * 0.4:  # Reduced from 60% to 40%
                # Keep only the best 2-word phrases and prioritize longer ones
                long_phrases = [p for p in filtered_phrases if len(p.split()) >= 3]
                two_word_phrases = [p for p in filtered_phrases if len(p.split()) == 2]
                
                # Limit 2-word phrases to maximum 30% of total (reduced from 40%)
                max_two_word = min(len(filtered_phrases) * 0.3, len(two_word_phrases))
                if len(two_word_phrases) > max_two_word:
                    two_word_phrases = two_word_phrases[:int(max_two_word)]
                
                # Combine with priority to longer phrases
                filtered_phrases = long_phrases + two_word_phrases
    except Exception:
        pass  # If post-processing fails, return original filtered phrases
    
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
        master.title("Radio Transcription Tool v3.0 - Powered by Bluvia")
        
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
            if key.startswith('sk-'):
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
        footer_text = ttk.Label(footer_frame, text="Powered by Bluvia - Advanced Audio Processing Solutions", 
                               font=('Arial', 9), foreground='#666666')
        footer_text.pack()
        
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
        title_label = ttk.Label(main_frame, text="Radio Transcription Tool v3.0", 
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
• Intelligent keyword and phrase extraction
• Support for multiple audio formats
• Professional output formatting"""
        
        features_label = ttk.Label(main_frame, text=features_text, font=('Arial', 9), justify='left')
        features_label.pack(pady=(0, 15))
        
        # Powered by
        powered_label = ttk.Label(main_frame, text="Powered by Bluvia Technology", 
                                font=('Arial', 12, 'bold'), foreground='#2E86AB')
        powered_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="Advanced Audio Processing Solutions", 
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
        if AudioSegment is None:
            # Use after() to schedule GUI updates in the main thread
            self.master.after(0, lambda: messagebox.showerror("Dependency Error", "pydub is not installed. Please install it with 'pip install pydub'."))
            return
        
        # Update status in main thread
        self.master.after(0, lambda: self.status_label.config(text="Transcribing audio..."))
        
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
            # Split audio into 10-minute chunks (600000 ms)
            chunk_length_ms = 10 * 60 * 1000
            
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
                transcript = " ".join([seg.get("text", "") for seg in all_segments if seg and isinstance(seg, dict)])
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
            
            if keybert_available:
                try:
                    # Check if transcript is too short for KeyBERT
                    if len(transcript.split()) < 50:
                        keybert_available = False
                    else:
                        # Use global stopwords for KeyBERT filtering
                        stopwords = DUTCH_STOPWORDS
                        
                        # Try KeyBERT for phrases first - without stopwords to get more results
                        kw_model = KeyBERT()
                        keywords_phrases = kw_model.extract_keywords(transcript, keyphrase_ngram_range=(2,5), top_n=30)
                        
                        # Try KeyBERT for single words separately - without stopwords to get more results
                        keywords_words = kw_model.extract_keywords(transcript, keyphrase_ngram_range=(1,1), top_n=20)
                        

                        
                        
                        # Combine results with smart filtering
                        keypoints = []
                        
                        # Use the full stopwords list for filtering
                        common_stopwords = DUTCH_STOPWORDS
                        
                        filtered_words = filter_words_robust(keywords_words, common_stopwords)
                        
                        # Filter phrases to remove those with too many stopwords
                        filtered_phrases = filter_phrases_robust(keywords_phrases, common_stopwords)
                        
                        # If filtering removes too many words, be less strict
                        if len(filtered_words) < 5 and len(keywords_words) > 0:
                            # Only filter out the most basic stopwords
                            basic_stopwords = {'de', 'het', 'een', 'en', 'van', 'in', 'te', 'dat', 'die', 'is', 'op', 'met', 'als', 'voor', 'aan', 'er', 'door', 'om', 'tot', 'ook', 'maar', 'uit', 'bij', 'over', 'nog', 'naar', 'dan', 'of', 'je', 'ik', 'ze', 'zij', 'hij', 'wij', 'jij', 'u', 'hun', 'ons', 'mijn', 'jouw', 'zijn', 'haar', 'hun', 'dit', 'dat', 'deze', 'die'}
                            filtered_words = filter_words_robust(keywords_words, basic_stopwords)
                        
                        keypoints.extend(filtered_words)
                        keypoints.extend(filtered_phrases)
                        
                        # If KeyBERT still finds nothing, force fallback
                        if not keypoints:
                            keybert_available = False
                        
                except Exception as kb_error:
                    keybert_available = False  # Force fallback
            else:
                # Fallback: most frequent words and phrases with STRICT filtering
                from collections import Counter
                import re
                
                # Extract single words
                words = re.findall(r'\w+', transcript.lower())
                
                # Use global stopwords for fallback method
                stopwords = DUTCH_STOPWORDS
                filtered_words = [w for w in words if w not in stopwords and len(w) > 3]
                
                # Extract phrases (2-3 word combinations) with STRICT filtering - max 1 stopword for 2-3 word phrases
                sentences = re.split(r'[.!?]+', transcript.lower())
                phrases = []
                for sentence in sentences:
                    sentence_words = re.findall(r'\w+', sentence.strip())
                    # Generate 2-word phrases
                    for i in range(len(sentence_words) - 1):
                        word1, word2 = sentence_words[i], sentence_words[i+1]
                                            # Count stopwords in phrase
                    stopword_count = sum(1 for word in [word1, word2] if word in stopwords)
                    # Allow max 1 stopword for 2-word phrases (moderate)
                    if stopword_count <= 1:
                        # Additional check: ensure non-stopword word is substantial
                        non_stopword = word1 if word1 not in stopwords else word2
                        if len(non_stopword) >= 3:  # Only if non-stopword is meaningful
                            phrase = f"{word1} {word2}"
                            phrases.append(phrase)
                
                # Generate 3-word phrases
                for i in range(len(sentence_words) - 2):
                    word1, word2, word3 = sentence_words[i], sentence_words[i+1], sentence_words[i+2]
                    # Count stopwords in phrase
                    stopword_count = sum(1 for word in [word1, word2, word3] if word in stopwords)
                    # Allow max 1 stopword for 3-word phrases (strict)
                    if stopword_count <= 1:
                        # Additional check: ensure at least 2 non-stopwords are substantial
                        non_stopwords = [w for w in [word1, word2, word3] if w not in stopwords]
                        if len(non_stopwords) >= 2 and all(len(w) >= 3 for w in non_stopwords):
                            phrase = f"{word1} {word2} {word3}"
                            phrases.append(phrase)
                
                # Generate 4-word phrases
                for i in range(len(sentence_words) - 3):
                    word1, word2, word3, word4 = sentence_words[i], sentence_words[i+1], sentence_words[i+2], sentence_words[i+3]
                    # Count stopwords in phrase
                    stopword_count = sum(1 for word in [word1, word2, word3, word4] if word in stopwords)
                    # Allow max 2 stopwords for 4-word phrases (moderate)
                    if stopword_count <= 2:
                        # Additional check: ensure at least 2 non-stopwords are substantial
                        non_stopwords = [w for w in [word1, word2, word3, word4] if w not in stopwords]
                        if len(non_stopwords) >= 2 and all(len(w) >= 3 for w in non_stopwords):
                            phrase = f"{word1} {word2} {word3} {word4}"
                            phrases.append(phrase)
                
                # Generate 5-word phrases
                for i in range(len(sentence_words) - 4):
                    word1, word2, word3, word4, word5 = sentence_words[i], sentence_words[i+1], sentence_words[i+2], sentence_words[i+3], sentence_words[i+4]
                    # Count stopwords in phrase
                    stopword_count = sum(1 for word in [word1, word2, word3, word4, word5] if word in stopwords)
                    # Allow max 2 stopwords for 5-word phrases (moderate)
                    if stopword_count <= 2:
                        # Additional check: ensure at least 3 non-stopwords are substantial
                        non_stopwords = [w for w in [word1, word2, word3, word4, word5] if w not in stopwords]
                        if len(non_stopwords) >= 3 and all(len(w) >= 3 for w in non_stopwords):
                            phrase = f"{word1} {word2} {word3} {word4} {word5}"
                            phrases.append(phrase)
                
                # Combine single words and phrases, get most common
                all_terms = filtered_words + phrases
                term_counts = Counter(all_terms)
                
                # Get top terms - 20 significant words and more phrases
                top_single_words = [w for w, _ in term_counts.most_common(100) if ' ' not in w][:20]  # Increased to 20
                # Include phrases that appear at least once (reduced from > 1 to >= 1 for short recordings)
                top_phrases = [p for p, count in term_counts.most_common(200) if ' ' in p and count >= 1][:25]  # Increased to 25 phrases
                

                
                # Ensure we have a good mix of words and phrases
                if len(top_single_words) < 5:
                    # Look for more single words in the most common terms
                    all_single_words = [w for w, _ in term_counts.most_common(200) if ' ' not in w and len(w) > 3]
                    top_single_words = all_single_words[:20]
                
                if len(top_phrases) < 10:
                    # Look for more phrases in the most common terms
                    all_phrases = [p for p, _ in term_counts.most_common(300) if ' ' in p and len(p.split()) <= 3]
                    top_phrases = all_phrases[:25]
                
                keypoints = top_single_words + top_phrases
            
            # Fallback: if no keypoints found, use most common words regardless of stopwords
            if not keypoints and transcript.strip():
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
                
                # If fallback also finds nothing, use all words longer than 3 characters
                if not keypoints:
                    all_words = [w for w in words if len(w) > 3]
                    all_counts = Counter(all_words)
                    keypoints = [w for w, _ in all_counts.most_common(15)]
            
            # Find when key points are mentioned
            try:
                keypoint_times = {kp: [] for kp in keypoints}
                
                for seg in all_segments:
                    for kp in keypoints:
                        if kp.lower() in seg["text"].lower():
                            keypoint_times[kp].append(seg["start"])
                            
            except Exception as kp_error:
                keypoint_times = {}
            
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
                        f.write("\n💬 Most Mentioned Phrases (Strict filtering - max 1 stopword for 2-3 word phrases):\n")
                        for i, (kp, times) in enumerate(phrases, 1):
                            try:
                                f.write(f"  {i:2d}. \"{kp}\": {', '.join([f'{t:.1f}s' for t in times])}\n")
                            except Exception as write_error:
                                continue
                    else:
                        f.write("\n💬 Most Mentioned Phrases (Strict filtering - max 1 stopword for 2-3 word phrases):\n  • No significant phrases encountered\n")
                
            except Exception as file_error:
                print(f"Error writing output file: {file_error}")
                output_txt = None
            
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
                    summary += "\n💬 Most Mentioned Phrases (Strict filtering - max 1 stopword for 2-3 word phrases):\n"
                    for i, (kp, times) in enumerate(phrases, 1):
                        try:
                            summary += f"  {i:2d}. \"{kp}\": {', '.join([f'{t:.1f}s' for t in times])}\n"
                        except Exception as format_error:
                            continue
                else:
                    summary += "\n💬 Most Mentioned Phrases (Strict filtering - max 1 stopword for 2-3 word phrases):\n  • No significant phrases encountered\n"
                
            except Exception as summary_error:
                summary = "--- Key Talking Points & Phrases ---\n\nError occurred while processing keypoints."
            
            def show_results():
                self.status_label.config(text=f"Transcription complete. See {output_txt}")
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
            
        except Exception as e:
            # Capture the exception in the closure
            error_msg = str(e)
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
