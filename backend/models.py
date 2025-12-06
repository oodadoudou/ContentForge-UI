from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

class TaskRequest(BaseModel):
    script_id: str = Field(..., description="ID of the script to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the script")
    work_dir: Optional[str] = Field(None, description="Working directory for execution override")

class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, running, success, failed, canceled
    exit_code: Optional[int] = None
    error: Optional[str] = None

class Settings(BaseModel):
    default_work_dir: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_base_url: Optional[str] = None
    ai_model_name: Optional[str] = None
    recent_tasks: List[Dict[str, Any]] = []
    favorite_paths: List[str] = []
    language: str = "zh-CN"
    auto_scroll_console: bool = True
