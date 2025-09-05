# Audio processing module for Radio Transcription Tool
import os
import sys
import subprocess
import time
import threading
import math
from pydub import AudioSegment
from config import CHUNK_LENGTH_MS, SAMPLE_RATE, CHANNELS, BITRATE
from utils import get_executable_path, get_silent_subprocess_params, get_output_filename
from logging_config import log_debug

def record_radio_stream(station_url, output_path, duration_minutes, progress_callback=None):
    """
    Record radio stream using ffmpeg
    
    Args:
        station_url: URL of the radio stream
        output_path: Path where to save the recording
        duration_minutes: Duration in minutes
        progress_callback: Optional callback function for progress updates
    
    Returns:
        True if successful, False otherwise
    """
    try:
        ffmpeg_path = get_executable_path("ffmpeg.exe")
        startupinfo, creationflags = get_silent_subprocess_params()
        
        # Calculate duration in seconds
        duration_seconds = duration_minutes * 60
        
        # FFmpeg command to record stream
        cmd = [
            ffmpeg_path,
            "-i", station_url,
            "-t", str(duration_seconds),
            "-acodec", "mp3",
            "-ab", BITRATE,
            "-ac", str(CHANNELS),
            "-ar", str(SAMPLE_RATE),
            "-y",  # Overwrite output file
            output_path
        ]
        
        log_debug(f"Starting radio recording: {os.path.basename(output_path)}")
        
        # Start recording process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=creationflags
        )
        
        # Monitor progress if callback provided
        if progress_callback:
            start_time = time.time()
            while process.poll() is None:
                elapsed = time.time() - start_time
                progress = min((elapsed / duration_seconds) * 100, 100)
                progress_callback(progress)
                time.sleep(1)
        
        # Wait for process to complete
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            log_debug(f"Recording completed successfully: {os.path.basename(output_path)}")
            return True
        else:
            log_debug(f"Recording failed with return code {process.returncode}")
            return False
            
    except Exception as e:
        log_debug(f"Recording error: {str(e)}")
        return False

def load_audio_file(audio_path):
    """
    Load audio file using pydub
    
    Args:
        audio_path: Path to the audio file
    
    Returns:
        AudioSegment object or None if failed
    """
    try:
        log_debug(f"Loading audio file with FFMPEG: {os.path.basename(audio_path)}")
        audio = AudioSegment.from_file(audio_path)
        return audio
    except Exception as e:
        log_debug(f"Failed to load audio file: {str(e)}")
        return None

def split_audio_into_chunks(audio, chunk_length_ms=CHUNK_LENGTH_MS):
    """
    Split audio into chunks for processing
    
    Args:
        audio: AudioSegment object
        chunk_length_ms: Length of each chunk in milliseconds
    
    Returns:
        List of AudioSegment chunks
    """
    chunks = []
    total_length = len(audio)
    
    for i in range(0, total_length, chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        if len(chunk) > 0:
            chunks.append(chunk)
    
    return chunks

def export_audio_chunk(chunk, output_path, chunk_index):
    """
    Export audio chunk to file
    
    Args:
        chunk: AudioSegment chunk
        output_path: Path where to save the chunk
        chunk_index: Index of the chunk (for logging)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if chunk_index == 0:  # Only log the first chunk export
            log_debug(f"Exporting chunk {chunk_index + 1} with FFMPEG: {os.path.basename(output_path)}")
        
        chunk.export(output_path, format="mp3")
        return True
    except Exception as e:
        log_debug(f"Failed to export chunk {chunk_index + 1}: {str(e)}")
        return False

def cleanup_audio_files(file_paths):
    """
    Clean up temporary audio files
    
    Args:
        file_paths: List of file paths to delete
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                log_debug(f"Cleaned up audio file: {os.path.basename(file_path)}")
        except Exception as e:
            log_debug(f"Failed to clean up {file_path}: {str(e)}")

def get_audio_info(audio_path):
    """
    Get information about an audio file
    
    Args:
        audio_path: Path to the audio file
    
    Returns:
        Dictionary with audio information or None if failed
    """
    try:
        audio = AudioSegment.from_file(audio_path)
        return {
            'duration_seconds': len(audio) / 1000.0,
            'duration_minutes': len(audio) / 60000.0,
            'sample_rate': audio.frame_rate,
            'channels': audio.channels,
            'bitrate': audio.frame_rate * audio.channels * audio.sample_width * 8
        }
    except Exception as e:
        log_debug(f"Failed to get audio info: {str(e)}")
        return None

def normalize_audio(audio, target_dBFS=-20.0):
    """
    Normalize audio to target dBFS level
    
    Args:
        audio: AudioSegment object
        target_dBFS: Target dBFS level
    
    Returns:
        Normalized AudioSegment
    """
    try:
        # Calculate the difference between current and target level
        change_in_dBFS = target_dBFS - audio.dBFS
        
        # Apply the change
        normalized_audio = audio.apply_gain(change_in_dBFS)
        
        return normalized_audio
    except Exception as e:
        log_debug(f"Failed to normalize audio: {str(e)}")
        return audio

def filter_audio_quality(audio, min_dBFS=-50.0):
    """
    Filter out low-quality audio segments
    
    Args:
        audio: AudioSegment object
        min_dBFS: Minimum dBFS level to consider as valid audio
    
    Returns:
        Filtered AudioSegment
    """
    try:
        # Split into smaller segments for analysis
        segment_length = 1000  # 1 second segments
        segments = []
        
        for i in range(0, len(audio), segment_length):
            segment = audio[i:i + segment_length]
            if segment.dBFS > min_dBFS:
                segments.append(segment)
        
        if segments:
            # Concatenate valid segments
            filtered_audio = segments[0]
            for segment in segments[1:]:
                filtered_audio += segment
            return filtered_audio
        else:
            return audio
            
    except Exception as e:
        log_debug(f"Failed to filter audio quality: {str(e)}")
        return audio

def convert_audio_format(input_path, output_path, output_format="mp3", bitrate="64k"):
    """
    Convert audio file to different format
    
    Args:
        input_path: Path to input audio file
        output_path: Path to output audio file
        output_format: Output format (mp3, wav, etc.)
        bitrate: Output bitrate
    
    Returns:
        True if successful, False otherwise
    """
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format=output_format, bitrate=bitrate)
        return True
    except Exception as e:
        log_debug(f"Failed to convert audio format: {str(e)}")
        return False

