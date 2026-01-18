import os
import subprocess
import shutil
import sys
from pathlib import Path

def print_step(message):
    print(f"\n{'='*50}")
    print(f" {message}")
    print(f"{'='*50}")

def run_command(command, cwd=None, shell=True):
    try:
        print(f"Running: {command}")
        subprocess.check_call(command, cwd=cwd, shell=shell)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        sys.exit(1)

def main():
    root_dir = Path(__file__).parent.absolute()
    frontend_dir = root_dir / "frontend"
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"

    print_step("Starting ContentForge Build Process")

    # 1. Clean previous builds
    # 1. Clean previous builds
    print_step("Cleaning previous builds...")
    # Helper to remove readonly
    def remove_readonly(func, path, excinfo):
        os.chmod(path, 0o777)
        func(path)

    if dist_dir.exists():
        print(f"Removing {dist_dir}...")
        try:
            shutil.rmtree(dist_dir, onerror=remove_readonly)
        except Exception as e:
            print(f"Warning: Could not fully remove dist dir: {e}")
            print("Make sure no other processes (like a running server) are using it.")
            
    if build_dir.exists():
        try:
            shutil.rmtree(build_dir, onerror=remove_readonly)
            print(f"Removed {build_dir}")
        except Exception as e:
            print(f"Warning: Could not remove build dir: {e}")

    # 2. Build Frontend
    print_step("Building Frontend...")
    if not frontend_dir.exists():
        print("Error: frontend directory not found!")
        sys.exit(1)
    
    # Check if node_modules exists, if not install dependencies
    if not (frontend_dir / "node_modules").exists():
        print("Installing frontend dependencies...")
        run_command("npm install", cwd=frontend_dir)
    
    run_command("npm run build", cwd=frontend_dir)

    # 3. Package Backend with PyInstaller
    print_step("Packaging Backend with PyInstaller...")
    spec_file = root_dir / "ContentForge.spec"
    if not spec_file.exists():
        print("Error: ContentForge.spec not found!")
        sys.exit(1)

    run_command(f"pyinstaller --clean {spec_file.name}", cwd=root_dir)

    # 4. Final Checks
    exe_path = dist_dir / "ContentForge" / "ContentForge.exe"
    if exe_path.exists():
        print_step("Build Successful!")
        print(f"Executable created at: {exe_path}")
        print("You can verify it by running the executable.")
    else:
        print_step("Build Failed!")
        print("Executable not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
