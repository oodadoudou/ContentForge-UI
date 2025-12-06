from fastapi import APIRouter, HTTPException
import json
import os
import logging
from backend.models import Settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Determine config path
# Router is in backend/routers/
# Parent is backend/
# Parent^2 is project root.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "backend", "shared_assets", "settings.json")

def load_config() -> Settings:
    if not os.path.exists(CONFIG_PATH):
        return Settings()
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return Settings(**data)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return Settings()

def save_config(settings: Settings):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write(settings.model_dump_json(indent=2))
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        raise HTTPException(status_code=500, detail="Failed to save settings")

@router.get("", response_model=Settings)
async def get_settings():
    return load_config()

@router.post("", response_model=Settings)
async def update_settings(settings: Settings):
    save_config(settings)
    return settings
