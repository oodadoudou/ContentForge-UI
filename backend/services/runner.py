import asyncio
import logging
from typing import Callable, Awaitable, List, Optional
import os

logger = logging.getLogger(__name__)

class ScriptRunner:
    def __init__(self):
        self.process: Optional[asyncio.subprocess.Process] = None

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
                # For Windows compat if needed in future: creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception as e:
            await log_callback(f"[ERROR] Failed to start process: {str(e)}")
            logger.error(f"Failed to start process: {e}")
            return -1

        # Concurrently read stdout and stderr
        await asyncio.gather(
            self._read_stream(self.process.stdout, "INFO", log_callback),
            self._read_stream(self.process.stderr, "ERROR", log_callback)
        )
        
        exit_code = await self.process.wait()
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
            
            # Decode with replacement to avoid crashing on bad chars
            line = line_bytes.decode('utf-8', errors='replace').rstrip()
            if line:
                await callback(f"[{level}] {line}")

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
