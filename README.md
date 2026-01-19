# GoldenDict Anki TTS Integration

This project adapts the Anki TTS Player addon logic for use with GoldenDict and AutoHotkey (AHK). It allows you to:
1. Play audio from local "Audio Dictionaries" (preserving Anki addon configuration).
2. Generate/Play TTS using Piper or Google TTS (gTTS).
3. Share the audio cache and rotation state with the Anki addon.
4. Override settings specifically for GoldenDict without affecting Anki.

## Table of Contents
- [GoldenDict Anki TTS Integration](#goldendict-anki-tts-integration)
  - [Table of Contents](#table-of-contents)
  - [Requirements](#requirements)
  - [Usage](#usage)
    - [Testing the CLI](#testing-the-cli)
    - [GoldenDict Integration](#goldendict-integration)
  - [Configuration](#configuration)
    - [`config.json`](#configjson)
  - [Features](#features)

## Requirements

- Python 3.x
- **Libraries**: `requests`, `gTTS`, `pyperclip` (optional, for clipboard support).
- **External Tools**: `ffplay` (from FFmpeg) must be in your system PATH to play audio.

[Return to Top](#goldendict-anki-tts-integration)

## Usage

### Testing the CLI
```powershell
C:\Python\Python312\python.exe .\goldendict-tts.py "text to play" "en"
```

### GoldenDict Integration
1. Go to **Edit > Dictionaries > Program**.
2. Add a new entry:
   - **Name**: Anki-TTS
   - **Command Line**: `C:\Python\Python312\python.exe "U:\voothi\20260119103526-goldendict-tts\goldendict-tts.py" "%GDWORD%" "en"`
   - **Type**: Audio

[Return to Top](#goldendict-anki-tts-integration)

## Configuration

The script uses a local `config.json` to locate the Anki addon and set overrides.

### `config.json`
```json
{
    "anki_addon_path": "./20250421115831-anki-gtts-player",
    "overrides": {
        "tts_engine": "Piper",
        "audio_dictionary_cycle_limit": 5
    }
}
```

- `anki_addon_path`: Relative or absolute path to the [Anki Addon folder](20250421115831-anki-gtts-player/).
- `overrides`: Any setting here (e.g., `tts_engine`, `gtts_timeout_sec`, `audio_dictionary_enabled`) will override the value found in the Anki addon's donor config.

[Return to Top](#goldendict-anki-tts-integration)

## Features
- **Persistent Rotation**: Uses JSON state files in `user_cache` to remember which recording or engine to play next across different process calls.
- **Shared Cache**: Automatically uses the same `user_cache` as the Anki addon to save bandwidth and disk space.
- **Failover**: Automatically falls back to the next available engine if the preferred one fails.

[Return to Top](#goldendict-anki-tts-integration)
