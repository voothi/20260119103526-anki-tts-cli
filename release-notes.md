# Release Notes

## [20260119114726] - 2026-01-19
### Changed
- Improved [`README.md`](README.md) with a Table of Contents and "Return to top" navigation links.

## [20260119113553] - 2026-01-19
### Added
- Added support for local [`config.json`](config.json) to allow overriding Anki addon settings.
- Decoupled hardcoded paths in [`goldendict-tts.py`](goldendict-tts.py) using the new configuration system.
- Added override mechanism to customize TTS engine or cache paths specifically for GoldenDict/AHK.

## [20260119111239] - 2026-01-19
### Fixed
- Fixed command-line argument for Piper TTS: changed `--output_file` to `--output-file` to match `piper_tts.py` expectations.

## [20260119110742] - 2026-01-19
### Fixed
- Fixed audio dictionary rotation: the script now cycles through available recordings across different calls.
- Fixed TTS engine cycling: Piper and gTTS now alternate correctly when `tts_cycle_enabled` is true.
### Added
- State persistence via JSON files in the `user_cache` directory.

## [20260119110110] - 2026-01-19
### Added
- Integrated [`goldendict-tts.py`](goldendict-tts.py) as a unified CLI for GoldenDict and AHK.
- Added support for Piper and gTTS with shared caching logic.
- Implemented Audio Dictionary lookup based on the Anki addon configuration.

## [20260119105824] - 2026-01-19
### Added
- Standalone `cli.py` (later renamed to `goldendict-tts.py`) providing a command-line interface for the Anki TTS logic.
- Support for clipboard-based TTS via `--clipboard` flag.
- Automatic path resolution for shared cache and configuration.
