# Transcription module for Radio Transcription Tool
import os
import sys
import openai
import time
from collections import Counter
from config import WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_PROMPT
from config import MIN_WORDS_FOR_KEYBERT, KEYBERT_PHRASE_RANGE, KEYBERT_MEDIUM_RANGE
from config import KEYBERT_WORD_RANGE, KEYBERT_TOP_N_PHRASES, KEYBERT_TOP_N_MEDIUM
from config import KEYBERT_TOP_N_WORDS, SIMILARITY_THRESHOLD
from utils import is_whisper_artifact, calculate_similarity, count_phrase_occurrences
from phrase_filtering import filter_phrases_robust, filter_words_robust, deduplicate_phrases
from logging_config import log_debug, log_transcript_info, log_fallback_info

# Import KeyBERT for keyword extraction
try:
    from keybert import KeyBERT
    keybert_available = True
    print("KeyBERT successfully imported in transcription.py")
except ImportError as e:
    keybert_available = False
    print(f"KeyBERT import failed in transcription.py: {e}")
except Exception as e:
    keybert_available = False
    print(f"KeyBERT import error in transcription.py: {e}")

def transcribe_audio_chunk(audio_file_path, chunk_index=0):
    """
    Transcribe a single audio chunk using OpenAI Whisper
    
    Args:
        audio_file_path: Path to the audio chunk file
        chunk_index: Index of the chunk (for logging)
    
    Returns:
        Transcribed text or None if failed
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            response = openai.Audio.transcribe(
                model=WHISPER_MODEL,
                file=audio_file,
                language=WHISPER_LANGUAGE,
                prompt=WHISPER_PROMPT
            )
        
        transcript = response.text.strip()
        
        # Filter out Whisper artifacts
        if is_whisper_artifact(transcript):
            log_debug(f"Filtered out Whisper artifact in chunk {chunk_index + 1}")
            return None
        
        return transcript
        
    except Exception as e:
        log_debug(f"Failed to transcribe chunk {chunk_index + 1}: {str(e)}")
        return None

def transcribe_audio_file(audio_file_path, chunk_length_ms=10*60*1000):
    """
    Transcribe an entire audio file by splitting it into chunks
    
    Args:
        audio_file_path: Path to the audio file
        chunk_length_ms: Length of each chunk in milliseconds
    
    Returns:
        Complete transcript text
    """
    try:
        from audio_processing import load_audio_file, split_audio_into_chunks, export_audio_chunk
        
        # Load audio file
        audio = load_audio_file(audio_file_path)
        if not audio:
            return None
        
        # Split into chunks
        chunks = split_audio_into_chunks(audio, chunk_length_ms)
        log_debug(f"Split audio into {len(chunks)} chunks")
        
        # Transcribe each chunk
        transcripts = []
        for i, chunk in enumerate(chunks):
            # Create temporary file for chunk
            chunk_path = f"{audio_file_path}_chunk_{i}.mp3"
            
            # Export chunk
            if export_audio_chunk(chunk, chunk_path, i):
                # Transcribe chunk
                transcript = transcribe_audio_chunk(chunk_path, i)
                if transcript:
                    transcripts.append(transcript)
                
                # Clean up chunk file
                try:
                    os.remove(chunk_path)
                except:
                    pass
        
        # Combine all transcripts
        complete_transcript = " ".join(transcripts)
        
        # Log transcript info
        word_count = len(complete_transcript.split())
        char_count = len(complete_transcript)
        log_transcript_info(word_count, char_count)
        
        return complete_transcript
        
    except Exception as e:
        log_debug(f"Failed to transcribe audio file: {str(e)}")
        return None

def extract_keypoints_with_keybert(text, stopwords):
    """
    Extract keypoints using KeyBERT
    
    Args:
        text: Text to extract keypoints from
        stopwords: Set of stopwords to filter out
    
    Returns:
        Tuple of (phrases, words) lists
    """
    if not keybert_available or not text or len(text.split()) < MIN_WORDS_FOR_KEYBERT:
        return [], []
    
    try:
        # Initialize KeyBERT
        kw_model = KeyBERT()
        
        # Extract phrases (2-8 words)
        phrases = kw_model.extract_keywords(
            text, 
            keyphrase_ngram_range=KEYBERT_PHRASE_RANGE,
            stop_words=list(stopwords),
            use_maxsum=True,
            nr_candidates=KEYBERT_TOP_N_PHRASES
        )
        
        # Extract medium phrases (2-4 words)
        medium_phrases = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=KEYBERT_MEDIUM_RANGE,
            stop_words=list(stopwords),
            use_maxsum=True,
            nr_candidates=KEYBERT_TOP_N_MEDIUM
        )
        
        # Extract single words
        words = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=KEYBERT_WORD_RANGE,
            stop_words=list(stopwords),
            use_maxsum=True,
            nr_candidates=KEYBERT_TOP_N_WORDS
        )
        
        # Filter and combine results
        filtered_phrases = filter_phrases_robust(phrases + medium_phrases, stopwords)
        filtered_words = filter_words_robust(words, stopwords)
        
        return filtered_phrases, filtered_words
        
    except Exception as e:
        log_debug(f"KeyBERT extraction failed: {str(e)}")
        return [], []

def extract_keypoints_fallback(text, stopwords):
    """
    Fallback keypoint extraction using word frequency analysis
    
    Args:
        text: Text to extract keypoints from
        stopwords: Set of stopwords to filter out
    
    Returns:
        Tuple of (phrases, words) lists
    """
    try:
        # Split text into words
        words = text.lower().split()
        
        # Filter out stopwords and short words
        filtered_words = [word for word in words if word not in stopwords and len(word) >= 3]
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        
        # Get most frequent words
        frequent_words = [(word, count) for word, count in word_counts.most_common(20)]
        
        # Extract phrases by looking for common word combinations (enhanced for longer phrases)
        phrases = []
        for i in range(len(words) - 1):
            # 2-word phrases
            phrase_2 = f"{words[i]} {words[i+1]}"
            if (words[i] not in stopwords and words[i+1] not in stopwords and 
                len(words[i]) >= 3 and len(words[i+1]) >= 3):
                phrases.append(phrase_2)
            
            # 3-word phrases
            if i < len(words) - 2:
                phrase_3 = f"{words[i]} {words[i+1]} {words[i+2]}"
                stopword_count = sum(1 for word in [words[i], words[i+1], words[i+2]] if word in stopwords)
                if stopword_count <= 1 and len(words[i]) >= 3 and len(words[i+1]) >= 3 and len(words[i+2]) >= 3:
                    phrases.append(phrase_3)
            
            # 4-word phrases (high priority)
            if i < len(words) - 3:
                phrase_4 = f"{words[i]} {words[i+1]} {words[i+2]} {words[i+3]}"
                stopword_count = sum(1 for word in [words[i], words[i+1], words[i+2], words[i+3]] if word in stopwords)
                if stopword_count <= 2 and len(words[i]) >= 3 and len(words[i+1]) >= 3 and len(words[i+2]) >= 3 and len(words[i+3]) >= 3:
                    phrases.append(phrase_4)
            
            # 5-word phrases (highest priority)
            if i < len(words) - 4:
                phrase_5 = f"{words[i]} {words[i+1]} {words[i+2]} {words[i+3]} {words[i+4]}"
                stopword_count = sum(1 for word in [words[i], words[i+1], words[i+2], words[i+3], words[i+4]] if word in stopwords)
                if stopword_count <= 2 and len(words[i]) >= 3 and len(words[i+1]) >= 3 and len(words[i+2]) >= 3 and len(words[i+3]) >= 3 and len(words[i+4]) >= 3:
                    phrases.append(phrase_5)
        
        # Count phrase frequencies
        phrase_counts = Counter(phrases)
        
        # Get most frequent phrases (increased limit for better coverage)
        frequent_phrases = [(phrase, count) for phrase, count in phrase_counts.most_common(50)]
        
        return frequent_phrases, frequent_words
        
    except Exception as e:
        log_debug(f"Fallback extraction failed: {str(e)}")
        return [], []

def extract_keypoints_with_timestamps(text, audio_duration, stopwords):
    """
    Extract keypoints with estimated timestamps
    
    Args:
        text: Transcribed text
        audio_duration: Duration of audio in seconds
        stopwords: Set of stopwords to filter out
    
    Returns:
        Dictionary mapping keypoints to their timestamps
    """
    try:
        # Extract keypoints
        if keybert_available and len(text.split()) >= MIN_WORDS_FOR_KEYBERT:
            phrases, words = extract_keypoints_with_keybert(text, stopwords)
            log_fallback_info(True, len(phrases) + len(words))
        else:
            phrases, words = extract_keypoints_fallback(text, stopwords)
            log_fallback_info(False, len(phrases) + len(words))
        
        # Create keypoint_times dictionary
        keypoint_times = {}
        
        # Add phrases with timestamps
        for phrase, _ in phrases:
            if phrase and ' ' in phrase:
                # Estimate timestamp based on phrase position in text
                timestamp = estimate_phrase_timestamp(phrase, text, audio_duration)
                keypoint_times[phrase] = [timestamp]
        
        # Add words with timestamps
        for word, _ in words:
            if word and ' ' not in word:
                # Estimate timestamp based on word position in text
                timestamp = estimate_word_timestamp(word, text, audio_duration)
                keypoint_times[word] = [timestamp]
        
        return keypoint_times
        
    except Exception as e:
        log_debug(f"Failed to extract keypoints with timestamps: {str(e)}")
        return {}

def estimate_phrase_timestamp(phrase, text, audio_duration):
    """
    Estimate timestamp for a phrase based on its position in the text
    
    Args:
        phrase: The phrase to find
        text: Complete text
        audio_duration: Duration of audio in seconds
    
    Returns:
        Estimated timestamp in seconds
    """
    try:
        # Find phrase position in text
        phrase_lower = phrase.lower()
        text_lower = text.lower()
        
        # Count occurrences
        occurrences = count_phrase_occurrences(phrase, text_lower.split())
        
        if occurrences > 0:
            # Find first occurrence
            first_occurrence = text_lower.find(phrase_lower)
            if first_occurrence != -1:
                # Estimate timestamp based on text position
                text_length = len(text)
                position_ratio = first_occurrence / text_length
                timestamp = position_ratio * audio_duration
                return timestamp
        
        return 0.0
        
    except Exception as e:
        log_debug(f"Failed to estimate phrase timestamp: {str(e)}")
        return 0.0

def estimate_word_timestamp(word, text, audio_duration):
    """
    Estimate timestamp for a word based on its position in the text
    
    Args:
        word: The word to find
        text: Complete text
        audio_duration: Duration of audio in seconds
    
    Returns:
        Estimated timestamp in seconds
    """
    try:
        # Find word position in text
        word_lower = word.lower()
        text_lower = text.lower()
        
        # Find first occurrence
        first_occurrence = text_lower.find(word_lower)
        if first_occurrence != -1:
            # Estimate timestamp based on text position
            text_length = len(text)
            position_ratio = first_occurrence / text_length
            timestamp = position_ratio * audio_duration
            return timestamp
        
        return 0.0
        
    except Exception as e:
        log_debug(f"Failed to estimate word timestamp: {str(e)}")
        return 0.0

def merge_similar_segments(segments, similarity_threshold=SIMILARITY_THRESHOLD):
    """
    Merge similar text segments to reduce redundancy
    
    Args:
        segments: List of text segments
        similarity_threshold: Threshold for considering segments similar
    
    Returns:
        List of merged segments
    """
    if not segments:
        return []
    
    merged_segments = []
    used_indices = set()
    
    for i, segment1 in enumerate(segments):
        if i in used_indices:
            continue
        
        # Find similar segments to merge
        similar_segments = [segment1]
        for j, segment2 in enumerate(segments[i+1:], i+1):
            if j in used_indices:
                continue
            
            similarity = calculate_similarity(segment1, segment2)
            if similarity >= similarity_threshold:
                similar_segments.append(segment2)
                used_indices.add(j)
        
        # Merge similar segments
        if len(similar_segments) > 1:
            # Combine segments and remove duplicates
            combined_text = " ".join(similar_segments)
            # Simple deduplication by removing repeated phrases
            words = combined_text.split()
            unique_words = []
            seen_phrases = set()
            
            for k in range(len(words) - 2):
                phrase = " ".join(words[k:k+3])
                if phrase not in seen_phrases:
                    unique_words.append(words[k])
                    seen_phrases.add(phrase)
            
            # Add remaining words
            unique_words.extend(words[len(words)-2:])
            merged_segment = " ".join(unique_words)
        else:
            merged_segment = segment1
        
        merged_segments.append(merged_segment)
        used_indices.add(i)
    
    return merged_segments

def filter_music_content(text, music_patterns):
    """
    Filter out music-related content from text
    
    Args:
        text: Text to filter
        music_patterns: Dictionary of music filtering patterns
    
    Returns:
        Filtered text with music content removed
    """
    try:
        words = text.split()
        filtered_words = []
        
        for word in words:
            word_lower = word.lower()
            
            # Check if word is music-related
            is_music = False
            for category, patterns in music_patterns.items():
                if any(pattern in word_lower for pattern in patterns):
                    is_music = True
                    break
            
            if not is_music:
                filtered_words.append(word)
        
        return " ".join(filtered_words)
        
    except Exception as e:
        log_debug(f"Failed to filter music content: {str(e)}")
        return text

def enhance_transcript_quality(transcript):
    """
    Enhance transcript quality by cleaning up common issues
    
    Args:
        transcript: Raw transcript text
    
    Returns:
        Enhanced transcript
    """
    try:
        # Remove extra whitespace
        transcript = " ".join(transcript.split())
        
        # Fix common transcription errors
        replacements = {
            " uh ": " ",
            " um ": " ",
            " er ": " ",
            " ah ": " ",
            "  ": " ",
            " ,": ",",
            " .": ".",
            " !": "!",
            " ?": "?",
        }
        
        for old, new in replacements.items():
            transcript = transcript.replace(old, new)
        
        # Capitalize sentences
        sentences = transcript.split(". ")
        capitalized_sentences = []
        for sentence in sentences:
            if sentence:
                sentence = sentence.strip()
                if sentence:
                    sentence = sentence[0].upper() + sentence[1:]
                    capitalized_sentences.append(sentence)
        
        transcript = ". ".join(capitalized_sentences)
        
        return transcript
        
    except Exception as e:
        log_debug(f"Failed to enhance transcript quality: {str(e)}")
        return transcript

def extract_keypoints(transcript_text):
    """
    Main function to extract keypoints from transcript text
    
    Args:
        transcript_text: The transcribed text
    
    Returns:
        Dictionary with keypoints and their timestamps, or None if failed
    """
    try:
        from config import DUTCH_STOPWORDS
        
        if not transcript_text or not transcript_text.strip():
            log_debug("No transcript text provided for keypoint extraction")
            return None
        
        # Enhance transcript quality first
        enhanced_transcript = enhance_transcript_quality(transcript_text)
        
        # Extract keypoints with timestamps (using estimated duration)
        # For now, we'll use a default duration of 30 minutes (1800 seconds)
        audio_duration = 30 * 60  # 30 minutes in seconds
        
        keypoints = extract_keypoints_with_timestamps(enhanced_transcript, audio_duration, DUTCH_STOPWORDS)
        
        if keypoints:
            log_debug(f"Successfully extracted {len(keypoints)} keypoints")
            return keypoints
        else:
            log_debug("No keypoints extracted from transcript")
            return None
            
    except Exception as e:
        log_debug(f"Failed to extract keypoints: {str(e)}")
        return None
