# Utility functions for Radio Transcription Tool
import os
import sys
import subprocess
import time
from datetime import datetime
from config import BIN_DIR, FFMPEG_EXE, FFPLAY_EXE, CONFIG_FILE, AUDIO_CLEANUP_CONFIG, PROGRAMMING_CONFIG

def get_executable_path(executable_name):
    """
    Get the path to ffmpeg or ffplay executable, preferring bin/ subdirectory
    """
    # First check if we're running as compiled executable
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check bin/ subdirectory first
    bin_path = os.path.join(app_dir, BIN_DIR, executable_name)
    if os.path.exists(bin_path):
        return bin_path
    
    # Fallback to system PATH
    return executable_name

def get_silent_subprocess_params():
    """Get parameters for silent subprocess execution on Windows"""
    startupinfo = None
    creationflags = 0
    
    if os.name == 'nt':  # Windows
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = subprocess.CREATE_NO_WINDOW
    
    return startupinfo, creationflags

def is_whisper_artifact(text):
    """
    Check if text is a Whisper prompt artifact that should be filtered out.
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to be a Whisper artifact, False otherwise
    """
    if not text or len(text.strip()) < 10:
        return False
    
    text_lower = text.lower().strip()
    
    # Common Whisper prompt artifacts
    whisper_prompt_indicators = [
        "transcriptie",
        "nederlandse radio-uitzending",
        "nieuws discussies interviews",
        "focus op spraak",
        "niet op muziek",
        "belangrijke woorden",
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
        "focus op spraak en gesprekken"
    ]
    
    for pattern in suspicious_patterns:
        if pattern in text_lower:
            return True
    
    return False

def get_output_filename(station_name):
    """
    Generate output filename based on station name and current timestamp.
    
    Args:
        station_name: Name of the radio station
        
    Returns:
        Formatted filename string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create subfolder structure: YYYYMMDD_HHMMSS_StationName/
    station_sanitized = station_name.replace(" ", "_").replace("(", "").replace(")", "")
    folder_name = f"{timestamp}_{station_sanitized}"
    
    # Create the full path with subfolder
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    recordings_dir = os.path.join(app_dir, "Recordings+transcriptions")
    os.makedirs(recordings_dir, exist_ok=True)
    
    station_dir = os.path.join(recordings_dir, folder_name)
    os.makedirs(station_dir, exist_ok=True)
    
    return os.path.join(station_dir, f"radio_recording_{timestamp}.mp3")

def load_openai_api_key():
    """Load OpenAI API key from config file"""
    try:
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        config_path = os.path.join(app_dir, CONFIG_FILE)
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                api_key = f.read().strip()
                if api_key and api_key.startswith('sk-'):
                    os.environ['OPENAI_API_KEY'] = api_key
                    return api_key
        
        return None
    except Exception as e:
        print(f"Error loading OpenAI API key: {e}")
        return None

def save_openai_api_key(api_key):
    """Save OpenAI API key to config file"""
    try:
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        config_path = os.path.join(app_dir, CONFIG_FILE)
        
        with open(config_path, 'w') as f:
            f.write(api_key)
        
        os.environ['OPENAI_API_KEY'] = api_key
        return True
    except Exception as e:
        print(f"Error saving OpenAI API key: {e}")
        return False

def load_audio_cleanup_config():
    """Load audio cleanup configuration"""
    try:
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        config_path = os.path.join(app_dir, AUDIO_CLEANUP_CONFIG)
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = f.read().strip()
                return config.lower() == 'true'
        
        return True  # Default to True
    except Exception:
        return True  # Default to True

def save_audio_cleanup_config(enabled):
    """Save audio cleanup configuration"""
    try:
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        config_path = os.path.join(app_dir, AUDIO_CLEANUP_CONFIG)
        
        with open(config_path, 'w') as f:
            f.write(str(enabled))
        
        return True
    except Exception as e:
        print(f"Error saving audio cleanup config: {e}")
        return False

def load_programming_config():
    """Load programming configuration"""
    try:
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        config_path = os.path.join(app_dir, PROGRAMMING_CONFIG)
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                # Try to parse as JSON first (new format)
                try:
                    import json
                    return json.loads(content)
                except:
                    # Fallback to old boolean format
                    return {'auto_update': content.lower() == 'true', 
                           'station': "Radio 1 (Netherlands)",
                           'webpage': "https://www.nporadio1.nl/gids"}
        
        return {'auto_update': False, 
               'station': "Radio 1 (Netherlands)",
               'webpage': "https://www.nporadio1.nl/gids"}
    except Exception as e:
        print(f"Error loading programming config: {e}")
        return {'auto_update': False, 
               'station': "Radio 1 (Netherlands)",
               'webpage': "https://www.nporadio1.nl/gids"}

def save_programming_config(config):
    """Save programming configuration"""
    try:
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        config_path = os.path.join(app_dir, PROGRAMMING_CONFIG)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(config, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving programming config: {e}")
        return False

def remove_openai_api_key():
    """Remove the OpenAI API key by deleting the config file"""
    try:
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        config_path = os.path.join(app_dir, CONFIG_FILE)
        
        if os.path.exists(config_path):
            os.remove(config_path)
        
        # Clear environment variable
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        return True
    except Exception as e:
        print(f"Error removing OpenAI API key: {e}")
        return False

def calculate_similarity(text1, text2):
    """
    Calculate similarity between two text segments using word overlap.
    
    Args:
        text1: First text segment
        text2: Second text segment
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Convert to sets of words for comparison
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def count_phrase_occurrences(phrase, transcript_words):
    """
    Count phrase occurrences in transcript - FLEXIBLE VERSION
    
    Args:
        phrase: The phrase to count
        transcript_words: List of words in the transcript
        
    Returns:
        Number of occurrences
    """
    if not phrase or not transcript_words:
        return 0
    
    phrase_words = phrase.lower().split()
    if len(phrase_words) == 0:
        return 0
    
    count = 0
    transcript_lower = [word.lower() for word in transcript_words]
    
    for i in range(len(transcript_lower) - len(phrase_words) + 1):
        # Check if the phrase matches starting at position i
        match = True
        for j, phrase_word in enumerate(phrase_words):
            if i + j >= len(transcript_lower) or transcript_lower[i + j] != phrase_word:
                match = False
                break
        
        if match:
            count += 1
    
    return count

