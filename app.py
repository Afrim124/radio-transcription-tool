# Main application module for Radio Transcription Tool
import os
import sys
import time
import threading
from datetime import datetime

# Import our modules
from config import VERSION, DUTCH_STOPWORDS, MUSIC_FILTER_PATTERNS, RADIO_STATIONS
from config import CHUNK_LENGTH_MS, WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_PROMPT
from config import MIN_WORDS_FOR_KEYBERT, KEYBERT_PHRASE_RANGE, KEYBERT_MEDIUM_RANGE
from config import KEYBERT_WORD_RANGE, KEYBERT_TOP_N_PHRASES, KEYBERT_TOP_N_MEDIUM
from config import KEYBERT_TOP_N_WORDS, SIMILARITY_THRESHOLD
from logging_config import setup_logging, log_recording_start, log_transcript_info
from logging_config import log_fallback_info, log_recording_complete, log_results, log_success
from phrase_filtering import filter_phrases_robust, filter_words_robust, deduplicate_phrases
from phrase_filtering import is_complete_thought
from utils import get_executable_path, get_silent_subprocess_params, is_whisper_artifact
from utils import get_output_filename, load_openai_api_key, save_openai_api_key
from utils import load_audio_cleanup_config, save_audio_cleanup_config
from utils import load_programming_config, save_programming_config, remove_openai_api_key
from utils import calculate_similarity, count_phrase_occurrences
from audio_processing import record_radio_stream, load_audio_file, split_audio_into_chunks
from audio_processing import export_audio_chunk, cleanup_audio_files, get_audio_info
from transcription import transcribe_audio_file, extract_keypoints_with_timestamps
from transcription import filter_music_content, enhance_transcript_quality

# Import pydub for audio processing
try:
    from pydub import AudioSegment
except ImportError:
    print("pydub not available")

# Import KeyBERT for keyword extraction
try:
    from keybert import KeyBERT
    keybert_available = True
    print("KeyBERT successfully imported")
except ImportError as e:
    keybert_available = False
    print(f"KeyBERT import failed: {e}")
except Exception as e:
    keybert_available = False
    print(f"KeyBERT import error: {e}")

# Configure pydub to use ffmpeg from bin directory
bin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
ffmpeg_path = os.path.join(bin_dir, 'ffmpeg.exe')
if os.path.exists(ffmpeg_path):
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
else:
    AudioSegment.converter = "ffmpeg"
    AudioSegment.ffmpeg = "ffmpeg"

