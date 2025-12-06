from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict
import uuid
import os
import json
import logging
from backend.models import TaskRequest, TaskStatus, Settings
from backend.services.scripts_catalog import SCRIPTS, get_script_command, ScriptDef
from backend.services.runner import ScriptRunner
from backend.services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()
runner = ScriptRunner()

# Determine project root (assuming backend/routers/tasks.py -> .../ContentForge-UI)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

@router.get("/scripts", response_model=List[ScriptDef])
async def list_scripts():
    return list(SCRIPTS.values())

@router.post("/run", response_model=TaskStatus)
async def run_script(request: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    
    # 1. Validate Script
    if request.script_id not in SCRIPTS:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # 2. Prepare Command
    try:
        command = get_script_command(request.script_id, request.params, PROJECT_ROOT)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # 3. Determine Working Directory
    # Priority: Request override > Global Settings (todo) > Project Root
    work_dir = request.work_dir or PROJECT_ROOT
    
    # 4. Define Log Callback
    async def log_callback(line: str):
        # Broadcast to WebSocket
        await manager.broadcast(line)
        # TODO: Persist to file if needed here or in runner
    
    # 5. Start Execution in Background
    # Note: For simple architecture, we use BackgroundTasks or fire-and-forget task
    # A true job queue (Celery/RQ) is overkill here.
    # We want to wait for it ? No, we want to return Task ID immediately.
    # But runner.run is async. We should schedule it.
    
    background_tasks.add_task(runner.run, command, work_dir, log_callback)

    return TaskStatus(task_id=task_id, status="running")

@router.post("/stop")
async def stop_task():
    """Stops the currently running task (single runner model for now)"""
    await runner.terminate()
    return {"status": "termination_requested"}

@router.post("/input")
async def send_input(data: Dict[str, str]):
    """Sends input to the running task's stdin"""
    input_text = data.get("input", "")
    await runner.write_stdin(input_text)
    return {"status": "input_sent"}

@router.get("/diritto/extracted-urls")
async def get_extracted_urls():
    """Retrieve extracted Diritto URLs from the saved JSON file"""
    file_path = os.path.join(PROJECT_ROOT, "diritto_extracted_urls.json")
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Failed to read extracted URLs: {e}")
            raise HTTPException(status_code=500, detail="Failed to read extracted URLs")
    
    return {"urls": []}