def merge_audio_files(file_paths, output_path):
    """
    Merge multiple audio files into one
    
    Args:
        file_paths: List of paths to audio files
        output_path: Path to output merged file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not file_paths:
            return False
        
        # Load first file
        merged_audio = AudioSegment.from_file(file_paths[0])
        
        # Merge with remaining files
        for file_path in file_paths[1:]:
            audio = AudioSegment.from_file(file_path)
            merged_audio += audio
        
        # Export merged audio
        merged_audio.export(output_path, format="mp3")
        return True
        
    except Exception as e:
        log_debug(f"Failed to merge audio files: {str(e)}")
        return False

def get_audio_spectrum(audio, fft_size=1024):
    """
    Get audio spectrum for analysis
    
    Args:
        audio: AudioSegment object
        fft_size: FFT size for spectrum analysis
    
    Returns:
        List of frequency bins and their magnitudes
    """
    try:
        # Convert to numpy array for analysis
        samples = audio.get_array_of_samples()
        
        # Simple spectrum analysis (this is a basic implementation)
        # In a real application, you might want to use more sophisticated analysis
        import numpy as np
        
        # Take a sample of the audio for analysis
        sample_length = min(len(samples), 44100)  # 1 second sample
        sample = samples[:sample_length]
        
        # Apply FFT
        fft = np.fft.fft(sample, fft_size)
        magnitude = np.abs(fft[:fft_size//2])
        
        # Create frequency bins
        freqs = np.fft.fftfreq(fft_size, 1/audio.frame_rate)[:fft_size//2]
        
        return list(zip(freqs, magnitude))
        
    except Exception as e:
        log_debug(f"Failed to get audio spectrum: {str(e)}")
        return []

def detect_silence(audio, silence_thresh=-50.0, min_silence_len=1000):
    """
    Detect silent segments in audio
    
    Args:
        audio: AudioSegment object
        silence_thresh: Silence threshold in dBFS
        min_silence_len: Minimum silence length in milliseconds
    
    Returns:
        List of (start, end) tuples for silent segments
    """
    try:
        # Use pydub's built-in silence detection
        silent_ranges = AudioSegment.silence.detect_silence(
            audio, 
            min_silence_len=min_silence_len, 
            silence_thresh=silence_thresh
        )
        
        return silent_ranges
        
    except Exception as e:
        log_debug(f"Failed to detect silence: {str(e)}")
        return []

def remove_silence(audio, silence_thresh=-50.0, min_silence_len=1000):
    """
    Remove silent segments from audio
    
    Args:
        audio: AudioSegment object
        silence_thresh: Silence threshold in dBFS
        min_silence_len: Minimum silence length in milliseconds
    
    Returns:
        AudioSegment with silence removed
    """
    try:
        # Detect silent ranges
        silent_ranges = detect_silence(audio, silence_thresh, min_silence_len)
        
        if not silent_ranges:
            return audio
        
        # Create new audio without silent segments
        non_silent_audio = AudioSegment.empty()
        last_end = 0
        
        for start, end in silent_ranges:
            # Add non-silent segment before this silence
            if start > last_end:
                non_silent_audio += audio[last_end:start]
            last_end = end
        
        # Add remaining audio after last silence
        if last_end < len(audio):
            non_silent_audio += audio[last_end:]
        
        return non_silent_audio
        
    except Exception as e:
        log_debug(f"Failed to remove silence: {str(e)}")
        return audio
