import sys
import os
import asyncio
import uvicorn

# CRITICAL: Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# CRITICAL: Set the event loop policy at the MODULE level.
# This ensures that when uvicorn spawns subprocesses (via multiprocessing for reload),
# and those processes import this module (or run it), the policy is applied 
# BEFORE the event loop is created.
if sys.platform == 'win32':
    # This is required for subprocess support on Windows (asyncio.create_subprocess_exec)
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    # Import settings from run.py if possible, or hardcode defaults matching run.py
    HOST = "127.0.0.1"
    PORT = 8000
    
    print(f"Starting Dev Server via custom runner on {HOST}:{PORT}...")
    
    # Run uvicorn with reload enabled
    # loop="asyncio" makes it use asyncio.new_event_loop(), which respects our policy set above.
    uvicorn.run("backend.app:app", host=HOST, port=PORT, reload=True, loop="asyncio")
