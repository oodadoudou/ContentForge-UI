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
        # Determine project root. 
        # Assumes this utils.py is in backend/utils.py or backend/utils.py 
        # If this file is in backend/utils.py, project root is ../../
        # If this file is directly in backend/, project root is ../
        
        # We will assume this file is placed at backend/utils.py for organization,
        # or we check relative to where it ends up.
        # Let's say we put it in backend/utils.py
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Check if we are in backend/utils or just backend
        if os.path.basename(current_dir) == 'backend':
             project_root = os.path.dirname(current_dir)
        else:
             project_root = os.path.dirname(os.path.dirname(current_dir))

        settings_path = os.path.join(project_root, 'shared_assets', 'settings.json')
        
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
