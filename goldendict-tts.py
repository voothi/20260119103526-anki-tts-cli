import os
import sys
import argparse
import json
import glob
import re
import subprocess
import threading
import shutil
import hashlib
from pathlib import Path

# --- Paths & Setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(SCRIPT_DIR)
# Adjust this folder name if the Anki addon folder name changes
ANKI_ADDON_DIR_NAME = "20250421115831-anki-gtts-player"
ANKI_ADDON_PATH = os.path.join(WORKSPACE_ROOT, ANKI_ADDON_DIR_NAME)
VENDOR_PATH = os.path.join(ANKI_ADDON_PATH, "vendor")
CONFIG_PATH = os.path.join(ANKI_ADDON_PATH, "config.json")

# Add vendor to sys.path to load gTTS from the Anki addon
if os.path.exists(VENDOR_PATH):
    sys.path.append(VENDOR_PATH)

try:
    from gtts import gTTS, gTTSError
except ImportError:
    gTTS = None

try:
    import pyperclip
except ImportError:
    pyperclip = None

# --- Core Logic Ported from Anki Addon ---

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: Config file not found at {CONFIG_PATH}", file=sys.stderr)
        return {}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        return {}

def sanitize_filename(text):
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    return text.strip().lower()

def get_cache_dir(conf):
    persistent_enabled = conf.get("persistent_cache_enabled", False)
    custom_path = conf.get("persistent_cache_path", "").strip()
    
    if persistent_enabled:
        if custom_path:
            cache_dir = custom_path
        else:
            cache_dir = os.path.join(ANKI_ADDON_PATH, "user_cache")
        
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir, exist_ok=True)
            except OSError:
                return None
        return cache_dir
    return None

def load_state(cache_dir, state_name):
    if not cache_dir:
        return {}
    state_file = os.path.join(cache_dir, f"{state_name}_state.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_state(cache_dir, state_name, state):
    if not cache_dir:
        return
    state_file = os.path.join(cache_dir, f"{state_name}_state.json")
    try:
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except:
        pass

def find_in_audio_dictionary(text, lang, conf):
    if not conf.get("audio_dictionary_enabled", False):
        return None

    root_path = conf.get("audio_dictionary_path", "").strip()
    if not root_path or not os.path.exists(root_path):
        return None

    exclusions = conf.get("audio_dictionary_exclusions", [])
    lang_map = conf.get("audio_dictionary_lang_map", {})

    default_short = lang.split('_')[0] if '_' in lang else lang
    target_folder = default_short 
    
    if lang in lang_map:
        target_folder = lang_map[lang]
    elif default_short in lang_map:
        target_folder = lang_map[default_short]

    clean_name = sanitize_filename(text)
    filename = f"{clean_name}.mp3"
    search_pattern = os.path.join(root_path, target_folder, "*", filename)
    
    candidates = glob.glob(search_pattern)
    
    valid_candidates = []
    if candidates:
        candidates.sort()
        for path in candidates:
            if exclusions and any(ex in path for ex in exclusions):
                continue
            if os.path.exists(path) and os.path.getsize(path) > 0:
                valid_candidates.append(path)

    if not valid_candidates:
        return None

    # --- Persistence & Rotation Logic ---
    cache_dir = get_cache_dir(conf)
    cycle_enabled = conf.get("audio_dictionary_cycle_enabled", False)
    cycle_limit = max(1, conf.get("audio_dictionary_cycle_limit", 2))
    
    effective_count = min(len(valid_candidates), cycle_limit)
    
    if cycle_enabled and effective_count > 1:
        state = load_state(cache_dir, "audio_cycle")
        key = f"{text}|{lang}"
        current_idx = state.get(key, 0)
        
        if current_idx >= effective_count:
            current_idx = 0
            
        selected_file = valid_candidates[current_idx]
        
        # Update for next time
        state[key] = (current_idx + 1) % effective_count
        save_state(cache_dir, "audio_cycle", state)
        
        print(f"Audio Dictionary: Playing file {current_idx + 1}/{effective_count}: {selected_file}")
        return selected_file
    else:
        return valid_candidates[0]

def run_piper_tts(text, lang, output_path, conf):
    python_exe = conf.get("piper_python_path")
    script_path = conf.get("piper_script_path")
    
    temp_output_path = f"{output_path}.temp_piper.wav"

    if not all([python_exe, script_path]):
        print("Piper TTS: Python executable or script path not configured.", file=sys.stderr)
        return False
        
    if not Path(python_exe).exists() or not Path(script_path).exists():
        print(f"Piper TTS: Path does not exist. Python: '{python_exe}', Script: '{script_path}'", file=sys.stderr)
        return False

    if "_" in lang:
        lang_code = lang.split("_")[0]
    else:
        lang_code = lang

    command = [
        python_exe,
        script_path,
        "--lang", lang_code,
        "--text", text,
        "--output_file", temp_output_path
    ]

    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            creationflags=creation_flags
        )
        if process.returncode == 0 and os.path.exists(temp_output_path) and os.path.getsize(temp_output_path) > 0:
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except OSError:
                    pass
            os.rename(temp_output_path, output_path)
            return True
        else:
            print(f"Piper TTS Error: {process.stderr}", file=sys.stderr)
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)
            return False
    except Exception as e:
        print(f"Failed to run Piper TTS process: {e}", file=sys.stderr)
        if os.path.exists(temp_output_path):
            try:
                os.remove(temp_output_path)
            except:
                pass
        return False

