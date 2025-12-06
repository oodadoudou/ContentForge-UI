import asyncio
import logging
from typing import Callable, Awaitable, List, Optional
import os

logger = logging.getLogger(__name__)

class ScriptRunner:
    def __init__(self):
        self.process: Optional[asyncio.subprocess.Process] = None
        self.last_activity_time: float = 0.0
        self.timeout_seconds: int = 180  # 3 minutes

    async def run(self, command: List[str], work_dir: str, log_callback: Callable[[str], Awaitable[None]]):
        """
        Executes a command in a subprocess and streams output to log_callback.
        """
        if not os.path.exists(work_dir):
             await log_callback(f"[ERROR] Working directory does not exist: {work_dir}")
             return -1

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
                # For Windows compat if needed in future: creationflags=subprocess.CREATE_NO_WINDOW
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
