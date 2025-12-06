import os
import sys
import json
import shutil
import re
from pypinyin import pinyin, Style

# --- Global Config ---
ORGANIZER_TARGET_EXTENSIONS = ".pdf .epub .txt .jpg .jpeg .png .gif .bmp .tiff .webp .zip .rar .7z .tar .gz"

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', print_end="\r"):
    if total == 0:
        percent_str, filled_length = "0.0%", 0
    else:
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        percent_str, filled_length = f"{percent}%", int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent_str} {suffix}')
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')
        sys.stdout.flush()

def load_settings_from_json():
    """Load settings from shared_assets/settings.json."""
    try:
        # Script is now in backend/file_organization/
        # Project root is ../..
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir)) # Up from backend/file_organization to root
        
        # Determine settings path.
        # If shared_assets is in backend/shared_assets (which we just moved):
        settings_path = os.path.join(project_root, 'backend', 'shared_assets', 'settings.json')
        
        if not os.path.exists(settings_path):
             # Fallback if structure is different
             settings_path = os.path.join(project_root, 'shared_assets', 'settings.json')

        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        default_dir = settings.get("default_work_dir")
        return default_dir if default_dir else os.path.join(os.path.expanduser("~"), "Downloads")

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Failed to load settings.json ({e}). Using default.")
        return os.path.join(os.path.expanduser("~"), "Downloads")

# ==============================================================================
# Module 1: File Organizer (Grouping)
# ==============================================================================
def clean_name_for_grouping(filename: str) -> str:
    cleaned = filename
    if cleaned.startswith('['):
        try:
            idx = cleaned.index(']') + 1
            cleaned = cleaned[idx:].strip()
        except ValueError:
            pass
    cleaned = os.path.splitext(cleaned)[0]
    cut_pos = len(cleaned)
    for ch in '0123456789[]()@#%&':
        pos = cleaned.find(ch)
        if pos != -1 and pos < cut_pos:
            cut_pos = pos
    cleaned = cleaned[:cut_pos].strip()
    return re.sub(r'\s+', ' ', cleaned)

def organize_files_into_subdirs(root_directory: str):
    """Group loose files into subdirectories based on similarity."""
    print(f"\n--- Step 1: Organizing loose files into groups ---")
    target_extensions = set(ext.lower() for ext in ORGANIZER_TARGET_EXTENSIONS.split())
    try:
        all_files = [
            f for f in os.listdir(root_directory)
            if os.path.isfile(os.path.join(root_directory, f)) and os.path.splitext(f)[1].lower() in target_extensions
        ]
        if not all_files:
            print("    No files to organize in root directory.")
            return
        
        print(f"    Found {len(all_files)} files. Grouping...")
        groups = {}
        for filename in all_files:
            group_key = clean_name_for_grouping(filename)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(filename)

        moved_count = 0
        print_progress_bar(0, len(groups), prefix='    Progress:', suffix='Complete', length=40)
        i = 0
        for group_key, file_list in groups.items():
            i += 1
            folder_name_raw = group_key if len(group_key) > 2 else os.path.splitext(file_list[0])[0]
            folder_name_sanitized = re.sub(r'[\\/*?:"<>|]', '_', folder_name_raw).strip()
            if not folder_name_sanitized: continue

            folder_path = os.path.join(root_directory, folder_name_sanitized)
            os.makedirs(folder_path, exist_ok=True)

            for filename in file_list:
                source_path = os.path.join(root_directory, filename)
                destination_path = os.path.join(folder_path, filename)
                if os.path.exists(source_path):
                    shutil.move(source_path, destination_path)
                    moved_count += 1
            print_progress_bar(i, len(groups), prefix='    Progress:', suffix='Complete', length=40)
        
        print(f"    Organization complete. Moved {moved_count} files.")
    except Exception as e:
        print(f"    Error during organization: {e}")

