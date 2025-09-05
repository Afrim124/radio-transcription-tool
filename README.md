# Radio Transcription Tool v3.7 - Modular Structure

## Overview

The Radio Transcription Tool has been refactored into a modular structure for better maintainability, readability, and scalability. The original monolithic file has been split into focused modules following common programming standards.

## Module Structure

### Core Modules

1. **`main.py`** - Main entry point
   - Application initialization
   - Module imports
   - Main function

2. **`config.py`** - Configuration and constants
   - Version information
   - Dutch stopwords
   - Music filtering patterns
   - Radio station database
   - Audio processing settings
   - Transcription settings
   - Keypoint extraction settings

3. **`logging_config.py`** - Logging setup and configuration
   - Setup logging function
   - Logging helper functions
   - Centralized logging management

4. **`utils.py`** - Utility functions
   - File path management
   - Configuration loading/saving
   - Similarity calculations
   - Whisper artifact detection

### Feature Modules

5. **`gui.py`** - GUI-related code
   - Main application window
   - Menu system
   - User interface components
   - Event handling

6. **`audio_processing.py`** - Audio recording and processing
   - Radio stream recording
   - Audio file loading
   - Chunk splitting and export
   - Audio quality enhancement
   - Silence detection and removal

7. **`transcription.py`** - Transcription and keypoint extraction
   - OpenAI Whisper integration
   - KeyBERT keypoint extraction
   - Fallback extraction methods
   - Timestamp estimation
   - Music content filtering

8. **`phrase_filtering.py`** - Phrase filtering and processing
   - Complete thought detection
   - Robust phrase filtering
   - Phrase merging and deduplication
   - Word filtering

9. **`app.py`** - Main application coordination
   - High-level workflow coordination
   - Result processing and formatting
   - File I/O operations

## Benefits of Modular Structure

### 1. Maintainability
- Each module has a single responsibility
- Easier to locate and modify specific functionality
- Reduced code complexity per file

### 2. Readability
- Much easier to understand individual components
- Clear separation of concerns
- Better code organization

### 3. Reusability
- Functions can be imported and used independently
- Modules can be tested separately
- Easier to extend with new features

### 4. Scalability
- Easy to add new modules for new features
- Simple to modify existing modules
- Better support for team development

### 5. Testing
- Individual modules can be unit tested
- Easier to mock dependencies
- Better test coverage

## Usage

### Running the Application

```bash
# Run the main application
python main.py

# Or run the app module directly
python app.py
```

### Importing Modules

```python
# Import specific functionality
from config import VERSION, DUTCH_STOPWORDS
from audio_processing import record_radio_stream
from transcription import transcribe_audio_file
from phrase_filtering import filter_phrases_robust

# Use the functionality
results = transcribe_audio_file("audio.mp3")
```

### Building Executable

```bash
# Build with PyInstaller
pyinstaller Radio_transcription_tool_Bluvia_v3.7_Optimized.spec
```

## File Organization

```
Radio_transcription_tool v2.0/
├── main.py                    # Main entry point
├── app.py                     # Application coordination
├── config.py                  # Configuration and constants
├── logging_config.py          # Logging setup
├── utils.py                   # Utility functions
├── gui.py                     # GUI components
├── audio_processing.py        # Audio processing
├── transcription.py           # Transcription logic
├── phrase_filtering.py        # Phrase filtering
├── requirements_modular.txt   # Dependencies
├── README_MODULAR.md          # This file
└── ... (other files)
```

## Dependencies

See `requirements_modular.txt` for the complete list of dependencies.

### Core Dependencies
- `openai` - OpenAI API integration
- `pydub` - Audio processing
- `tkinter` - GUI framework

### Optional Dependencies
- `keybert` - Keypoint extraction
- `sentence-transformers` - NLP processing
- `transformers` - Transformer models
- `torch` - PyTorch for ML models

## Migration from Monolithic Structure

The modular structure maintains full compatibility with the original functionality while providing better organization:

1. **Configuration**: All constants moved to `config.py`
2. **Logging**: Centralized in `logging_config.py`
3. **Utilities**: Common functions in `utils.py`
4. **GUI**: Interface code in `gui.py`
5. **Audio**: Processing logic in `audio_processing.py`
6. **Transcription**: Core logic in `transcription.py`
7. **Filtering**: Phrase processing in `phrase_filtering.py`
8. **Coordination**: High-level workflow in `app.py`

## Development Guidelines

### Adding New Features

1. **Identify the appropriate module** for your feature
2. **Add functions** to the relevant module
3. **Update imports** in other modules if needed
4. **Test the functionality** independently
5. **Update documentation** as needed

### Modifying Existing Features

1. **Locate the relevant module** using the structure guide
2. **Make changes** to the specific module
3. **Test the changes** thoroughly
4. **Update related modules** if necessary

### Code Style

- Follow Python PEP 8 guidelines
- Use descriptive function and variable names
- Add docstrings to all functions
- Keep modules focused on their specific purpose
- Use type hints where appropriate

## Troubleshooting

### Import Errors

If you encounter import errors:

1. **Check module paths** - Ensure all modules are in the same directory
2. **Verify dependencies** - Install required packages from `requirements_modular.txt`
3. **Check Python path** - Ensure the project directory is in your Python path

### Missing Dependencies

Install missing dependencies:

```bash
pip install -r requirements_modular.txt
```

### Module Not Found

Ensure all modules are present and properly named:
- `config.py`
- `logging_config.py`
- `utils.py`
- `gui.py`
- `audio_processing.py`
- `transcription.py`
- `phrase_filtering.py`
- `app.py`

## Support

For issues with the modular structure:

1. **Check the module structure** against this documentation
2. **Verify all dependencies** are installed
3. **Test individual modules** to isolate issues
4. **Check the original monolithic file** for reference if needed

The modular structure provides the same functionality as the original monolithic version while offering significant improvements in maintainability and extensibility.
