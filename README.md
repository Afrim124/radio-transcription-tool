# Radio Transcription Tool v3.5

A professional Python application for recording and transcribing Dutch and Belgian radio streams using OpenAI Whisper API, with enhanced music detection, improved phrase detection, comprehensive logging, and advanced deduplication powered by Bluvia.

##    Latest Version: v3.5

**Major improvements in reliability and debugging!** 

- **Comprehensive logging system** for both script and executable versions
- **Enhanced fallback mechanism** that triggers more reliably
- **Fixed overlapping phrase generation** for cleaner keypoints
- **Better error handling** and debugging information
- **Improved phrase deduplication** to eliminate repetitive content

### 📥 Download
- [v3.5 Release] https://sourceforge.net/projects/radio-transcription-tool/
- [Previous versions] https://sourceforge.net/projects/radio-transcription-tool/

## 🎯 Features

- **Live Radio Recording**: Record streams from 40+ Dutch and Belgian radio stations
- **Live Stream Listening**: Listen to radio streams without recording
- **AI Transcription**: High-quality transcription using OpenAI Whisper API
- **Smart Keyword Extraction**: Advanced phrase analysis with KeyBERT, prioritizing longer meaningful phrases
- **Comprehensive Logging**: Detailed logging system for debugging and monitoring
- **Enhanced Fallback System**: Robust fallback mechanism when KeyBERT is unavailable
- **Professional UI**: Modern Tkinter interface with Bluvia branding
- **Organized Output**: Timestamped folders with MP3 recordings and transcriptions
- **API Key Management**: Built-in OpenAI API key configuration

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- FFmpeg (included in `bin/` folder)

### Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/radio-transcription-tool.git
   cd radio-transcription-tool
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your OpenAI API key:**
   - Run the application
   - Go to `Settings` → `Set OpenAI API Key`
   - Enter your OpenAI API key (starts with 'sk-')

4. **Run the application:**
   ```bash
   python radio_transcription_final_build_clean.py
   ```

## 🏗️ Building the Executable

### Prerequisites
- PyInstaller: `pip install pyinstaller`

### Build Process
1. **Use the optimized spec file (this is the correct one):**
   ```bash
   pyinstaller Radio_transcription_tool_Bluvia_v3.5_Optimized.spec
   ```

2. **Copy FFmpeg binaries:**
   ```bash
   # Copy the bin folder to the dist directory
   xcopy "bin" "dist\bin" /E /I
   ```

**Note**: The spec file `Radio_transcription_tool_Bluvia_v3.5_Optimized.spec` is already configured correctly and points to the clean build file.

### Build Results
- **Executable size**: ~29MB (optimized)
- **Full package size**: ~35MB (with FFmpeg)
- **All images and icons included**

## 📁 Project Structure

```
Radio_transcription_tool/
├── radio_transcription_final_build_clean.py    # Main application
├── Radio_transcription_tool_Bluvia_v3.5_Optimized.spec  # PyInstaller spec
├── Bluvia images/                       # Application images and icons
│   ├── Bluebird app icon 2a.ico        # Main application icon
│   ├── Bluvia logo.jpeg                # About screen logo
│   └── Bluebird favicon.jpeg           # UI favicon
├── bin/                                 # External executables
│   ├── ffmpeg.exe                      # Audio processing
│   └── ffplay.exe                      # Live stream playback
├── build/                               # PyInstaller build directory
├── dist/                                # PyInstaller output directory
├── Recordings+transcriptions/           # Output directory (auto-created)
│   └── transcription.log               # Comprehensive logging file
└── README.md                            # This file
```

## 🎵 Supported Radio Stations

### Dutch Stations
- **Public Broadcasting**: Radio 1, Radio 2, 3FM, Radio 6
- **Regional**: Radio Rijnmond
- **Commercial**: BNR Nieuwsradio, Radio 538, Sky Radio, Qmusic, Veronica, Radio 10
- **Alternative**: KINK

### Belgian (Flemish) Stations
- **Public Broadcasting**: Radio 1, Klara, MNM, Studio Brussel, VRT NWS
- **Regional**: Radio 2 (all provinces)
- **Commercial**: Qmusic, JOE FM, Radio Contact, TOPradio
- **Cultural**: Klara Continuo, Klara Jazz, Sporza Radio
- **Local**: Radio Scorpio, Radio Centraal, Urgent.fm, Radio Campus

## ⚙️ Configuration

