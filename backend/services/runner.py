import asyncio
import logging
from typing import Callable, Awaitable, List, Optional
from typing import Callable, Awaitable, List, Optional
import os
import subprocess

logger = logging.getLogger(__name__)

class ScriptRunner:
    def __init__(self):
        self.process: Optional[asyncio.subprocess.Process] = None
        self.last_activity_time: float = 0.0
        self.timeout_seconds: int = 1800  # 30 minutes

    async def run(self, command: List[str], work_dir: str, log_callback: Callable[[str], Awaitable[None]]):
        """
        Executes a command in a subprocess and streams output to log_callback.
        """
        if not os.path.exists(work_dir):
             await log_callback(f"[ERROR] Working directory does not exist: {work_dir}")
             return -1

        # Adjust command for PyInstaller frozen environment
        import sys
        if getattr(sys, 'frozen', False):
            if command and (command[0] == 'python' or command[0] == 'python3'):
                exe_path = sys.executable
                
                # Identify script path from command
                # Dev Command: ['python', '-u', 'D:/.../backend/script.py', 'args']
                # We need to find the script part and remap it
                script_path_index = -1
                for i, arg in enumerate(command):
                    if i > 0 and (arg.endswith('.py') or 'backend' in arg.replace('\\', '/')):
                        script_path_index = i
                        break
                
                if script_path_index != -1:
                    original_path = command[script_path_index]
                    # Logic: Find 'backend' in the path and get everything after it
                    # Normalize slashes
                    norm_path = original_path.replace('\\', '/')
                    if 'backend/' in norm_path:
                        rel_path = norm_path.split('backend/', 1)[1]
                        # In frozen app (onedir or onefile), 'backend' is at root of sys._MEIPASS or dist dir
                        # Actually in onedir, it's just ./backend/<script>
                        # In onefile, it's sys._MEIPASS/backend/<script>
                        bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
                        
                        # We bundled 'backend' folder as-is into root
                        new_script_path = os.path.join(bundle_dir, 'backend', rel_path)
                        command[script_path_index] = new_script_path
                        await log_callback(f"[SYSTEM] Remapped script path to: {new_script_path}")

                # Transform: python script.py args -> ContentForge.exe run-script script.py args
                new_command = [exe_path, 'run-script'] + command[1:]
                # Remove '-u' if present as run-script handles it
                if '-u' in new_command:
                    new_command.remove('-u')
                    
                await log_callback(f"[SYSTEM] Frozen Env: Routing through {os.path.basename(exe_path)}")
                command = new_command

        logger.info(f"Starting command: {command} in {work_dir}")
        await log_callback(f"[SYSTEM] Starting: {' '.join(command)}")
        await log_callback(f"[SYSTEM] CWD: {work_dir}")
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                *command,
                cwd=work_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            self.last_activity_time = asyncio.get_event_loop().time()
        except Exception as e:
            await log_callback(f"[ERROR] Failed to start process: {str(e)}")
            logger.error(f"Failed to start process: {e}")
            return -1

        # Start timeout monitor
        monitor_task = asyncio.create_task(self._monitor_timeout(log_callback))

        # Concurrently read stdout and stderr
        try:
            await asyncio.gather(
                self._read_stream(self.process.stdout, "INFO", log_callback),
                self._read_stream(self.process.stderr, "ERROR", log_callback)
            )
            exit_code = await self.process.wait()
        except asyncio.CancelledError:
            logger.info("Process execution cancelled")
            exit_code = -1
        finally:
            monitor_task.cancel()
        
        await log_callback(f"[SYSTEM] Process finished with exit code {exit_code}")
        return exit_code

    async def _read_stream(self, stream: asyncio.StreamReader, level: str, callback: Callable[[str], Awaitable[None]]):
        """Reads a stream line by line until EOF."""
        if not stream:
            return
            
        while True:
            line_bytes = await stream.readline()
            if not line_bytes:
                break
            
            # Update activity time
            self.last_activity_time = asyncio.get_event_loop().time()

            # Decode with replacement to avoid crashing on bad chars
            line = line_bytes.decode('utf-8', errors='replace').rstrip()
            if line:
                await callback(f"[{level}] {line}")

    async def _monitor_timeout(self, callback: Callable[[str], Awaitable[None]]):
        """Monitors inactivity and kills process if timeout reached."""
        while True:
            await asyncio.sleep(5)
            if self.process and self.process.returncode is None:
                elapsed = asyncio.get_event_loop().time() - self.last_activity_time
                if elapsed > self.timeout_seconds:
                    await callback(f"[SYSTEM] Timeout: No activity for {self.timeout_seconds}s. Terminating.")
                    await self.terminate()
                    break

    async def write_stdin(self, text: str):
        """Writes text to the process stdin."""
        if self.process and self.process.stdin:
            try:
                # Update activity time
                self.last_activity_time = asyncio.get_event_loop().time()
                
                input_bytes = (text + "\n").encode('utf-8')
                self.process.stdin.write(input_bytes)
                await self.process.stdin.drain()
            except Exception as e:
                logger.error(f"Failed to write to stdin: {e}")

    async def terminate(self):
        if self.process and self.process.returncode is None:
            try:
                self.process.terminate()
                # Give it a bit to terminate
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.process.kill()
            except Exception as e:
                logger.error(f"Error terminating process: {e}")
