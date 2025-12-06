import os
import sys
import subprocess
import threading
import time
import socket
import requests

# Configuration
HOST = "127.0.0.1"
PORT = 8000

backend_process = None

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) == 0

def start_backend():
    global backend_process
    if is_port_in_use(PORT):
        print(f"Backend already running on port {PORT}")
        return

    print("Starting Backend...")
    # Run uvicorn as a subprocess
    cmd = [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", HOST, "--port", str(PORT)]
    
    # Hide console window on Windows
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    backend_process = subprocess.Popen(cmd, cwd=os.getcwd(), startupinfo=startupinfo)

def wait_for_backend():
    url = f"http://{HOST}:{PORT}/health"
    start_time = time.time()
    while time.time() - start_time < 30:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.ConnectionError:
            time.sleep(0.5)
    return False

def on_closed():
    print("Application closed. Cleaning up...")
    if backend_process:
        backend_process.terminate()
    os._exit(0)

if __name__ == "__main__":
    # 1. Start Backend
    start_backend()

    # 2. Wait for Backend
    print(f"Waiting for backend at http://{HOST}:{PORT}...")
    if wait_for_backend():
        print("Backend is ready.")
    else:
        print("Failed to start backend.")
        sys.exit(1)

    # 3. Open in Browser
    start_url = f"http://{HOST}:{PORT}"
    print(f"Opening application at {start_url}")
    
    import webbrowser
    webbrowser.open(start_url)

    print("Application is running. Press Ctrl+C to stop.")
    
    # 4. Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        on_closed()