class RadioTranscriptionApp:
    """Main application class that coordinates all components"""
    
    def __init__(self):
        self.recording = False
        self.recording_thread = None
        self.recording_process = None
        self.recording_start_time = None
        self.recording_duration = 0
        
        # Load configurations
        self.audio_cleanup_enabled = load_audio_cleanup_config()
        self.programming_enabled = load_programming_config()
        
        # Setup logging
        setup_logging()
    
    def record_and_transcribe(self, station_name, duration_minutes, progress_callback=None, status_callback=None):
        """
        Main function to record and transcribe radio stream
        
        Args:
            station_name: Name of the radio station
            duration_minutes: Duration in minutes
            progress_callback: Optional callback for progress updates
            status_callback: Optional callback for status updates
        
        Returns:
            Dictionary with results
        """
        try:
            # Get station URL
            if station_name not in RADIO_STATIONS:
                raise ValueError(f"Unknown radio station: {station_name}")
            
            station_url = RADIO_STATIONS[station_name]
            
            # Generate output filename
            output_path = get_output_filename(station_name)
            recording_name = os.path.basename(output_path)
            
            # Log recording start
            log_recording_start(recording_name)
            
            if status_callback:
                status_callback("Recording...")
            
            # Record radio stream
            success = record_radio_stream(
                station_url, 
                output_path, 
                duration_minutes, 
                progress_callback
            )
            
            if not success:
                raise Exception("Failed to record radio stream")
            
            if status_callback:
                status_callback("Transcribing...")
            
            # Transcribe audio
            transcript = transcribe_audio_file(output_path)
            if not transcript:
                raise Exception("Failed to transcribe audio")
            
            # Enhance transcript quality
            transcript = enhance_transcript_quality(transcript)
            
            # Filter music content
            transcript = filter_music_content(transcript, MUSIC_FILTER_PATTERNS)
            
            if status_callback:
                status_callback("Extracting keypoints...")
            
            # Get audio duration for timestamp estimation
            audio_info = get_audio_info(output_path)
            audio_duration = audio_info['duration_seconds'] if audio_info else duration_minutes * 60
            
            # Extract keypoints with timestamps
            keypoint_times = extract_keypoints_with_timestamps(
                transcript, 
                audio_duration, 
                DUTCH_STOPWORDS
            )
            
            # Process keypoints
            results = self.process_keypoints(keypoint_times, transcript)
            
            # Clean up audio file if enabled
            if self.audio_cleanup_enabled:
                try:
                    os.remove(output_path)
                except:
                    pass
            
            if status_callback:
                status_callback("Complete")
            
            return results
            
        except Exception as e:
            if status_callback:
                status_callback(f"Error: {str(e)}")
            raise e
    
    def process_keypoints(self, keypoint_times, transcript):
        """
        Process extracted keypoints and create results
        
        Args:
            keypoint_times: Dictionary mapping keypoints to timestamps
            transcript: Complete transcript text
        
        Returns:
            Dictionary with processed results
        """
        try:
            # Separate words and phrases
            words_with_times = [(kp, times) for kp, times in keypoint_times.items() if ' ' not in kp and times]
            phrases_with_times = [(kp, times) for kp, times in keypoint_times.items() if ' ' in kp and times]
            
            # Deduplicate phrases
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
            
            # Count results
            word_count = len(words_with_times)
            phrase_count = len(deduplicated_phrases)
            total_keypoints = word_count + phrase_count
            
            # Log results
            log_recording_complete("recording", total_keypoints)
            log_results(total_keypoints, word_count, phrase_count)
            
            if total_keypoints > 0:
                log_success()
            
            # Create results dictionary
            results = {
                'total_keypoints': total_keypoints,
                'word_count': word_count,
                'phrase_count': phrase_count,
                'keypoint_times': keypoint_times,
                'transcript': transcript,
                'words': [kp for kp, times in words_with_times],
                'phrases': [kp for kp, times in deduplicated_phrases]
            }
            
            return results
            
        except Exception as e:
            print(f"Error processing keypoints: {str(e)}")
            return {
                'total_keypoints': 0,
                'word_count': 0,
                'phrase_count': 0,
                'keypoint_times': {},
                'transcript': transcript,
                'words': [],
                'phrases': []
            }
    
    def format_results(self, results):
        """
        Format results for display
        
        Args:
            results: Results dictionary
        
        Returns:
            Formatted string
        """
        try:
            output = []
            output.append(f"=== RADIO TRANSCRIPTION RESULTS ===")
            output.append(f"Total Keypoints: {results['total_keypoints']}")
            output.append(f"Words: {results['word_count']}")
            output.append(f"Phrases: {results['phrase_count']}")
            output.append("")
            
            # Add phrases
            if results['phrases']:
                output.append("=== PHRASES ===")
                for i, phrase in enumerate(results['phrases'][:10], 1):  # Show top 10
                    times = results['keypoint_times'].get(phrase, [0.0])
                    time_str = ", ".join([f"{t:.1f}s" for t in times])
                    output.append(f"{i}. \"{phrase}\": {time_str}")
                output.append("")
            
            # Add words
            if results['words']:
                output.append("=== WORDS ===")
                for i, word in enumerate(results['words'][:10], 1):  # Show top 10
                    times = results['keypoint_times'].get(word, [0.0])
                    time_str = ", ".join([f"{t:.1f}s" for t in times])
                    output.append(f"{i}. \"{word}\": {time_str}")
                output.append("")
            
            # Add transcript preview
            if results['transcript']:
                output.append("=== TRANSCRIPT PREVIEW ===")
                transcript_preview = results['transcript'][:500] + "..." if len(results['transcript']) > 500 else results['transcript']
                output.append(transcript_preview)
            
            return "\n".join(output)
            
        except Exception as e:
            return f"Error formatting results: {str(e)}"
    
    def save_results_to_file(self, results, output_path):
        """
        Save results to file
        
        Args:
            results: Results dictionary
            output_path: Path to save results
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Format results
            formatted_results = self.format_results(results)
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_results)
            
            # Also save raw transcript
            transcript_path = output_path.replace('.txt', '_transcript.txt')
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(results['transcript'])
            
        except Exception as e:
            print(f"Error saving results: {str(e)}")

def main():
    """Main entry point for the Radio Transcription Tool"""
    # Load OpenAI API key
    api_key = load_openai_api_key()
    if not api_key:
        print("Warning: OpenAI API key not found. Please set it in the application.")
    
    # Create and run the main application
    app = RadioTranscriptionApp()
    
    # This would typically be called from the GUI
    # For now, just demonstrate the structure
    print(f"Radio Transcription Tool v{VERSION} initialized successfully")
    print("Use the GUI to start recording and transcription")

if __name__ == "__main__":
    main()
