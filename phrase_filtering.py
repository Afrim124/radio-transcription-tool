# Phrase filtering and processing for Radio Transcription Tool
import re
from collections import Counter
from config import DUTCH_STOPWORDS

def is_complete_thought(phrase):
    """
    Check if a phrase forms a complete thought rather than an incomplete fragment.
    
    Args:
        phrase: The phrase to check
        
    Returns:
        True if the phrase appears to be complete, False if it's an incomplete fragment
    """
    if not phrase or len(phrase.strip()) < 5:
        return False
    
    # Common incomplete patterns
    incomplete_patterns = [
        # Phrases that start with common incomplete words
        'moet zorgen voor een', 'het ook een beetje', 'ik zeggen het glas',
        'er zijn bijna geen', 'zou ik zeggen het', 'maar ik heb het',
        'ik heb het ook', 'van ga ik wel', 'ik zeg nooit',
        
        # General patterns for incomplete fragments
        'voor een', 'een beetje', 'zeggen het', 'bijna geen', 'zeggen het',
        'heb het', 'heb het ook', 'ga ik wel', 'zeg nooit',
        
        # Phrases that end with incomplete words
        'voor een', 'een beetje', 'het glas', 'bijna geen', 'het ook',
        'heb het', 'heb het ook', 'ik wel', 'zeg nooit'
    ]
    
    phrase_lower = phrase.lower().strip()
    
    # Check against incomplete patterns
    for pattern in incomplete_patterns:
        if pattern in phrase_lower:
            return False
    
    # Check if phrase starts or ends with common incomplete words
    incomplete_start_words = {'moet', 'het', 'ik', 'er', 'zou', 'maar', 'van', 'zeg'}
    incomplete_end_words = {'een', 'beetje', 'glas', 'geen', 'het', 'ook', 'wel', 'nooit'}
    
    words = phrase_lower.split()
    if len(words) >= 2:
        if words[0] in incomplete_start_words and words[-1] in incomplete_end_words:
            return False
    
    # Check for phrases that are too generic
    generic_phrases = {
        'ik zeg', 'ik heb', 'het is', 'dat is', 'er zijn', 'er is',
        'ik ben', 'ik ga', 'ik doe', 'ik wil', 'ik kan', 'ik moet'
    }
    
    if phrase_lower in generic_phrases:
        return False
    
    return True

def filter_phrases_robust(phrases, stopwords, max_stopword_ratio=0.8):
    """
    Filter phrases based on stopword content with robust error handling.
    Optimized to prioritize longer, more meaningful phrases and minimize 2-word phrases.
    
    Strategy:
    - Remove phrases that are too short (less than 3 words)
    - Remove phrases that start or end with stopwords
    - Remove phrases with too many stopwords
    - Prioritize longer phrases over shorter ones
    - Remove incomplete sentence fragments
    - Remove phrases that don't form complete thoughts
    
    Args:
        phrases: List of phrases to filter
        stopwords: Set of stopwords to check against
        max_stopword_ratio: Maximum ratio of stopwords allowed in a phrase
    
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
                    
                    # Additional check: ensure phrase is a complete thought
                    if not is_complete_thought(phrase):
                        continue  # Skip incomplete fragments
                    
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

def merge_overlapping_phrases(phrases):
    """
    Merge overlapping phrases into longer, more complete phrases.
    
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
        
        # Look for phrases that can be merged with this one
        for j, other_phrase in enumerate(sorted_phrases[i+1:], i+1):
            if j in used_indices:
                continue
            
            # Check if phrases overlap significantly
            if can_merge_phrases(phrase, other_phrase):
                # Merge the phrases
                merged = merge_two_phrases(phrase, other_phrase)
                if merged:
                    merged_phrases.append(merged)
                    used_indices.add(i)
                    used_indices.add(j)
                    break
        
        # If no merge was found, keep the original phrase
        if i not in used_indices:
            merged_phrases.append(phrase)
    
    return merged_phrases

def can_merge_phrases(phrase1, phrase2):
    """Check if two phrases can be merged based on overlap"""
    words1 = set(phrase1.lower().split())
    words2 = set(phrase2.lower().split())
    
    # Calculate overlap
    overlap = len(words1.intersection(words2))
    total_unique = len(words1.union(words2))
    
    # Require at least 50% overlap to consider merging
    return overlap / total_unique >= 0.5 if total_unique > 0 else False

def merge_two_phrases(phrase1, phrase2):
    """Merge two overlapping phrases into a longer phrase"""
    words1 = phrase1.lower().split()
    words2 = phrase2.lower().split()
    
    # Find the longest common subsequence
    common_words = []
    for word in words1:
        if word in words2:
            common_words.append(word)
    
    if len(common_words) >= 2:
        # Create merged phrase by combining unique words
        all_words = list(dict.fromkeys(words1 + words2))  # Preserve order, remove duplicates
        return ' '.join(all_words)
    
    return None

def remove_true_subphrases(phrases):
    """
    Remove phrases that are true sub-phrases of longer phrases.
    
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
        
        # Check if this phrase is contained within any longer phrase
        is_subphrase = False
        for longer_phrase in filtered_phrases:
            longer_lower = longer_phrase.lower().strip()
            if phrase_lower in longer_lower and phrase_lower != longer_lower:
                is_subphrase = True
                break
        
        if not is_subphrase:
            filtered_phrases.append(phrase)
    
    return filtered_phrases

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
        
        if not merged:
            phrase_dict[normalized_phrase] = (phrase, timestamps)
    
    return list(phrase_dict.values())

def filter_words_robust(keywords, stopwords):
    """Filter words based on stopwords and length"""
    if not keywords or not stopwords:
        return []
    
    filtered_words = []
    
    try:
        for kw in keywords:
            if not isinstance(kw, (list, tuple)) or len(kw) == 0:
                continue
                
            word = str(kw[0]) if kw[0] is not None else ""
            if not word or ' ' in word:  # Skip phrases, only process single words
                continue
                
            # Filter out stopwords and very short words
            if word.lower() not in stopwords and len(word) >= 3:
                filtered_words.append(word)
                
    except Exception:
        # If filtering fails, return original words
        return [kw[0] for kw in keywords if isinstance(kw, (list, tuple)) and len(kw) > 0 and kw[0] is not None and ' ' not in str(kw[0])]
    
    return filtered_words
