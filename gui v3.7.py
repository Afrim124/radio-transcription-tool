# GUI module for Radio Transcription Tool
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import sys
import time
import threading
import subprocess
import webbrowser
from config import VERSION, RADIO_STATIONS
from utils import load_openai_api_key, save_openai_api_key, remove_openai_api_key
from utils import load_audio_cleanup_config, save_audio_cleanup_config
from utils import load_programming_config, save_programming_config, download_programming_info
import logging
import math
from utils import get_executable_path, get_silent_subprocess_params, get_output_filename

# Try to import PIL for image processing (optional)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def record_stream(stream_url, output_file, stop_event):
    """Record radio stream using ffmpeg (from original implementation)"""
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

class RadioRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Radio Transcription Tool v{VERSION} - Powered by Bluvia (Dutch Language & Music Filtering)")
        
        # Initialize logging for the GUI
        from logging_config import setup_logging
        setup_logging()
        
        # Check for OpenAI API key and prompt if missing
        self.check_and_prompt_api_key()
        
        # Check for automatic programming download
        self.check_and_download_programming()
        
        # Set window icon if available
        try:
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(app_dir, "Bluvia images", "Bluebird app icon 2a.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # Icon setting is optional
        
        # Create menu bar
        self.create_menu()
        
        # Create main content frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add Bluvia logo at the top
        self.create_logo_section(main_frame)
        
        # Initialize variables (matching original implementation)
        self.station_var = tk.StringVar(value=list(RADIO_STATIONS.keys())[0])
        self.is_recording = False
        self.recording_thread = None
        self.stop_event = threading.Event()
        self.output_file = None
        self.is_listening = False
        self.listen_process = None
        
        # Audio cleanup setting (default: True - auto cleanup)
        self.auto_cleanup_audio = tk.BooleanVar(value=True)
        self.load_audio_cleanup_setting()
        
        # Programming settings (default: False - no auto update)
        self.auto_update_programming = tk.BooleanVar(value=False)
        self.programming_station_var = tk.StringVar(value="Radio 1 (Netherlands)")
        self.programming_webpage_var = tk.StringVar(value="https://www.nporadio1.nl/gids")
        self.load_programming_settings()
        
        # Create main interface
        self.create_main_interface(main_frame)
        
        # Add footer with Bluvia branding
        self.create_footer(main_frame)
    
    def check_and_prompt_api_key(self):
        """Check if OpenAI API key exists and prompt user if missing"""
        try:
            api_key = load_openai_api_key()
            if not api_key:
                logging.info("DEBUG: No OpenAI API key found, prompting user")
                self.show_api_key_required_dialog()
            else:
                logging.info("DEBUG: OpenAI API key found and loaded")
        except Exception as e:
            logging.error(f"DEBUG: Error checking API key: {e}")
            self.show_api_key_required_dialog()
    
    def show_api_key_required_dialog(self):
        """Show dialog requiring API key before proceeding"""
        dialog = tk.Toplevel(self.root)
        dialog.title("OpenAI API Key Required")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the window
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
        
        # Make dialog modal (block other windows)
        dialog.focus_set()
        dialog.lift()
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Warning icon and title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        warning_label = ttk.Label(title_frame, text="⚠️", font=('Arial', 24))
        warning_label.pack(side=tk.LEFT, padx=(0, 15))
        
        title_text = ttk.Label(title_frame, text="OpenAI API Key Required", 
                              font=('Arial', 16, 'bold'), foreground='#D32F2F')
        title_text.pack(side=tk.LEFT)
        
        # Description
        desc_text = """The Radio Transcription Tool requires an OpenAI API key to transcribe audio recordings.

Without an API key, you can record audio but cannot transcribe it.

Please enter your OpenAI API key below to continue."""
        
        desc_label = ttk.Label(main_frame, text=desc_text, font=('Arial', 10), 
                              wraplength=450, justify='left')
        desc_label.pack(pady=(0, 20))
        
        # API Key entry
        ttk.Label(main_frame, text="OpenAI API Key:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        key_var = tk.StringVar()
        key_entry = ttk.Entry(main_frame, textvariable=key_var, width=60, show="*")
        key_entry.pack(pady=(0, 10))
        
        # Help text
        help_text = "Your API key starts with 'sk-' and can be found at: https://platform.openai.com/api-keys"
        help_label = ttk.Label(main_frame, text=help_text, font=('Arial', 8), 
                              foreground='#666666', wraplength=450)
        help_label.pack(pady=(0, 20))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        def save_and_continue():
            key = key_var.get().strip()
            if key and key.startswith('sk-'):
                try:
                    save_openai_api_key(key)
                    logging.info("DEBUG: API key saved successfully")
                    messagebox.showinfo("Success", "OpenAI API key has been saved successfully!")
                    dialog.destroy()
                except Exception as e:
                    logging.error(f"DEBUG: Failed to save API key: {e}")
                    messagebox.showerror("Error", f"Failed to save API key: {str(e)}")
            else:
                messagebox.showerror("Invalid Key", "Please enter a valid OpenAI API key that starts with 'sk-'")
        
        def exit_app():
            logging.info("DEBUG: User chose to exit without API key")
            self.root.quit()
        
        ttk.Button(button_frame, text="Save & Continue", command=save_and_continue).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Exit", command=exit_app).pack(side=tk.LEFT)
        
        # Focus on entry and handle Enter key
        key_entry.focus_set()
        dialog.bind('<Return>', lambda e: save_and_continue())
        
        # Prevent closing dialog without API key
        def on_closing():
            if not load_openai_api_key():
                if messagebox.askokcancel("Exit", "You cannot use the transcription features without an API key. Are you sure you want to exit?"):
                    self.root.quit()
        
        dialog.protocol("WM_DELETE_WINDOW", on_closing)
    
    def check_and_download_programming(self):
        """Check if automatic programming download is enabled and download if needed"""
        try:
            config = load_programming_config()
            if config and config.get('auto_update', False):
                station = config.get('station', "Radio 1 (Netherlands)")
                webpage = config.get('webpage', "https://www.nporadio1.nl/gids")
                
                logging.info(f"DEBUG: Auto programming download enabled for {station}")
                
                # Download programming info in background thread
                def download_thread():
                    try:
                        result = download_programming_info(station, webpage)
                        if result == True:
                            logging.info(f"DEBUG: Programming info downloaded successfully for {station}")
                            # Show success notification after download completes
                            self.root.after(0, lambda: messagebox.showinfo("Programming Download", 
                                f"Programming for {station} was downloaded successfully!"))
                        elif result == "skipped":
                            logging.info(f"DEBUG: Programming info already exists for {station}, no download needed")
                            # Don't show any popup for skipped downloads
                        else:
                            logging.warning(f"DEBUG: Failed to download programming info for {station}")
                            # Show error notification
                            self.root.after(0, lambda: messagebox.showerror("Programming Download", 
                                f"Failed to download programming information for {station}"))
                    except Exception as e:
                        logging.error(f"DEBUG: Error in programming download thread: {e}")
                        # Show error notification
                        self.root.after(0, lambda: messagebox.showerror("Programming Download", 
                            f"Error downloading programming information: {str(e)}"))
                
                # Start download in background
                threading.Thread(target=download_thread, daemon=True).start()
            else:
                logging.info("DEBUG: Auto programming download disabled")
                
        except Exception as e:
            logging.error(f"DEBUG: Error checking programming config: {e}")
    
    def create_menu(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Set OpenAI API Key", command=self.show_api_key_popup)
        settings_menu.add_command(label="Remove OpenAI API Key", command=self.remove_openai_api_key)
        settings_menu.add_separator()
        settings_menu.add_command(label="Audio Cleanup Settings", command=self.show_audio_cleanup_settings)
        settings_menu.add_command(label="Programming Settings", command=self.show_programming_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label="Transcribe Recent Recordings", command=self.transcribe_recent_recordings)
        settings_menu.add_separator()
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_separator()
        help_menu.add_command(label="Bluvia Website", command=self.open_bluvia_website)
    
    def create_main_interface(self, main_frame):
        """Create the main interface elements"""
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
    
    def create_logo_section(self, parent):
        """Create the logo section at the top of the application"""
        logo_frame = ttk.Frame(parent)
        logo_frame.pack(fill=tk.X, pady=(0, 20))
        
        try:
            # Try to load and display the Bluebird favicon (medium-large size)
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            favicon_path = os.path.join(app_dir, 'Bluvia images', 'Bluebird favicon.jpeg')
            if os.path.exists(favicon_path) and PIL_AVAILABLE:
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
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            favicon_path = os.path.join(app_dir, 'Bluvia images', 'Bluebird favicon.jpeg')
            if os.path.exists(favicon_path) and PIL_AVAILABLE:
                # Load and resize favicon
                img = Image.open(favicon_path)
                img = img.resize((16, 16), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                favicon_label = ttk.Label(footer_frame, image=photo)
                favicon_label.image = photo
                favicon_label.pack(side=tk.RIGHT, padx=10)
                
        except Exception:
            pass  # Favicon is optional
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def update_status(self):
        """Update the status display"""
        if self.recording:
            elapsed = time.time() - self.recording_start_time
            self.recording_duration = elapsed
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.status_label.config(text=f"Recording: {minutes:02d}:{seconds:02d}")
            
            # Schedule next update
            self.recording_timer = self.root.after(1000, self.update_status)
        else:
            self.status_label.config(text="Ready to record")
    
    def start_recording(self):
        """Start recording (matching original implementation)"""
        if self.is_recording:
            return
        station = self.station_var.get()
        stream_url = RADIO_STATIONS[station]
        self.output_file = get_output_filename(station)
        
        # Log recording start immediately
        import logging
        recording_name = os.path.basename(self.output_file)
        logging.info(f"RECORDING START: {recording_name}")
        
        self.stop_event.clear()
        self.recording_thread = threading.Thread(target=record_stream, args=(stream_url, self.output_file, self.stop_event))
        self.recording_thread.start()
        self.is_recording = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text=f"Recording: {station}")

    def stop_recording(self):
        """Stop recording (matching original implementation)"""
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
    
    def toggle_listen(self):
        """Toggle live listening to radio station"""
        if not self.is_listening:
            try:
                station = self.station_var.get()
                if not station or station not in RADIO_STATIONS:
                    messagebox.showerror("Error", "Please select a valid radio station")
                    return
                
                # Start listening
                self.is_listening = True
                self.listen_button.config(text="■ Stop Listening")
                self.status_label.config(text="Listening to live stream...")
                
                # Start listening thread
                self.listen_thread = threading.Thread(
                    target=self.listen_to_stream,
                    args=(station,),
                    daemon=True
                )
                self.listen_thread.start()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start listening: {str(e)}")
        else:
            # Stop listening
            self.is_listening = False
            self.listen_button.config(text="► Listen Live")
            self.status_label.config(text="Stopped listening")
            
            # Stop the listening process
            if self.listen_process:
                try:
                    self.listen_process.terminate()
                    self.listen_process = None
                except:
                    pass
    
    def transcribe_and_extract(self, audio_path):
        """Transcribe and extract keypoints (from original implementation)"""
        # Logging is already set up in GUI initialization
        
        logging.info("=" * 80)
        logging.info("DEBUG: STARTING TRANSCRIPTION PROCESS")
        logging.info("=" * 80)
        logging.info(f"DEBUG: Audio file: {audio_path}")
        logging.info(f"DEBUG: Audio file exists: {os.path.exists(audio_path)}")
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            logging.info(f"DEBUG: Audio file size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
        
        print("DEBUG: Starting transcription process...")
        print("DEBUG: This should be visible in console/terminal")
        
        # Import pydub for audio processing
        try:
            from pydub import AudioSegment
        except ImportError:
            # Use after() to schedule GUI updates in the main thread
            self.root.after(0, lambda: messagebox.showerror("Dependency Error", "pydub is not installed. Please install it with 'pip install pydub'."))
            self.root.after(0, lambda: self.status_label.config(text="pydub not available"))
            return
        
        # Update status in main thread
        self.root.after(0, lambda: self.status_label.config(text="Transcribing audio with Dutch language optimization and music filtering..."))
        
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
            # Split audio into 10-minute chunks (600000 ms) for better transcription quality
            chunk_length_ms = 10 * 60 * 1000
            
            # Load audio with error handling
            try:
                logging.info(f"DEBUG: Loading audio file with FFMPEG: {os.path.basename(audio_path)}")
                audio = AudioSegment.from_file(audio_path)
                duration_ms = len(audio)
                duration_minutes = duration_ms / (1000 * 60)
                logging.info(f"DEBUG: Audio loaded successfully - Duration: {duration_minutes:.2f} minutes")
                
            except Exception as audio_error:
                logging.error(f"DEBUG: Failed to load audio file: {str(audio_error)}")
                self.root.after(0, lambda: messagebox.showerror("Audio Error", f"Failed to load audio file: {str(audio_error)}\n\nThis could be due to:\n- Corrupted audio file\n- Unsupported audio format\n- File access issues\n\nPlease try recording again."))
                self.root.after(0, lambda: self.status_label.config(text="Failed to load audio file"))
                return
            
            num_chunks = math.ceil(duration_ms / chunk_length_ms)
            all_segments = []
            
            logging.info(f"DEBUG: Expected number of chunks: {num_chunks}")
            
            # Check if audio is valid
            if duration_ms == 0:
                logging.error("DEBUG: Audio file has zero duration")
                self.root.after(0, lambda: messagebox.showerror("Audio Error", "The recorded audio file has zero duration. This could be due to:\n- Recording was too short\n- Audio file corruption\n- Recording failed\n\nPlease try recording again."))
                self.root.after(0, lambda: self.status_label.config(text="Audio file has zero duration"))
                return
            
            for i in range(num_chunks):
                try:
                    # Update progress in main thread
                    self.root.after(0, lambda i=i: self.status_label.config(text=f"Transcribing chunk {i+1}/{num_chunks}..."))
                    
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
                        logging.error(f"DEBUG: Failed to export chunk {i+1}: {export_error}")
                        self.root.after(0, lambda i=i: self.status_label.config(text=f"Chunk {i+1} export failed, continuing..."))
                        continue
                    
                    # Add timeout and retry logic for OpenAI API calls
                    max_retries = 3
                    response = None
                    
                    for retry in range(max_retries):
                        try:
                            with open(chunk_path, "rb") as f:
                                import openai
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
                                self.root.after(0, lambda i=i, retry=retry: self.status_label.config(text=f"Chunk {i+1} failed, retrying ({retry+1}/3)..."))
                                time.sleep(2)  # Wait before retry
                            else:
                                # Final retry failed, log error and continue
                                logging.error(f"Failed to transcribe chunk {i+1} after {max_retries} retries: {api_error}")
                                self.root.after(0, lambda i=i: self.status_label.config(text=f"Chunk {i+1} failed, continuing..."))
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
                                    seg_dict = {
                                        "start": getattr(seg, "start", 0),
                                        "end": getattr(seg, "end", 0),
                                        "text": getattr(seg, "text", "")
                                    }
                                    seg_dicts.append(seg_dict)
                            
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
                    self.root.after(0, lambda i=i: self.status_label.config(text=f"Chunk {i+1} error, continuing..."))
                    # Clean up chunk file if it exists
                    chunk_path = os.path.join(os.path.dirname(audio_path), f"chunk_{i}.mp3")
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                    continue
            
            # Extract key points and phrases
            try:
                self.root.after(0, lambda: self.status_label.config(text="Extracting keypoints and phrases..."))
                
                # Get all text from segments
                all_text = " ".join([seg.get("text", "") for seg in all_segments if seg.get("text")])
                
                if all_text.strip():
                    logging.info(f"Transcription completed. Text length: {len(all_text)} characters")
                    
                    # Use the working fallback keypoint extraction method (bypassing KeyBERT issues)
                    from transcription import extract_keypoints_fallback
                    from phrase_filtering import filter_phrases_robust, deduplicate_phrases
                    from config import DUTCH_STOPWORDS
                    
                    # Filter out Whisper prompt text that sometimes appears in transcriptions
                    prompt_text = "Dit is een Nederlandse radio-uitzending met nieuws, discussies, interviews en gesprekken. Focus op spraak en gesprekken, niet op muziek. De transcriptie moet alle belangrijke woorden en zinnen bevatten, maar muziekteksten en jingles kunnen worden overgeslagen"
                    
                    # Remove the prompt text (case-insensitive) and any repetitions
                    import re
                    # Remove the full prompt text
                    all_text = re.sub(re.escape(prompt_text), "", all_text, flags=re.IGNORECASE)
                    # Remove partial repetitions of the prompt ending
                    all_text = re.sub(r"maar muziekteksten en jingles kunnen worden overgeslagen,?\s*", "", all_text, flags=re.IGNORECASE)
                    # Clean up extra whitespace
                    all_text = re.sub(r'\s+', ' ', all_text).strip()
                    
                    # Extract keypoints using the reliable fallback method
                    phrases, words = extract_keypoints_fallback(all_text, DUTCH_STOPWORDS)
                    
                    # Build keypoint_times dictionary with timestamps (prioritizing longer phrases)
                    keypoints = []
                    
                    # Prioritize longer phrases first (5+ words, then 4 words, then 3 words, then 2 words)
                    long_phrases = [phrase for phrase, count in phrases if len(phrase.split()) >= 5]
                    medium_phrases = [phrase for phrase, count in phrases if len(phrase.split()) == 4]
                    short_phrases = [phrase for phrase, count in phrases if len(phrase.split()) == 3]
                    two_word_phrases = [phrase for phrase, count in phrases if len(phrase.split()) == 2]
                    
                    # Add phrases in priority order (longer first)
                    keypoints.extend(long_phrases[:10])  # Top 10 long phrases
                    keypoints.extend(medium_phrases[:15])  # Top 15 medium phrases
                    keypoints.extend(short_phrases[:20])  # Top 20 short phrases
                    keypoints.extend(two_word_phrases[:15])  # Top 15 two-word phrases
                    
                    # Add words
                    keypoints.extend([word for word, count in words])
                    
                    keypoint_times = {kp: [] for kp in keypoints}
                    
                    for seg in all_segments:
                        for kp in keypoints:
                            if kp.lower() in seg["text"].lower():
                                keypoint_times[kp].append(seg["start"])
                    
                    # Apply advanced phrase filtering and deduplication (matching original)
                    if keypoint_times:
                        # Separate words and phrases
                        words_with_times = [(kp, times) for kp, times in keypoint_times.items() if ' ' not in kp and times]
                        phrases_with_times = [(kp, times) for kp, times in keypoint_times.items() if ' ' in kp and times]
                        
                        # Apply deduplication only to phrases, not words
                        if phrases_with_times:
                            deduplicated_phrases = deduplicate_phrases(phrases_with_times)
                        else:
                            deduplicated_phrases = []
                        
                        # Rebuild keypoint_times with words + deduplicated phrases
                        keypoint_times = {}
                        for kp, times in words_with_times:
                            keypoint_times[kp] = times
                        for kp, times in deduplicated_phrases:
                            keypoint_times[kp] = times
                    
                    # Save transcription to file (using original filename format)
                    output_txt = os.path.splitext(audio_path)[0] + "_transcription.txt"
                    
                    # Write transcription to file (matching original format)
                    try:
                        with open(output_txt, 'w', encoding='utf-8') as f:
                            # Write timestamped transcript first
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
                            
                            # Separate single words and phrases
                            single_words = [(kp, times) for kp, times in keypoint_times.items() if ' ' not in kp and times]
                            phrases = [(kp, times) for kp, times in keypoint_times.items() if ' ' in kp and times]
                            
                            if single_words:
                                f.write(f"\n📝 Most Mentioned Words (Top 20):\n")
                                for i, (kp, times) in enumerate(single_words, 1):
                                    f.write(f"  {i:2d}. {kp}: {', '.join([f'{t:.1f}s' for t in times])}\n")
                            
                            if phrases:
                                f.write(f"\n💬 Most Mentioned Phrases (Improved filtering - more lenient for better coverage):\n")
                                for i, (kp, times) in enumerate(phrases, 1):
                                    f.write(f"  {i:2d}. \"{kp}\": {', '.join([f'{t:.1f}s' for t in times])}\n")
                    
                    except Exception as file_error:
                        logging.error(f"Failed to write transcription file: {file_error}")
                        raise file_error
                    
                    # Create summary for popup
                    summary = "--- Key Talking Points & Phrases ---\n"
                    
                    if single_words:
                        summary += "\n📝 Most Mentioned Words (Top 20):\n"
                        for i, (kp, times) in enumerate(single_words, 1):
                            summary += f"  {i:2d}. {kp}: {', '.join([f'{t:.1f}s' for t in times])}\n"
                    else:
                        summary += "\n📝 Most Mentioned Words (Top 20):\n  • No significant words encountered\n"
                    
                    if phrases:
                        summary += "\n💬 Most Mentioned Phrases (Improved filtering - more lenient for better coverage):\n"
                        for i, (kp, times) in enumerate(phrases, 1):
                            summary += f"  {i:2d}. \"{kp}\": {', '.join([f'{t:.1f}s' for t in times])}\n"
                    else:
                        summary += "\n💬 Most Mentioned Phrases (Improved filtering - more lenient for better coverage):\n  • No significant phrases encountered\n"
                    
                    # Show results popup and open folder
                    total_keypoints = len(single_words) + len(phrases)
                    
                    if total_keypoints < 10:
                        logging.info(f"LOW RESULTS: Only {total_keypoints} keypoints found")
                        self.root.after(0, lambda: self.status_label.config(text=f"Transcription complete but found only {total_keypoints} key points. See {os.path.basename(output_txt)}"))
                        self.root.after(0, lambda: messagebox.showwarning("Limited Results", f"Only {total_keypoints} significant key points found. This might indicate:\n- Audio quality issues\n- Very short speech content\n- Transcription problems\n\nCheck the output file for details."))
                    else:
                        logging.info(f"SUCCESS: Adequate keypoints found")
                        self.root.after(0, lambda: self.status_label.config(text=f"Transcription complete. Found {total_keypoints} key points. See {os.path.basename(output_txt)}"))
                        self.root.after(0, lambda: messagebox.showinfo("Key Talking Points", summary))
                    
                    # Clean up audio file and organize transcription file (if enabled)
                    if self.auto_cleanup_audio.get() and os.path.exists(audio_path):
                        try:
                            # Create central Transcriptions folder in Recordings+transcriptions directory
                            recordings_root_dir = os.path.dirname(os.path.dirname(audio_path))  # Go up two levels
                            transcriptions_dir = os.path.join(recordings_root_dir, "Transcriptions")
                            os.makedirs(transcriptions_dir, exist_ok=True)
                            
                            # Extract date and station from the recording folder name
                            recording_dir = os.path.dirname(audio_path)
                            recording_folder_name = os.path.basename(recording_dir)
                            parts = recording_folder_name.split('_')
                            
                            if len(parts) >= 3:
                                try:
                                    # Extract date (first part: YYYYMMDD)
                                    date_str = parts[0]
                                    import time
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
                                    
                                    logging.info(f"DEBUG: Organizing transcription by date and station ({date_folder}_{station_folder})")
                                    
                                except Exception as date_error:
                                    logging.info(f"DEBUG: Could not parse date/station from folder name, using default location: {date_error}")
                                    # Fallback to central Transcriptions folder
                                    new_transcription_path = os.path.join(transcriptions_dir, transcription_filename)
                            else:
                                # Fallback if folder name format is unexpected
                                new_transcription_path = os.path.join(transcriptions_dir, transcription_filename)
                            
                            try:
                                # Copy transcription file to organized location
                                import shutil
                                shutil.copy2(output_txt, new_transcription_path)
                                logging.info(f"DEBUG: Transcription moved to organized location: {os.path.relpath(new_transcription_path, recordings_root_dir)}")
                                
                                # Remove original transcription file from recording folder
                                os.remove(output_txt)
                                logging.info(f"DEBUG: Original transcription file removed from recording folder")
                                
                                # Remove audio file
                                os.remove(audio_path)
                                logging.info(f"DEBUG: Audio file cleaned up: {os.path.basename(audio_path)}")
                                
                                # Try to remove empty recording folder
                                try:
                                    if not os.listdir(recording_dir):
                                        os.rmdir(recording_dir)
                                        logging.info(f"DEBUG: Empty recording folder removed: {os.path.basename(recording_dir)}")
                                    else:
                                        logging.info(f"DEBUG: Recording folder kept (contains other items): {os.path.basename(recording_dir)}")
                                except Exception as folder_cleanup_error:
                                    logging.info(f"DEBUG: Warning - Could not remove recording folder: {folder_cleanup_error}")
                                
                                logging.info(f"DEBUG: Transcription saved to central Transcriptions folder: {transcription_filename}")
                                
                                # Open the organized Transcriptions folder
                                self.root.after(0, lambda: self.open_results_folder(transcriptions_dir))
                                
                            except Exception as move_error:
                                logging.info(f"DEBUG: Warning - Could not move transcription file: {move_error}")
                                # Fallback: just remove audio file
                                os.remove(audio_path)
                                logging.info(f"DEBUG: Audio file cleaned up (fallback): {os.path.basename(audio_path)}")
                                logging.info(f"DEBUG: Transcription saved: {os.path.basename(output_txt)}")
                                
                                # Open the folder containing the files
                                recording_dir = os.path.dirname(output_txt)
                                self.root.after(0, lambda: self.open_results_folder(recording_dir))
                        except Exception as cleanup_error:
                            logging.info(f"Failed to clean up audio file: {cleanup_error}")
                            # Open the folder containing the files
                            recording_dir = os.path.dirname(output_txt)
                            self.root.after(0, lambda: self.open_results_folder(recording_dir))
                    else:
                        # Audio cleanup disabled - just open the folder containing the files
                        recording_dir = os.path.dirname(output_txt)
                        self.root.after(0, lambda: self.open_results_folder(recording_dir))
                    
                    logging.info(f"RESULTS: {total_keypoints} keypoints ({len(single_words)} words, {len(phrases)} phrases)")
                    logging.info(f"Saved transcription to: {output_txt}")
                    
                else:
                    logging.info("No text found in transcription")
                    self.root.after(0, lambda: self.status_label.config(text="No speech detected in recording."))
                    self.root.after(0, lambda: messagebox.showinfo("No Speech", "No speech was detected in the recording. This could be due to:\n- Very short recording\n- Only music/noise\n- Audio quality issues"))
                    
            except Exception as keypoint_error:
                print(f"Error extracting keypoints: {keypoint_error}")
                self.root.after(0, lambda: self.status_label.config(text="Keypoint extraction failed, but transcription completed."))
        
        finally:
            # Restore original subprocess.Popen
            subprocess.Popen = original_popen
            logging.info("=" * 80)
            logging.info("DEBUG: TRANSCRIPTION PROCESS COMPLETED")
            logging.info("=" * 80)
    
    def transcribe_and_extract_batch(self, audio_path):
        """Transcribe and extract keypoints for batch processing (no folder opening)"""
        # Logging is already set up in GUI initialization
        
        logging.info("=" * 80)
        logging.info("DEBUG: STARTING BATCH TRANSCRIPTION PROCESS")
        logging.info("=" * 80)
        logging.info(f"DEBUG: Audio file: {audio_path}")
        logging.info(f"DEBUG: Audio file exists: {os.path.exists(audio_path)}")
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            logging.info(f"DEBUG: Audio file size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
        
        print("DEBUG: Starting batch transcription process...")
        print("DEBUG: This should be visible in console/terminal")
        
        # Import pydub for audio processing
        try:
            from pydub import AudioSegment
        except ImportError:
            # Use after() to schedule GUI updates in the main thread
            self.root.after(0, lambda: messagebox.showerror("Dependency Error", "pydub is not installed. Please install it with 'pip install pydub'."))
            self.root.after(0, lambda: self.status_label.config(text="pydub not available"))
            return
        
        # Update status in main thread
        self.root.after(0, lambda: self.status_label.config(text="Transcribing audio with Dutch language optimization and music filtering..."))
        
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
            # Split audio into 10-minute chunks (600000 ms) for better transcription quality
            chunk_length_ms = 10 * 60 * 1000
            
            # Load audio with error handling
            try:
                logging.info(f"DEBUG: Loading audio file with FFMPEG: {os.path.basename(audio_path)}")
                audio = AudioSegment.from_file(audio_path)
                duration_ms = len(audio)
                duration_minutes = duration_ms / (1000 * 60)
                logging.info(f"DEBUG: Audio loaded successfully - Duration: {duration_minutes:.2f} minutes")
                
            except Exception as audio_error:
                logging.error(f"DEBUG: Failed to load audio file: {str(audio_error)}")
                self.root.after(0, lambda: messagebox.showerror("Audio Error", f"Failed to load audio file: {str(audio_error)}\n\nThis could be due to:\n- Corrupted audio file\n- Unsupported audio format\n- File access issues\n\nPlease try recording again."))
                self.root.after(0, lambda: self.status_label.config(text="Failed to load audio file"))
                return
            
            num_chunks = math.ceil(duration_ms / chunk_length_ms)
            all_segments = []
            
            logging.info(f"DEBUG: Expected number of chunks: {num_chunks}")
            
            # Check if audio is valid
            if duration_ms == 0:
                logging.error("DEBUG: Audio file has zero duration")
                self.root.after(0, lambda: messagebox.showerror("Audio Error", "The recorded audio file has zero duration. This could be due to:\n- Recording was too short\n- Audio file corruption\n- Recording failed\n\nPlease try recording again."))
                self.root.after(0, lambda: self.status_label.config(text="Audio file has zero duration"))
                return
            
            for i in range(num_chunks):
                try:
                    # Update progress in main thread
                    self.root.after(0, lambda i=i: self.status_label.config(text=f"Transcribing chunk {i+1}/{num_chunks}..."))
                    
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
                        logging.error(f"DEBUG: Failed to export chunk {i+1}: {export_error}")
                        self.root.after(0, lambda i=i: self.status_label.config(text=f"Chunk {i+1} export failed, continuing..."))
                        continue
                    
                    # Add timeout and retry logic for OpenAI API calls
                    max_retries = 3
                    response = None
                    
                    for retry in range(max_retries):
                        try:
                            with open(chunk_path, "rb") as f:
                                import openai
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
                                self.root.after(0, lambda i=i, retry=retry: self.status_label.config(text=f"Chunk {i+1} failed, retrying ({retry+1}/3)..."))
                                time.sleep(2)  # Wait before retry
                            else:
                                # Final retry failed, log error and continue
                                logging.error(f"Failed to transcribe chunk {i+1} after {max_retries} retries: {api_error}")
                                self.root.after(0, lambda i=i: self.status_label.config(text=f"Chunk {i+1} failed, continuing..."))
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
                                    seg_dict = {
                                        "start": getattr(seg, "start", 0),
                                        "end": getattr(seg, "end", 0),
                                        "text": getattr(seg, "text", "")
                                    }
                                    seg_dicts.append(seg_dict)
                            
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
                    self.root.after(0, lambda i=i: self.status_label.config(text=f"Chunk {i+1} error, continuing..."))
                    # Clean up chunk file if it exists
                    chunk_path = os.path.join(os.path.dirname(audio_path), f"chunk_{i}.mp3")
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                    continue
            
            # Extract key points and phrases
            try:
                self.root.after(0, lambda: self.status_label.config(text="Extracting keypoints and phrases..."))
                
                # Get all text from segments
                all_text = " ".join([seg.get("text", "") for seg in all_segments if seg.get("text")])
                
                if all_text.strip():
                    logging.info(f"Transcription completed. Text length: {len(all_text)} characters")
                    
                    # Use the working fallback keypoint extraction method (bypassing KeyBERT issues)
                    from transcription import extract_keypoints_fallback
                    from phrase_filtering import filter_phrases_robust, deduplicate_phrases
                    from config import DUTCH_STOPWORDS
                    
                    # Filter out Whisper prompt text that sometimes appears in transcriptions
                    prompt_text = "Dit is een Nederlandse radio-uitzending met nieuws, discussies, interviews en gesprekken. Focus op spraak en gesprekken, niet op muziek. De transcriptie moet alle belangrijke woorden en zinnen bevatten, maar muziekteksten en jingles kunnen worden overgeslagen"
                    
                    # Remove the prompt text (case-insensitive) and any repetitions
                    import re
                    # Remove the full prompt text
                    all_text = re.sub(re.escape(prompt_text), "", all_text, flags=re.IGNORECASE)
                    # Remove partial repetitions of the prompt ending
                    all_text = re.sub(r"maar muziekteksten en jingles kunnen worden overgeslagen,?\s*", "", all_text, flags=re.IGNORECASE)
                    # Clean up extra whitespace
                    all_text = re.sub(r'\s+', ' ', all_text).strip()
                    
                    # Extract keypoints using the reliable fallback method
                    phrases, words = extract_keypoints_fallback(all_text, DUTCH_STOPWORDS)
                    
                    # Build keypoint_times dictionary with timestamps (prioritizing longer phrases)
                    keypoints = []
                    
                    # Prioritize longer phrases first (5+ words, then 4 words, then 3 words, then 2 words)
                    long_phrases = [phrase for phrase, count in phrases if len(phrase.split()) >= 5]
                    medium_phrases = [phrase for phrase, count in phrases if len(phrase.split()) == 4]
                    short_phrases = [phrase for phrase, count in phrases if len(phrase.split()) == 3]
                    two_word_phrases = [phrase for phrase, count in phrases if len(phrase.split()) == 2]
                    
                    # Add phrases in priority order (longer first)
                    keypoints.extend(long_phrases[:10])  # Top 10 long phrases
                    keypoints.extend(medium_phrases[:15])  # Top 15 medium phrases
                    keypoints.extend(short_phrases[:20])  # Top 20 short phrases
                    keypoints.extend(two_word_phrases[:15])  # Top 15 two-word phrases
                    
                    # Add words
                    keypoints.extend([word for word, count in words])
                    
                    keypoint_times = {kp: [] for kp in keypoints}
                    
                    for seg in all_segments:
                        for kp in keypoints:
                            if kp.lower() in seg["text"].lower():
                                keypoint_times[kp].append(seg["start"])
                    
                    # Apply advanced phrase filtering and deduplication (matching original)
                    if keypoint_times:
                        # Separate words and phrases
                        words_with_times = [(kp, times) for kp, times in keypoint_times.items() if ' ' not in kp and times]
                        phrases_with_times = [(kp, times) for kp, times in keypoint_times.items() if ' ' in kp and times]
                        
                        # Apply deduplication only to phrases, not words
                        if phrases_with_times:
                            deduplicated_phrases = deduplicate_phrases(phrases_with_times)
                        else:
                            deduplicated_phrases = []
                        
                        # Rebuild keypoint_times with words + deduplicated phrases
                        keypoint_times = {}
                        for kp, times in words_with_times:
                            keypoint_times[kp] = times
                        for kp, times in deduplicated_phrases:
                            keypoint_times[kp] = times
                    
                    # Save transcription to file (using original filename format)
                    output_txt = os.path.splitext(audio_path)[0] + "_transcription.txt"
                    
                    # Write transcription to file (matching original format)
                    try:
                        with open(output_txt, 'w', encoding='utf-8') as f:
                            # Write timestamped transcript first
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
                            
                            # Separate single words and phrases
                            single_words = [(kp, times) for kp, times in keypoint_times.items() if ' ' not in kp and times]
                            phrases = [(kp, times) for kp, times in keypoint_times.items() if ' ' in kp and times]
                            
                            if single_words:
                                f.write(f"\n📝 Most Mentioned Words (Top 20):\n")
                                for i, (kp, times) in enumerate(single_words, 1):
                                    f.write(f"  {i:2d}. {kp}: {', '.join([f'{t:.1f}s' for t in times])}\n")
                            
                            if phrases:
                                f.write(f"\n💬 Most Mentioned Phrases (Improved filtering - more lenient for better coverage):\n")
                                for i, (kp, times) in enumerate(phrases, 1):
                                    f.write(f"  {i:2d}. \"{kp}\": {', '.join([f'{t:.1f}s' for t in times])}\n")
                    
                    except Exception as file_error:
                        logging.error(f"Failed to write transcription file: {file_error}")
                        raise file_error
                    
                    # Clean up audio file and organize transcription file (if enabled) - BATCH VERSION
                    if self.auto_cleanup_audio.get() and os.path.exists(audio_path):
                        try:
                            # Create central Transcriptions folder in Recordings+transcriptions directory
                            recordings_root_dir = os.path.dirname(os.path.dirname(audio_path))  # Go up two levels
                            transcriptions_dir = os.path.join(recordings_root_dir, "Transcriptions")
                            os.makedirs(transcriptions_dir, exist_ok=True)
                            
                            # Extract date and station from the recording folder name
                            recording_dir = os.path.dirname(audio_path)
                            recording_folder_name = os.path.basename(recording_dir)
                            parts = recording_folder_name.split('_')
                            
                            if len(parts) >= 3:
                                try:
                                    # Extract date (first part: YYYYMMDD)
                                    date_str = parts[0]
                                    import time
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
                                    
                                    logging.info(f"DEBUG: Organizing transcription by date and station ({date_folder}_{station_folder})")
                                    
                                except Exception as date_error:
                                    logging.info(f"DEBUG: Could not parse date/station from folder name, using default location: {date_error}")
                                    # Fallback to central Transcriptions folder
                                    new_transcription_path = os.path.join(transcriptions_dir, transcription_filename)
                            else:
                                # Fallback if folder name format is unexpected
                                new_transcription_path = os.path.join(transcriptions_dir, transcription_filename)
                            
                            try:
                                # Copy transcription file to organized location
                                import shutil
                                shutil.copy2(output_txt, new_transcription_path)
                                logging.info(f"DEBUG: Transcription moved to organized location: {os.path.relpath(new_transcription_path, recordings_root_dir)}")
                                
                                # Remove original transcription file from recording folder
                                os.remove(output_txt)
                                logging.info(f"DEBUG: Original transcription file removed from recording folder")
                                
                                # Remove audio file
                                os.remove(audio_path)
                                logging.info(f"DEBUG: Audio file cleaned up: {os.path.basename(audio_path)}")
                                
                                # Try to remove empty recording folder
                                try:
                                    if not os.listdir(recording_dir):
                                        os.rmdir(recording_dir)
                                        logging.info(f"DEBUG: Empty recording folder removed: {os.path.basename(recording_dir)}")
                                    else:
                                        logging.info(f"DEBUG: Recording folder kept (contains other items): {os.path.basename(recording_dir)}")
                                except Exception as folder_cleanup_error:
                                    logging.info(f"DEBUG: Warning - Could not remove recording folder: {folder_cleanup_error}")
                                
                                logging.info(f"DEBUG: Transcription saved to central Transcriptions folder: {transcription_filename}")
                                
                                # NOTE: BATCH VERSION - NO FOLDER OPENING
                                # The folder opening is intentionally omitted for batch processing
                                
                            except Exception as move_error:
                                logging.info(f"DEBUG: Warning - Could not move transcription file: {move_error}")
                                # Fallback: just remove audio file
                                os.remove(audio_path)
                                logging.info(f"DEBUG: Audio file cleaned up (fallback): {os.path.basename(audio_path)}")
                                logging.info(f"DEBUG: Transcription saved: {os.path.basename(output_txt)}")
                                
                        except Exception as cleanup_error:
                            logging.info(f"Failed to clean up audio file: {cleanup_error}")
                    
                    logging.info(f"RESULTS: {len(single_words) + len(phrases)} keypoints ({len(single_words)} words, {len(phrases)} phrases)")
                    logging.info(f"Saved transcription to: {output_txt}")
                    
                else:
                    logging.info("No text found in transcription")
                    self.root.after(0, lambda: self.status_label.config(text="No speech detected in recording."))
                    self.root.after(0, lambda: messagebox.showinfo("No Speech", "No speech was detected in the recording. This could be due to:\n- Very short recording\n- Only music/noise\n- Audio quality issues"))
                    
            except Exception as keypoint_error:
                print(f"Error extracting keypoints: {keypoint_error}")
                self.root.after(0, lambda: self.status_label.config(text="Keypoint extraction failed, but transcription completed."))
        
        finally:
            # Restore original subprocess.Popen
            subprocess.Popen = original_popen
            logging.info("=" * 80)
            logging.info("DEBUG: BATCH TRANSCRIPTION PROCESS COMPLETED")
            logging.info("=" * 80)
    
    def open_results_folder(self, folder_path):
        """Open the folder containing the recording and transcription files"""
        try:
            import sys
            
            # Update status
            self.status_label.config(text="Processing complete! Opening results folder...")
            
            # Open folder based on operating system (using original method)
            if sys.platform.startswith('win'):
                os.startfile(folder_path)
            elif sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['open', folder_path])
            else:  # Linux
                subprocess.run(['xdg-open', folder_path])
            
            logging.info(f"Opened results folder: {folder_path}")
            
        except Exception as e:
            logging.info(f"Failed to open folder: {str(e)}")
            # If opening folder fails, just show a message
            try:
                messagebox.showinfo("Folder Location", f"Files saved in: {folder_path}")
            except Exception as msg_error:
                # If even the message box fails, just update status
                self.status_label.config(text=f"Files saved in: {folder_path}")
    
    def listen_to_stream(self, station):
        """Listen to live radio stream"""
        try:
            self.root.after(0, lambda: self.status_label.config(text="Listening to live stream..."))
            
            # Get the radio station URL
            station_url = RADIO_STATIONS.get(station)
            if not station_url:
                raise ValueError(f"Unknown station: {station}")
            
            # Use ffplay to stream the radio station
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            ffplay_path = os.path.join(app_dir, 'bin', 'ffplay.exe')
            if not os.path.exists(ffplay_path):
                ffplay_path = 'ffplay'  # Fallback to system PATH
            
            # Start ffplay process
            cmd = [ffplay_path, '-nodisp', '-autoexit', station_url]
            self.listen_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for the process to complete or be stopped
            while self.is_listening and self.listen_process.poll() is None:
                time.sleep(0.1)
            
            if self.is_listening:  # Only if not stopped early
                self.root.after(0, lambda: self.status_label.config(text="Stopped listening"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Listening failed: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.listen_button.config(text="► Listen Live"))
            self.root.after(0, lambda: setattr(self, 'is_listening', False))
    
    def show_api_key_popup(self):
        """Show popup to set OpenAI API key"""
        popup = tk.Toplevel(self.root)
        popup.title("Set OpenAI API Key")
        popup.geometry("400x200")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        
        # Center the window
        popup.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
        
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
                    save_openai_api_key(key)
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
            remove_openai_api_key()
            messagebox.showinfo("Success", "OpenAI API key has been removed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove OpenAI API key: {str(e)}")
    
    def load_audio_cleanup_setting(self):
        """Load audio cleanup setting from config file"""
        try:
            self.auto_cleanup_audio.set(load_audio_cleanup_config())
        except Exception as e:
            print(f"Warning: Could not load audio cleanup setting: {e}")
            # Keep default value (True)
    
    def load_programming_settings(self):
        """Load programming settings from config file"""
        try:
            config = load_programming_config()
            if config:
                self.auto_update_programming.set(config.get('auto_update', False))
                self.programming_station_var.set(config.get('station', "Radio 1 (Netherlands)"))
                self.programming_webpage_var.set(config.get('webpage', "https://www.nporadio1.nl/gids"))
        except Exception as e:
            print(f"Warning: Could not load programming settings: {e}")
            # Keep default values
    
    def show_audio_cleanup_settings(self):
        """Show audio cleanup settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Audio Cleanup Settings")
        settings_window.geometry("400x250")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Center the window
        settings_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
        
        # Main frame
        main_frame = ttk.Frame(settings_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Audio Cleanup Settings", font=('Arial', 12, 'bold')).pack(pady=(0, 15))
        
        # Description
        desc_label = ttk.Label(main_frame, text="Configure automatic cleanup of audio files after transcription:", 
                             font=('Arial', 9), wraplength=350, justify='left')
        desc_label.pack(pady=(0, 15))
        
        # Checkbox
        cleanup_var = tk.BooleanVar(value=self.auto_cleanup_audio.get())
        cleanup_check = ttk.Checkbutton(main_frame, text="Automatically delete audio files after transcription", 
                                       variable=cleanup_var)
        cleanup_check.pack(pady=(0, 15))
        
        # Note
        note_label = ttk.Label(main_frame, text="Note: Transcriptions and keypoints will be preserved.", 
                             font=('Arial', 8), foreground='#666666')
        note_label.pack(pady=(0, 20))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        def save_settings():
            self.auto_cleanup_audio.set(cleanup_var.get())
            save_audio_cleanup_config(cleanup_var.get())
            messagebox.showinfo("Success", "Audio cleanup settings saved successfully!")
            settings_window.destroy()
        
        def cancel():
            settings_window.destroy()
        
        ttk.Button(button_frame, text="Save", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)
    
    def show_programming_settings(self):
        """Show programming settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Programming Settings")
        settings_window.geometry("500x350")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Center the window
        settings_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
        
        # Main frame
        main_frame = ttk.Frame(settings_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Programming Settings", font=('Arial', 12, 'bold')).pack(pady=(0, 15))
        
        # Description
        desc_label = ttk.Label(main_frame, text="Configure automatic programming information updates:", 
                             font=('Arial', 9), wraplength=450, justify='left')
        desc_label.pack(pady=(0, 15))
        
        # Auto update checkbox
        auto_update_var = tk.BooleanVar(value=self.auto_update_programming.get())
        auto_update_check = ttk.Checkbutton(main_frame, text="Automatically update programming information", 
                                          variable=auto_update_var)
        auto_update_check.pack(pady=(0, 15))
        
        # Station selection
        ttk.Label(main_frame, text="Radio Station:", font=('Arial', 9, 'bold')).pack(pady=(10, 5))
        station_var = tk.StringVar(value=self.programming_station_var.get())
        station_combo = ttk.Combobox(main_frame, textvariable=station_var, 
                                    values=list(RADIO_STATIONS.keys()), state='readonly', width=40)
        station_combo.pack(pady=(0, 15))
        
        # Webpage URL
        ttk.Label(main_frame, text="Programming Webpage URL:", font=('Arial', 9, 'bold')).pack(pady=(10, 5))
        webpage_var = tk.StringVar(value=self.programming_webpage_var.get())
        webpage_entry = ttk.Entry(main_frame, textvariable=webpage_var, width=50)
        webpage_entry.pack(pady=(0, 15))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        def download_now():
            # Save current settings first
            self.auto_update_programming.set(auto_update_var.get())
            self.programming_station_var.set(station_var.get())
            self.programming_webpage_var.set(webpage_var.get())
            
            config = {
                'auto_update': auto_update_var.get(),
                'station': station_var.get(),
                'webpage': webpage_var.get()
            }
            save_programming_config(config)
            
            # Download programming info now
            station = station_var.get()
            webpage = webpage_var.get()
            
            def download_thread():
                try:
                    result = download_programming_info(station, webpage)
                    if result == True:
                        self.root.after(0, lambda: messagebox.showinfo("Success", 
                            f"Programming information downloaded successfully for {station}!"))
                    elif result == "skipped":
                        self.root.after(0, lambda: messagebox.showinfo("Info", 
                            f"Programming information already exists for {station}. No download needed."))
                    else:
                        self.root.after(0, lambda: messagebox.showerror("Error", 
                            f"Failed to download programming information for {station}"))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", 
                        f"Error downloading programming information: {str(e)}"))
            
            # Start download in background
            threading.Thread(target=download_thread, daemon=True).start()
            messagebox.showinfo("Download Started", "Downloading programming information in the background...")
            settings_window.destroy()
        
        def close_and_save():
            # Save current settings
            self.auto_update_programming.set(auto_update_var.get())
            self.programming_station_var.set(station_var.get())
            self.programming_webpage_var.set(webpage_var.get())
            
            config = {
                'auto_update': auto_update_var.get(),
                'station': station_var.get(),
                'webpage': webpage_var.get()
            }
            save_programming_config(config)
            settings_window.destroy()
        
        ttk.Button(button_frame, text="Download programming now!", command=download_now).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=close_and_save).pack(side=tk.LEFT, padx=5)
    
    def transcribe_recent_recordings(self):
        """Transcribe recent recordings from the Recordings+transcriptions folder"""
        try:
            import sys
            import time
            
            # Find the recordings directory
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            recordings_dir = os.path.join(app_dir, "Recordings+transcriptions")
            
            if not os.path.exists(recordings_dir):
                messagebox.showinfo("No Recordings", "No recordings directory found. Please record some audio first.")
                return
            
            # Find all MP3 files that don't have transcription files
            mp3_files = []
            for root, dirs, files in os.walk(recordings_dir):
                for file in files:
                    if file.endswith('.mp3') and file.startswith('radio_recording_'):
                        file_path = os.path.join(root, file)
                        
                        # Check if transcription file already exists
                        transcription_file = os.path.splitext(file_path)[0] + "_transcription.txt"
                        
                        if not os.path.exists(transcription_file):
                            mp3_files.append((file_path, os.path.getmtime(file_path)))
            
            if not mp3_files:
                messagebox.showinfo("No Untranscribed Files", "All recorded audio files have already been transcribed.")
                return
            
            # Sort by modification time (newest first) and take last 3
            mp3_files.sort(key=lambda x: x[1], reverse=True)
            recent_files = mp3_files[:3]
            
            # Show confirmation dialog
            confirm_window = tk.Toplevel(self.root)
            confirm_window.title("Transcribe Recent Recordings")
            confirm_window.geometry("500x400")
            confirm_window.resizable(False, False)
            confirm_window.transient(self.root)
            confirm_window.grab_set()
            
            # Center the window
            confirm_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
            
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
            
            # File list
            file_text = tk.Text(main_frame, height=8, width=60, wrap=tk.WORD)
            file_text.pack(pady=(0, 20))
            
            for i, (file_path, mtime) in enumerate(recent_files, 1):
                file_name = os.path.basename(file_path)
                file_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                file_text.insert(tk.END, f"{i}. {file_name}\n   Recorded: {file_time}\n\n")
            
            file_text.config(state=tk.DISABLED)
            
            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(pady=(10, 0))
            
            def start_transcription():
                confirm_window.destroy()
                self.status_label.config(text="Transcribing recent recordings...")
                
                # Process each file in a separate thread
                def process_files():
                    try:
                        for i, (file_path, mtime) in enumerate(recent_files):
                            self.root.after(0, lambda i=i: self.status_label.config(
                                text=f"Transcribing file {i+1} of {len(recent_files)}..."))
                            
                            # Use batch transcription method that doesn't open folders
                            self.transcribe_and_extract_batch(file_path)
                            
                            # Small delay between files
                            time.sleep(1)
                        
                        self.root.after(0, lambda: self.status_label.config(text="Recent recordings transcription completed!"))
                        self.root.after(0, lambda: messagebox.showinfo("Success", "All recent recordings have been transcribed successfully!"))
                        
                    except Exception as e:
                        self.root.after(0, lambda: self.status_label.config(text="Transcription failed"))
                        self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to transcribe recordings: {str(e)}"))
                
                # Start processing in background thread
                threading.Thread(target=process_files, daemon=True).start()
            
            ttk.Button(button_frame, text="Start Transcription", command=start_transcription).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="Cancel", command=confirm_window.destroy).pack(side=tk.LEFT)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to transcribe recent recordings: {str(e)}")
    
    def show_about(self):
        """Show the About dialog with Bluvia information"""
        # Create custom about dialog with logo
        about_window = tk.Toplevel(self.root)
        about_window.title("About - Radio Transcription Tool")
        about_window.geometry("500x520")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Center the window
        about_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Main frame
        main_frame = ttk.Frame(about_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Try to load and display the Bluvia logo
        try:
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            logo_path = os.path.join(app_dir, 'Bluvia images', 'Bluvia logo.jpeg')
            if os.path.exists(logo_path) and PIL_AVAILABLE:
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
        guide_window = tk.Toplevel(self.root)
        guide_window.title("Radio Transcription Tool - User Guide")
        guide_window.geometry("600x500")  # Much more compact height
        guide_window.resizable(True, True)
        
        # Center the window
        guide_window.transient(self.root)
        guide_window.grab_set()
        
        # Create main frame with padding
        main_frame = ttk.Frame(guide_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Radio Transcription Tool - User Guide", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Guide text with proper formatting
        guide_text = """How to use the Radio Transcription Tool:

1. SELECT A RADIO STATION
   • Choose from the dropdown menu of available Dutch radio stations
   • The tool supports major Dutch radio stations including NPO Radio 1, 2, 3, etc.

2. START RECORDING
   • Click the "● Start Recording" button to begin recording
   • The tool will connect to the selected radio station and start recording
   • Recording status will be displayed in the status area

3. STOP RECORDING
   • Click the "■ Stop Recording" button to stop the recording
   • The tool will automatically process the audio file

4. TRANSCRIPTION PROCESS
   • After recording stops, transcription begins automatically
   • The tool uses OpenAI Whisper for high-quality transcription
   • Dutch language optimization is applied for better accuracy

5. KEYPOINT EXTRACTION
   • After transcription, keypoints are extracted using advanced algorithms
   • Music segments are filtered out to focus on speech content
   • Important phrases and keywords are identified and highlighted

6. OUTPUT FILES
   • All files are saved in the "Recordings+transcriptions" folder
   • Audio files, transcriptions, and keypoints are organized by date
   • Files are named with timestamps for easy identification

SETTINGS AND CONFIGURATION:
• OpenAI API Key: Set your API key in Settings menu
• Audio Cleanup: Configure automatic deletion of audio files
• Programming Info: Enable automatic programming updates

TROUBLESHOOTING:
• Ensure you have a valid OpenAI API key
• Check your internet connection for radio streaming
• Verify FFmpeg is properly installed (included in the package)

For technical support or questions, visit the Bluvia website."""
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Arial', 9))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert guide text
        text_widget.insert(tk.END, guide_text)
        text_widget.config(state=tk.DISABLED)  # Make read-only
        
        # Close button
        close_button = ttk.Button(main_frame, text="Close", command=guide_window.destroy)
        close_button.pack(pady=(10, 0))
    
    def open_bluvia_website(self):
        """Open the Bluvia website in the default browser"""
        try:
            webbrowser.open("https://www.bluvia.com")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open website: {str(e)}")