def run_gtts_with_timeout(text, lang, output_path, conf):
    if gTTS is None:
        print("gTTS module not available.", file=sys.stderr)
        return False

    timeout = conf.get("gtts_timeout_sec", 5)
    result_container = {}
    
    temp_output_path = f"{output_path}.temp_gtts.mp3"

    def gtts_save_job():
        try:
            # lang_check=False speed up
            tts = gTTS(text=text, lang=lang, lang_check=False, slow=False)
            tts.save(temp_output_path)
            result_container['success'] = True
        except Exception as e:
            result_container['error'] = e

    try:
        thread = threading.Thread(target=gtts_save_job)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            print(f"gTTS timed out after {timeout} seconds.", file=sys.stderr)
            return False
        
        if 'error' in result_container:
            if os.path.exists(temp_output_path):
                try:
                    os.remove(temp_output_path)
                except:
                    pass
            raise result_container['error']
        
        if os.path.exists(temp_output_path) and os.path.getsize(temp_output_path) > 0:
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except OSError:
                    pass
            os.rename(temp_output_path, output_path)
            return True
        
        return False

    except Exception as e:
        print(f"gTTS error: {e}", file=sys.stderr)
        return False

def play_audio(file_path):
    """Plays audio file using ffplay or system default."""
    # We use ffplay with nodisp and autoexit
    # Attempt to find ffplay
    ffplay = shutil.which("ffplay")
    if not ffplay:
        print("Error: ffplay not found in PATH. Cannot play audio.", file=sys.stderr)
        return

    try:
        subprocess.run([ffplay, "-nodisp", "-autoexit", "-loglevel", "quiet", file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error playing audio: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Anki TTS CLI for GoldenDict")
    parser.add_argument("text", nargs="?", help="Text to speak")
    parser.add_argument("lang", help="Language code (e.g. en, de, ru)")
    parser.add_argument("--play", action="store_true", default=True, help="Play the audio (default)")
    parser.add_argument("--no-play", action="store_false", dest="play", help="Do not play audio")
    parser.add_argument("--output", help="Output file path (optional)")
    parser.add_argument("--clipboard", action="store_true", help="Use text from clipboard")
    
    args = parser.parse_args()

    text = args.text
    if args.clipboard:
        if pyperclip is None:
            print("Error: pyperclip module not found. Cannot read clipboard.", file=sys.stderr)
            sys.exit(1)
        text = pyperclip.paste()
        print(f"Read from clipboard: {text}")

    if not text:
        print("Error: No text provided.", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    lang = args.lang
    conf = load_config()

    # --- 1. Audio Dictionary Lookup ---
    found_file = find_in_audio_dictionary(text, lang, conf)
    if found_file:
        print(f"Found in Audio Dictionary: {found_file}")
        if args.play:
            play_audio(found_file)
        if args.output:
            shutil.copy2(found_file, args.output)
        return

    # --- 2. Determine Cache/Temp Path ---
    persistent_enabled = conf.get("persistent_cache_enabled", False)
    custom_path = conf.get("persistent_cache_path", "").strip()
    
    # Construct a filename hash
    hash_str = hashlib.md5(f"{text}_{lang}".encode('utf-8')).hexdigest()
    
    cache_dir = None
    if persistent_enabled:
        if custom_path:
            cache_dir = custom_path
        else:
            cache_dir = os.path.join(ANKI_ADDON_PATH, "user_cache")
        
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir, exist_ok=True)
            except OSError:
                cache_dir = None # Fallback to temp

    if cache_dir:
        base_filename = os.path.join(cache_dir, f"tts_{hash_str}")
    else:
        # Just use temp dir
        import tempfile
        base_filename = os.path.join(tempfile.gettempdir(), f"tts_{hash_str}")

    gtts_file = f"{base_filename}.mp3"
    piper_file = f"{base_filename}.wav"

    # --- 3. TTS Logic ---
    gtts_cache_enabled = conf.get("gtts_cache_enabled", True)
    piper_cache_enabled = conf.get("piper_cache_enabled", False)
    enable_gtts = conf.get("gtts_enabled", True)
    enable_piper = conf.get("piper_enabled", True)
    default_engine = conf.get("tts_engine", "gTTS") # gTTS or Piper
    cycle_tts = conf.get("tts_cycle_enabled", False)

    final_file = None

    # Determine engine order with cycling support
    current_engine = default_engine
    if cycle_tts and enable_gtts and enable_piper:
        cache_dir = get_cache_dir(conf)
        state = load_state(cache_dir, "tts_cycle")
        key = f"{text}|{lang}"
        
        if key in state:
            current_engine = state[key]
        else:
            current_engine = default_engine
        
        # Toggle for next time
        state[key] = "Piper" if current_engine == "gTTS" else "gTTS"
        save_state(cache_dir, "tts_cycle", state)
        print(f"TTS Cycle: Selected {current_engine}")

    engines_to_try = []
    if current_engine == "Piper":
        if enable_piper: engines_to_try.append("Piper")
        if enable_gtts: engines_to_try.append("gTTS")
    else:
        if enable_gtts: engines_to_try.append("gTTS")
        if enable_piper: engines_to_try.append("Piper")

    for engine in engines_to_try:
        if engine == "Piper":
            # Check cache
            if piper_cache_enabled and os.path.exists(piper_file) and os.path.getsize(piper_file) > 0:
                print("Found cached Piper file.")
                final_file = piper_file
                break
            # Generate
            print("Generating Piper TTS...")
            if run_piper_tts(text, lang, piper_file, conf):
                final_file = piper_file
                break
        
        elif engine == "gTTS":
            # Check cache
            if gtts_cache_enabled and os.path.exists(gtts_file) and os.path.getsize(gtts_file) > 0:
                print("Found cached gTTS file.")
                final_file = gtts_file
                break
            # Generate
            print("Generating gTTS...")
            if run_gtts_with_timeout(text, lang, gtts_file, conf):
                final_file = gtts_file
                break

    if final_file:
        if args.play:
            play_audio(final_file)
        if args.output:
            if args.output != final_file:
                shutil.copy2(final_file, args.output)
    else:
        print("Failed to find or generate audio.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
