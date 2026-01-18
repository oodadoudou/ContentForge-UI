import os
import signal
import psutil
import logging
import time

logger = logging.getLogger(__name__)

def kill_proc_tree(pid, including_parent=True):
    """
    Terminates a process and its children recursively.
    """
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # Kill children first
        for child in children:
            try:
                logger.info(f"Terminating child process: {child.pid} ({child.name()})")
                child.terminate()
            except psutil.NoSuchProcess:
                pass
                
        _, alive = psutil.wait_procs(children, timeout=3)
        for p in alive:
            try:
                logger.warning(f"Force killing child process: {p.pid} ({p.name()})")
                p.kill()
            except psutil.NoSuchProcess:
                pass

        if including_parent:
            try:
                logger.info(f"Terminating parent process: {parent.pid} ({parent.name()})")
                parent.terminate()
                parent.wait(3)
            except psutil.NoSuchProcess:
                pass
            except psutil.TimeoutExpired:
                logger.warning(f"Force killing parent process: {parent.pid}")
                parent.kill()
                
    except psutil.NoSuchProcess:
        pass

def free_port(port):
    """
    Finds the process using the specified port and terminates it.
    """
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    logger.info(f"Port {port} is in use by process {proc.pid} ({proc.name()}). Cleaning up...")
                    kill_proc_tree(proc.pid)
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def cleanup_resources(port=8000):
    """
    Comprehensive cleanup:
    1. Kills all child processes of the current process.
    2. Frees the target port if still occupied.
    """
    logger.info("Starting resource cleanup...")
    
    # 1. Clean up child processes of the current process
    current_process = psutil.Process(os.getpid())
    children = current_process.children(recursive=True)
    if children:
        logger.info(f"Found {len(children)} child processes to clean up.")
        for child in children:
            kill_proc_tree(child.pid, including_parent=True)
    
    # 2. Ensure Port is free (in case it was held by a detached process)
    if free_port(port):
        logger.info(f"Port {port} successfully freed.")
    else:
        logger.info(f"Port {port} was already free.")
        
    logger.info("Cleanup complete.")
