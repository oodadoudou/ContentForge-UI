import os
import json
import sys

def load_settings():
    """
    Load settings from shared_assets/settings.json.
    Returns the full settings dictionary.
    Includes error handling and logical fallbacks.
    """
    try:
        # Determine paths relative to this file (backend/utils.py)
        # We expect settings.json to be in backend/shared_assets/settings.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        settings_path = os.path.join(current_dir, 'shared_assets', 'settings.json')

        
        if not os.path.exists(settings_path):
            return {}

        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load settings: {e}")
        return {}

def get_default_work_dir():
    """
    Returns the default work directory from settings, or Downloads as fallback.
    """
    settings = load_settings()
    default_dir = settings.get("default_work_dir")
    
    if default_dir and os.path.isdir(default_dir):
        return default_dir
    
    return os.path.join(os.path.expanduser("~"), "Downloads")