# ==============================================================================
# Module 2: Add Pinyin Prefix (Sorting)
# ==============================================================================
def add_pinyin_prefix_to_dirs(root_directory: str):
    """Add pinyin/alphabetical prefix to subdirectories for sorting."""
    print(f"\n--- Step 2: Adding Pinyin/Alpha prefixes for sorting ---")
    
    try:
        dir_names = [
            d for d in os.listdir(root_directory)
            if os.path.isdir(os.path.join(root_directory, d)) and not d.startswith('.')
        ]
    except Exception as e:
        print(f"    Error reading directory: {e}")
        return

    if not dir_names:
        print("    No folders found.")
        return
    
    dir_names.sort()
    renamed_count = 0
    error_count = 0
    
    print_progress_bar(0, len(dir_names), prefix='    Prefixing:', suffix='Complete', length=40)
    for i, original_name in enumerate(dir_names):
        # Skip if already prefixed (Single letter + dash)
        if re.match(r'^[A-Z]-', original_name):
            print_progress_bar(i + 1, len(dir_names), prefix='    Prefixing:', suffix='Complete', length=40)
            continue

        first_char_match = re.search(r'([\u4e00-\u9fff]|[A-Za-z])', original_name)
        if not first_char_match:
            print(f"\n    Warning: Could not determine prefix for '{original_name}'.")
            error_count += 1
            print_progress_bar(i + 1, len(dir_names), prefix='    Prefixing:', suffix='Complete', length=40)
            continue
        
        prefix = ''
        try:
            first_char = first_char_match.group(1)
            if '\u4e00' <= first_char <= '\u9fff':
                prefix = pinyin(first_char, style=Style.FIRST_LETTER)[0][0].upper()
            elif 'a' <= first_char.lower() <= 'z':
                prefix = first_char.upper()
        except Exception as e:
            print(f"\n    Prefix error for '{original_name}': {e}")
            prefix = 'X'
        
        if prefix:
            new_name_with_prefix = f"{prefix}-{original_name}"
            original_path = os.path.join(root_directory, original_name)
            new_path = os.path.join(root_directory, new_name_with_prefix)
            
            if os.path.isdir(original_path):
                if not os.path.exists(new_path):
                    try:
                        os.rename(original_path, new_path)
                        renamed_count += 1
                    except Exception as e:
                        print(f"\n    Rename error '{original_name}': {e}")
                        error_count += 1
                else:
                    # Target exists, skip
                    pass
        
        print_progress_bar(i + 1, len(dir_names), prefix='    Prefixing:', suffix='Complete', length=40)

    print(f"\n    Prefixing complete. Renamed: {renamed_count}, Errors/Skipped: {error_count}")

# ==============================================================================
# Main
# ==============================================================================
if __name__ == "__main__":
    import argparse
    
    print("Organizer Script (No Translation)")
    print("-" * 50)
    
    parser = argparse.ArgumentParser(description="Organize Files")
    parser.add_argument("--target_dir", help="Target directory to organize")
    # Backup for piped input if needed, but we prefer args
    args = parser.parse_args()

    default_path = load_settings_from_json()
    target_directory = ""

    if args.target_dir:
        if os.path.isdir(args.target_dir):
            target_directory = args.target_dir
            print(f"Using target directory from args: {target_directory}")
        else:
            print(f"Error: Provided target_dir '{args.target_dir}' is not valid.")
            sys.exit(1)
    else:
        try:
            # Support both interactive input and piped input (via echo) - fallback behavior
            if not sys.stdin.isatty():
                 # Piped input could be just the path
                 # But since we use argparse now, this might be less relevant unless we keep it for backward compat
                 # Let's try to read it if no args provided
                 possible_input = sys.stdin.read().strip()
                 if possible_input and os.path.isdir(possible_input):
                      target_directory = possible_input
                      print(f"Received path via pipe: {target_directory}")
                 else:
                      pass # Will fall to interactive
            
            if not target_directory:
                target_directory_input = input(f"Enter directory path (Default: {default_path}): ").strip()
                target_directory = target_directory_input if target_directory_input else default_path
            
            while not os.path.isdir(target_directory):
                print(f"Error: '{target_directory}' is not a valid directory.")
                if not sys.stdin.isatty():
                     sys.exit(1) # Fail if piped
                target_directory_input = input("Please re-enter path: ").strip()
                if not target_directory_input:
                    sys.exit()
                target_directory = target_directory_input

        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit()

    try:
        # Execute
        organize_files_into_subdirs(target_directory)
        add_pinyin_prefix_to_dirs(target_directory)
        print("\nAll operations complete.")
    except Exception as e:
        print(f"Error during execution: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit()