def download_programming_info(station_name, webpage_url):
    """Download and scrape programming information for a radio station"""
    try:
        import requests
        from datetime import datetime
        from bs4 import BeautifulSoup
        
        # Create programming info directory
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create subdirectory with date and station name
        today = datetime.now().strftime('%Y-%m-%d')
        station_folder = station_name.replace(' ', '_').replace('(', '').replace(')', '')
        programming_dir = os.path.join(app_dir, "Recordings+transcriptions", "Transcriptions", f"{today}_{station_folder}")
        os.makedirs(programming_dir, exist_ok=True)
        
        # Check if programming.txt already exists for today
        programming_file = os.path.join(programming_dir, "programming.txt")
        if os.path.exists(programming_file):
            print(f"Programming info already exists for {station_name} on {today}, skipping download")
            return True
        
        # Download webpage
        response = requests.get(webpage_url, timeout=30)
        response.raise_for_status()
        
        # Parse HTML and extract programming information
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        import re
        
        # Find programming entries by looking for specific HTML structures
        programming_entries = []
        
        # Try different approaches to find programming items
        # Look for common programming item selectors
        item_selectors = [
            'div[class*="program"]',
            'div[class*="item"]',
            'div[class*="entry"]',
            'li[class*="program"]',
            'li[class*="item"]',
            'tr[class*="program"]',
            'tr[class*="item"]',
            '.program-item',
            '.schedule-item',
            '.programming-item',
            'article',
            'section[class*="program"]',
            'div[class*="schedule"]',
            'div[class*="gids"]'
        ]
        
        programming_items = []
        for selector in item_selectors:
            items = soup.select(selector)
            if items:
                programming_items.extend(items)  # Add all found items
        
        # If no specific items found, look for time patterns in the page
        if not programming_items:
            # Look for elements containing time patterns
            all_elements = soup.find_all(['div', 'span', 'p', 'td', 'li', 'article', 'section'])
            for element in all_elements:
                text_content = element.get_text().strip()
                if re.search(r'\d{2}:\d{2}', text_content):
                    programming_items.append(element)
        
        # Also try to find programming items by looking for time patterns in parent containers
        time_elements = soup.find_all(string=re.compile(r'\d{2}:\d{2}'))
        for time_element in time_elements:
            # Find the parent element that likely contains the full program info
            parent = time_element.parent
            while parent and parent.name not in ['body', 'html']:
                if parent not in programming_items:
                    programming_items.append(parent)
                parent = parent.parent
        
        # Process each programming item
        seen_entries = set()  # Track entries to avoid duplicates
        processed_times = set()  # Track processed time slots to avoid duplicates
        
        # Sort items by depth (process smaller elements first to avoid parent containers)
        programming_items.sort(key=lambda x: len(str(x)))
        
        for item in programming_items:
            try:
                # Extract start time
                start_time = None
                end_time = None
                program_name = ""
                reporter = ""
                
                # Look for time elements
                time_elements = item.find_all(['span', 'div', 'td'], string=re.compile(r'\d{2}:\d{2}'))
                if time_elements:
                    time_text = time_elements[0].get_text().strip()
                    time_match = re.search(r'(\d{2}:\d{2})', time_text)
                    if time_match:
                        start_time = time_match.group(1)
                
                # Look for time range
                time_range_match = re.search(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})', item.get_text())
                if time_range_match:
                    start_time = time_range_match.group(1)
                    end_time = time_range_match.group(2)
                
                # Extract program name - look for elements with program-related classes
                program_selectors = [
                    '[class*="title"]',
                    '[class*="name"]',
                    '[class*="program"]',
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
                ]
                
                for selector in program_selectors:
                    program_element = item.select_one(selector)
                    if program_element:
                        program_name = program_element.get_text().strip()
                        break
                
                # If no specific program element found, try to extract from text
                if not program_name:
                    text_content = item.get_text()
                    # Remove time information to get program name
                    text_content = re.sub(r'\d{2}:\d{2}\s*-\s*\d{2}:\d{2}', '', text_content)
                    text_content = re.sub(r'\d{2}:\d{2}', '', text_content)
                    # Clean up extra whitespace and newlines
                    text_content = re.sub(r'\s+', ' ', text_content)
                    program_name = text_content.strip()
                
                # Try alternative extraction methods if still no program name
                if not program_name or len(program_name) < 3:
                    # Look for text nodes that might contain program names
                    for text_node in item.find_all(string=True):
                        text_content = text_node.strip()
                        if text_content and len(text_content) > 3:
                            # Skip if it's just a time or time range
                            if not re.match(r'^\d{2}:\d{2}$', text_content) and not re.match(r'^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}$', text_content):
                                program_name = text_content
                                break
                
                # Filter out navigation and non-programming content
                filter_words = ['gids', 'programma', 'schedule', 'menu', 'navigation', 'nav', 'header', 'footer']
                program_name_lower = program_name.lower()
                
                # Skip if program name contains filter words, is too short, or is just a time
                if (any(word in program_name_lower for word in filter_words) or 
                    len(program_name) < 3 or 
                    re.match(r'^\d{2}:\d{2}$', program_name) or 
                    re.match(r'^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}$', program_name)):
                    continue
                
                # Extract reporter - look for elements with presenter/reporter classes
                reporter_selectors = [
                    '[class*="presenter"]',
                    '[class*="reporter"]',
                    '[class*="host"]',
                    '[class*="dj"]',
                    '[class*="guest"]',
                    '[class*="name"]'
                ]
                
                for selector in reporter_selectors:
                    reporter_element = item.select_one(selector)
                    if reporter_element:
                        reporter = reporter_element.get_text().strip()
                        break
                
                # If no specific reporter element found, try to extract from text
                if not reporter and program_name:
                    # Look for capitalized names that might be reporters/guests
                    text_content = item.get_text()
                    # Remove time and program name to find reporter
                    text_content = re.sub(r'\d{2}:\d{2}\s*-\s*\d{2}:\d{2}', '', text_content)
                    text_content = re.sub(r'\d{2}:\d{2}', '', text_content)
                    text_content = re.sub(re.escape(program_name), '', text_content, flags=re.IGNORECASE)
                    text_content = text_content.strip()
                    
                    # Look for capitalized words that might be names
                    words = text_content.split()
                    potential_reporter = []
                    for word in words:
                        if word[0].isupper() and word.isalpha() and len(word) > 2:
                            potential_reporter.append(word)
                    
                    if potential_reporter:
                        reporter = ' '.join(potential_reporter)
                
                # If we found a start time, add to programming entries
                if start_time and program_name:
                    # Create time key for deduplication
                    time_key = f"{start_time}-{end_time}" if end_time else start_time
                    
                    # Skip if we've already processed this time slot
                    if time_key in processed_times:
                        continue
                    
                    if end_time:
                        entry = f"{start_time} - {end_time}: {program_name}"
                    else:
                        entry = f"{start_time}: {program_name}"
                    
                    if reporter:
                        entry += f" {reporter}"
                    
                    # Check for duplicates before adding
                    if entry not in seen_entries:
                        programming_entries.append(entry)
                        seen_entries.add(entry)
                        processed_times.add(time_key)
                    
            except Exception as e:
                continue  # Skip items that can't be processed
        
        # Format the programming entries
        if programming_entries:
            # Sort entries chronologically by start time
            def extract_start_time(entry):
                # Extract start time from entry (e.g., "06:00 - 07:00: Program Name" -> "06:00")
                time_match = re.match(r'(\d{2}:\d{2})', entry)
                if time_match:
                    return time_match.group(1)
                return "00:00"  # Fallback for entries without time
            
            programming_entries.sort(key=extract_start_time)
            text = '\n\n'.join(programming_entries)
        else:
            # Fallback to simple text extraction if structured parsing fails
            text = soup.get_text()
            # Clean up the text
            lines = []
            for line in text.splitlines():
                line = line.strip()
                if line:
                    lines.append(line)
            text = '\n'.join(lines)
        
        # Save programming info as text file
        with open(programming_file, 'w', encoding='utf-8') as f:
            f.write(f"=== {station_name} Programming - {today} ===\n\n")
            f.write(text)
        
        print(f"Programming info scraped and saved: {programming_file}")
        return True
        
    except Exception as e:
        print(f"Error downloading programming info: {e}")
        return False
