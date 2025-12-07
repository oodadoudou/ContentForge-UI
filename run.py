import os
import sys
import threading
import time
import socket
import requests
import logging

try:
    import webview
    HAS_WEBVIEW = True
except ImportError:
    HAS_WEBVIEW = False
    import webbrowser

# Configuration
HOST = "127.0.0.1"
PORT = 8000

# Global process verification
backend_process = None

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) == 0

def run_script_mode(args):
    """
    Execute a python script in the frozen environment.
    Usage: ContentForge.exe run-script <script_path> [args...]
    """
    if len(args) < 1:
        print("Error: No script specified for run-script mode.")
        sys.exit(1)
    
    script_path = args[0]
    script_args = args[1:]
    
    print(f"[FrozenExec] Running script: {script_path}")
    print(f"[FrozenExec] Args: {script_args}")
    
    # Verify script existence
    if not os.path.exists(script_path):
        print(f"Error: Script file not found: {script_path}")
        sys.exit(1)
        
    # Prepare environment
    # We replace sys.argv so the script thinks it was called directly
    sys.argv = [script_path] + script_args
    
    # Add script directory to sys.path so imports work
    script_dir = os.path.dirname(os.path.abspath(script_path))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        
    try:
        # Execute the script
        import runpy
        runpy.run_path(script_path, run_name="__main__")
    except Exception as e:
        print(f"[FrozenExec] Error executing script: {e}")
        sys.exit(1)

def start_server_frozen():
    """Run uvicorn server directly in this process (for PyInstaller)"""
    try:
        from backend.app import app
        import uvicorn
        
        # Configure logging to file in frozen mode to capture errors
        logging.basicConfig(filename='backend_startup.log', level=logging.INFO)
        print("Starting Uvicorn in frozen mode...")
        uvicorn.run(app, host=HOST, port=PORT, log_level="info")
    except Exception as e:
        error_msg = f"Failed to start backend: {e}"
        print(error_msg)
        with open("startup_error.txt", "w") as f:
            f.write(error_msg)
        sys.exit(1)

def start_server_dev():
    """Run uvicorn as subprocess (for Development with reload)"""
    global backend_process
    print("Starting Uvicorn in dev mode (subprocess)...")
    import subprocess
    
    cmd = [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", HOST, "--port", str(PORT), "--reload"]
    
    # Hide console window on Windows
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    backend_process = subprocess.Popen(cmd, cwd=os.getcwd(), startupinfo=startupinfo)

def wait_for_backend_and_launch():
    """Wait for server to be ready then launch browser/webview"""
    url = f"http://{HOST}:{PORT}/health"
    start_url = f"http://{HOST}:{PORT}"
    
    print(f"Waiting for backend at {start_url}...")
    
    start_time = time.time()
    # Wait longer for frozen start
    while time.time() - start_time < 60:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Backend is ready.")
                
                # Launch GUI
                if HAS_WEBVIEW:
                    print("Launching pywebview...")
                    # This must be called from Main Thread, so we set a flag or just print here
                    # Actually webview.start() blocks main thread, so we can't call it here.
                    # This thread is just checking backend.
                    return True
                else:
                    print(f"Opening application at {start_url}")
                    webbrowser.open(start_url)
                    return True
        except requests.ConnectionError:
            time.sleep(0.5)
        except Exception as e:
            print(f"Error checking backend: {e}")
            time.sleep(1)
            
    print("Timed out waiting for backend.")
    return False

def on_closed():
    print("Application closed. Cleaning up...")
    if backend_process:
        backend_process.terminate()
    # If using webview, this might handle itself, but force exit is safer
    os._exit(0)

if __name__ == "__main__":
    # Check arguments for custom modes
    # Usage: ContentForge.exe run-script <script.py> [args]
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "run-script":
            # Delegate to script runner
            run_script_mode(sys.argv[2:])
            sys.exit(0)

    # Normal Application Startup
    
    # Check if port is already in use
    if is_port_in_use(PORT):
        print(f"Backend already running on port {PORT}")
        sys.exit(0)

    # Determine execution mode
    check_frozen = getattr(sys, 'frozen', False)

    # Start Backend in a separate thread (Frozen) or process (Dev)
    if check_frozen:
        t = threading.Thread(target=start_server_frozen, daemon=True)
        t.start()
    else:
        start_server_dev()

    # Wait for backend in a separate thread
    # If using webview, we need to wait BEFORE creating window? 
    # No, webview needs to be created on main thread. We can check backend in bg
    # but webview load_url might fail if backend isn't ready.
    # Pywebview allows creating window and then loading URL later or waiting.
    
    # For simplicity, let's start the checker thread
    if not HAS_WEBVIEW:
        threading.Thread(target=wait_for_backend_and_launch, daemon=True).start()
        
        # Keep main thread alive for dev mode / browser mode
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            on_closed()
            
    else:
        # WEBVIEW MODE (Blocking Main Thread)
        print("Initializing Desktop App Mode...")
        
        # We need to wait for backend before showing window ideally, 
        # or show a loading screen?
        # Let's just create window pointing to URL. If it fails, it shows error.
        # But we can assume uvicorn starts fast.
        
        # We'll spawn a thread to check backend readiness
        def check_ready():
            wait_for_backend_and_launch()
            
        threading.Thread(target=check_ready, daemon=True).start()
        
        window = webview.create_window('ContentForge', f"http://{HOST}:{PORT}", width=1280, height=800)
        webview.start()
        on_closed()