### OpenAI API Key
- **Set**: `Settings` → `Set OpenAI API Key`
- **Remove**: `Settings` → `Remove OpenAI API Key`
- **Storage**: Saved locally in `openai_config.txt`

### Output Settings
- **Location**: `Recordings+transcriptions/` folder in app directory
- **Format**: `YYYYMMDD_HHMMSS_StationName/radio_recording_YYYYMMDD.mp3`
- **Transcriptions**: Saved alongside recordings

### Logging System
- **Log file**: `Recordings+transcriptions/transcription.log`
- **Content**: Recording start/end times, transcript details, fallback triggers, results summary
- **Format**: Timestamped entries with clear status information
- **Availability**: Works in both script and executable versions

## 🔧 Technical Details

### Dependencies
- **Core**: tkinter, threading, time, os, sys
- **Audio**: pydub, ffmpeg
- **AI**: openai, keybert, sentence-transformers
- **Images**: PIL (Pillow)
- **Logging**: logging, datetime

### Enhanced Fallback Mechanism
- **Automatic triggering**: When KeyBERT finds fewer than 15 keypoints
- **Aggressive fallback**: Forces fallback when KeyBERT finds fewer than 20 keypoints
- **Non-overlapping phrases**: Uses stepping algorithms to prevent duplicate content
- **Smart deduplication**: Removes overlapping phrases while keeping the most complete versions
- **Multiple fallback levels**: Ensures meaningful content is always extracted

### Improved Phrase Generation
- **5-word phrases**: Generated with 3-word stepping to avoid overlaps
- **4-word phrases**: Generated with 2-word stepping to reduce overlaps
- **3-word phrases**: Generated with 2-word stepping to reduce overlaps
- **2-word phrases**: Generated with 2-word stepping to reduce overlaps
- **Overlap detection**: Automatically removes phrases that are contained within longer ones

### Keyword Extraction Strategy
- **Prioritizes longer phrases**: 2+ word phrases get highest priority
- **Balanced coverage**: Ensures sufficient phrases are found while maintaining quality
- **Frequency-based filtering**: Only includes phrases that appear multiple times (2+ occurrences)
- **Smart filtering**: Balances meaningful content with phrase length and coverage
- **Smart merging**: Combines phrases with reasonable overlap (40%+ of shorter phrase)
- **Eliminates redundancy**: Only removes phrases with substantial overlap (80%+ of shorter phrase)
- **Extended phrase range**: Supports phrases from 2-8 words for comprehensive coverage

### Build Optimization
- **Excluded**: Heavy ML packages (torch, tensorflow, sklearn)
- **Excluded**: Web frameworks (flask, django, fastapi)
- **Excluded**: Database packages (sqlalchemy, sqlite3)
- **Included**: Essential dependencies only
- **Result**: 29MB executable vs 200MB+ without optimization

## 🐛 Troubleshooting

### Common Issues
1. **FFmpeg not found**: Ensure `bin/` folder is copied to `dist/`
2. **API key error**: Set your OpenAI API key via Settings menu
3. **Image loading issues**: Check `Bluvia images/` folder exists
4. **Large executable**: Use the optimized .spec file
5. **No debug output in executable**: Check `transcription.log` file in `Recordings+transcriptions/` folder

### Debugging with Logs
- **Check log file**: `Recordings+transcriptions/transcription.log`
- **Look for**: Recording start/end times, fallback triggers, error messages
- **Common log entries**:
  - `RECORDING START: filename.mp3`
  - `TRANSCRIPT: X words, X chars`
  - `FALLBACK: KeyBERT=false, Found=X`
  - `RESULTS: X keypoints (X words, X phrases)`

### Build Issues
- **Missing modules**: Check `hiddenimports` in .spec file
- **Large size**: Review `excludes` list in .spec file
- **Icon not working**: Use double backslashes in icon path

## 📝 License

This project is open source. See [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For support and questions:
- **Website**: [Bluvia.nl](https://bluvia.nl)
- **Issues**: Use GitHub Issues
- **Documentation**: Check this README and code comments

## 🏆 Credits

- **Developed by**: Bluvia
- **Powered by**: OpenAI Whisper API, KeyBERT
- **Audio Processing**: FFmpeg
- **UI Framework**: Tkinter

---

**Radio Transcription Tool v3.5** - Professional audio transcription and analysis for Dutch and Belgian radio content with comprehensive logging and enhanced reliability. 