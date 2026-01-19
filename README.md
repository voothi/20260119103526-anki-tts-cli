# Anki TTS CLI for GoldenDict & AHK

This project adapts the Anki TTS Player addon logic for use with GoldenDict and AutoHotkey (AHK). It allows you to:
1. Play audio from local "Audio Dictionaries" (preserving Anki addon configuration).
2. Generate/Play TTS using Piper (via local script) or Google TTS (gTTS).
3. Share the audio cache with the Anki addon.

## Requirements

- Python 3.x
- **Libraries**: You may need to install the following libraries in your Python environment:
  ```bash
  pip install requests gTTS pyperclip
  ```
  *(Note: `gTTS` is technically vendored in the Anki addon, but relies on `requests`. Using the system installed `gTTS` is often easier for CLI usage).*

- **External Tools**: `ffplay` (from FFmpeg) must be in your system PATH to play audio.

## Usage

### Command Line
```bash
python cli.py "Text to speak" "lang_code" [options]
```

**Options:**
- `--play` : Play the audio immediately (Default).
- `--no-play` : Do not play audio.
- `--output <path>` : Save the audio file to a specific path.
- `--clipboard` : Use text from the clipboard instead of the command argument.

**Example:**
```bash
python cli.py "Hello World" en
python cli.py --clipboard en
```

## Integration

### GoldenDict
Add a new Program in GoldenDict:
- **Type**: Audio
- **Name**: Anki TTS En
- **Command Line**:
  ```cmd
  C:\Python\Python312\python.exe "U:\voothi\20260119103526-goldendict-tts\20260119-anki-tts-cli\cli.py" "%GDWORD%" "en"
  ```
  *(Adjust paths to `python.exe` and `cli.py` as needed on your system)*.

### AutoHotkey (AHK)
Update your `tts.ahk` script to point to this new CLI tool.

```autohotkey
RunPythonScript(lang) {
    ; Pass the language code. The Python script reads from clipboard via --clipboard
    RunWait("C:/Python/Python312/python.exe U:/voothi/20260119103526-goldendict-tts/20260119-anki-tts-cli/cli.py ""placeholder"" " lang " --clipboard", "", "Hide")
}
```
*Note: We pass "placeholder" as the text argument because `cli.py` expects a positional argument for text, even if using `--clipboard`.*

## Configuration
This tool reads the configuration from the **Anki Addon folder**:
`../20250421115831-anki-gtts-player/config.json`

It shares:
- Audio Dictionary paths
- Cache Directory
- Enabled/Disabled engines (Piper/gTTS)
