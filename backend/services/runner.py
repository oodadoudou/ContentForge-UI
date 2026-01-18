import asyncio
import logging
import subprocess
import threading
import os
import sys
import queue
from typing import List, Callable, Awaitable, Optional

logger = logging.getLogger(__name__)

class ScriptRunner:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.last_activity_time: float = 0.0
        self.timeout_seconds: int = 1800  # 30 minutes
        self.stop_monitoring = False

    async def run(self, command: List[str], work_dir: str, log_callback: Callable[[str], Awaitable[None]]):
        """
        Executes a command using subprocess.Popen and threads for output reading.
        Safe for Windows SelectorEventLoop.
        """
        if not os.path.exists(work_dir):
             await log_callback(f"[ERROR] Working directory does not exist: {work_dir}")
             return -1

        # Adjust command for PyInstaller frozen environment
        if getattr(sys, 'frozen', False):
            if command and (command[0] == 'python' or command[0] == 'python3'):
                exe_path = sys.executable
                
                # Identify script path from command
                script_path_index = -1
                for i, arg in enumerate(command):
                    if i > 0 and (arg.endswith('.py') or 'backend' in arg.replace('\\', '/')):
                        script_path_index = i
                        break
                
                if script_path_index != -1:
                    original_path = command[script_path_index]
                    norm_path = original_path.replace('\\', '/')
                    if 'backend/' in norm_path:
                        rel_path = norm_path.split('backend/', 1)[1]
                        bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
                        new_script_path = os.path.join(bundle_dir, 'backend', rel_path)
                        command[script_path_index] = new_script_path
                        await log_callback(f"[SYSTEM] Remapped script path to: {new_script_path}")

                new_command = [exe_path, 'run-script'] + command[1:]
                if '-u' in new_command:
                    new_command.remove('-u')
                    
                await log_callback(f"[SYSTEM] Frozen Env: Routing through {os.path.basename(exe_path)}")
                command = new_command

        logger.info(f"Starting command: {command} in {work_dir}")
        await log_callback(f"[SYSTEM] Starting: {' '.join(command)}")
        await log_callback(f"[SYSTEM] CWD: {work_dir}")
        
        loop = asyncio.get_running_loop()
        self.stop_monitoring = False

        def read_stream(pipe, level):
            """Thread function to read from a pipe and schedule callback on main loop."""
            try:
                for line in iter(pipe.readline, b''):
                    line_str = line.decode('utf-8', errors='replace').rstrip()
                    if line_str:
                        # Thread-safe callback scheduling
                        asyncio.run_coroutine_threadsafe(
                            log_callback(f"[{level}] {line_str}"), loop
                        )
                        # Create a dummy task to update last activity asynchronously to avoid thread safety issues with floats? 
                        # Actually float assignment is atomic enough, but let's do it right.
                        # We'll just update self.last_activity_time here, it's thread-safe enough for a timestamp.
                        self.last_activity_time = loop.time()
            except Exception as e:
                logger.error(f"Error reading stream: {e}")
            finally:
                pipe.close()

        try:
            # Use Popen instead of asyncio.create_subprocess_exec
            self.process = subprocess.Popen(
                command,
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            self.last_activity_time = loop.time()

            # Start reader threads
            t_out = threading.Thread(target=read_stream, args=(self.process.stdout, "INFO"), daemon=True)
            t_err = threading.Thread(target=read_stream, args=(self.process.stderr, "ERROR"), daemon=True)
            t_out.start()
            t_err.start()

            # Monitor loop (async wait for Popen to finish)
            while self.process.poll() is None:
                await asyncio.sleep(0.1)
                
                # Check timeout
                elapsed = loop.time() - self.last_activity_time
                if elapsed > self.timeout_seconds:
                    await log_callback(f"[SYSTEM] Timeout: No activity for {self.timeout_seconds}s. Terminating.")
                    self.terminate()
                    break

            exit_code = self.process.poll()
            
        except Exception as e:
            await log_callback(f"[ERROR] Failed to start process: {str(e)}")
            logger.error(f"Failed to start process: {e}")
            return -1

        await log_callback(f"[SYSTEM] Process finished with exit code {exit_code}")
        return exit_code

    async def write_stdin(self, text: str):
        """Writes text to the process stdin."""
        if self.process and self.process.stdin:
            try:
                # We need to write from a thread because stdin.write might block? 
                # Popen stdin is a file object.
                # Let's do it in a thread to be safe/non-blocking to the loop.
                def _write():
                    try:
                        input_bytes = (text + "\n").encode('utf-8')
                        self.process.stdin.write(input_bytes)
                        self.process.stdin.flush()
                    except Exception as e:
                        logger.error(f"Failed to write to stdin: {e}")
                
                await asyncio.to_thread(_write)
                self.last_activity_time = asyncio.get_running_loop().time()
            except Exception as e:
                logger.error(f"Failed to dispatch stdin write: {e}")

    def terminate(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                # We can't await wait() here easily if this is called synchronously.
                # But Popen's terminate is non-blocking.
            except Exception as e:
                logger.error(f"Error terminating process: {e}")
