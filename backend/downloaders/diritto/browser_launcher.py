#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser Launcher Utility for Diritto Scripts
Automatically detects and launches Chrome with remote debugging enabled.
"""
import os
import sys
import time
import subprocess
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def is_chrome_running_on_port(port=9222):
    """
    Check if Chrome is already running with debugging enabled on the specified port.
    
    Args:
        port: Debug port number (default: 9222)
    
    Returns:
        bool: True if Chrome is listening on the port, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except Exception:
        return False


def find_chrome_executable():
    """
    Find Chrome executable path based on operating system.
    
    Returns:
        str: Path to Chrome executable, or None if not found
    """
    system = sys.platform
    
    if system == 'win32':
        # Windows paths
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
            # Edge as fallback (also supports remote debugging)
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
    elif system == 'darwin':
        # macOS paths
        possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
    else:
        # Linux paths
        possible_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def launch_chrome(port=9222, user_data_dir=None):
    """
    Launch Chrome with remote debugging enabled.
    
    Args:
        port: Debug port number (default: 9222)
        user_data_dir: Custom user data directory (optional)
    
    Returns:
        subprocess.Popen: Process handle if launched, None if already running
    """
    if is_chrome_running_on_port(port):
        print(f"[信息] Chrome 已在端口 {port} 运行，将连接到现有实例。")
        return None
    
    chrome_path = find_chrome_executable()
    if not chrome_path:
        print("❌ 错误: 未找到 Chrome 浏览器。")
        print("请确保已安装 Google Chrome 或 Microsoft Edge。")
        return None
    
    # Set default user data dir if not provided
    if user_data_dir is None:
        if sys.platform == 'win32':
            user_data_dir = r'C:\selenium\chrome_profile'
        else:
            user_data_dir = os.path.expanduser('~/selenium/chrome_profile')
    
    # Create user data directory if it doesn't exist
    os.makedirs(user_data_dir, exist_ok=True)
    
    # Build command
    cmd = [
        chrome_path,
        f'--remote-debugging-port={port}',
        f'--user-data-dir={user_data_dir}',
    ]
    
    print(f"[信息] 正在启动 Chrome 浏览器...")
    print(f"  - 调试端口: {port}")
    print(f"  - 数据目录: {user_data_dir}")
    
    try:
        # Launch Chrome in background
        if sys.platform == 'win32':
            # On Windows, use CREATE_NEW_PROCESS_GROUP to detach
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
        else:
            # On Unix-like systems
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        
        # Wait for Chrome to start
        print("[信息] 等待 Chrome 启动...")
        max_wait = 10  # seconds
        for i in range(max_wait):
            time.sleep(1)
            if is_chrome_running_on_port(port):
                print("✅ Chrome 已成功启动！")
                return process
        
        print("⚠️ 警告: Chrome 启动超时，但将尝试连接...")
        return process
        
    except Exception as e:
        print(f"❌ 启动 Chrome 失败: {e}")
        return None


def setup_driver_with_auto_launch(port=9222, user_data_dir=None):
    """
    Setup Selenium WebDriver with automatic Chrome launching.
    Tries to connect to existing Chrome instance, or launches new one if needed.
    
    Args:
        port: Debug port number (default: 9222)
        user_data_dir: Custom user data directory (optional)
    
    Returns:
        webdriver.Chrome: Configured WebDriver instance, or None if failed
    """
    print("\\n[信息] 正在连接到 Chrome 浏览器 (调试端口 {})...".format(port))
    
    # Check if Chrome is already running first
    if not is_chrome_running_on_port(port):
        print("[信息] 未检测到运行中的 Chrome 实例。")
        print("[信息] 正在自动启动 Chrome 浏览器...")
        
        # Launch Chrome
        process = launch_chrome(port=port, user_data_dir=user_data_dir)
        if process is None and not is_chrome_running_on_port(port):
            print("\\n❌ 无法启动 Chrome 浏览器。")
            print("您可以手动启动 Chrome:")
            if sys.platform == 'win32':
                print(f'  chrome.exe --remote-debugging-port={port} --user-data-dir="C:\\\\selenium\\\\chrome_profile"')
            else:
                print(f'  google-chrome --remote-debugging-port={port} --user-data-dir=~/selenium/chrome_profile')
            return None
    
    # Now try to connect
    options = Options()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ 成功连接到浏览器！")
        return driver
    except Exception as e:
        print(f"⚠️ 连接现有浏览器失败: {e}")
        print("尝试清理占用端口的进程并重启浏览器...")
        
        # 尝试杀掉占用端口的进程
        try:
            if sys.platform != 'win32':
                os.system(f"lsof -t -i:{port} | xargs kill -9")
            else:
                 # Windows kill command
                 os.system(f"netstat -ano | findstr :{port} > pid.txt")
                 # 简单的 Windows 处理逻辑可能比较复杂，这里暂略，主要针对 Mac 用户优化
                 pass
            time.sleep(2)
        except Exception:
            pass

        # 重试启动
        print("[信息] 正在重新启动 Chrome 浏览器...")
        process = launch_chrome(port=port, user_data_dir=user_data_dir)
        if process:
             try:
                 driver = webdriver.Chrome(options=options)
                 print("✅ 重启后成功连接到浏览器！")
                 return driver
             except Exception as e2:
                 print(f"❌ 重启后连接失败: {e2}")
        
        return None


if __name__ == "__main__":
    # Test the launcher
    print("=== Chrome Browser Launcher Test ===")
    driver = setup_driver_with_auto_launch()
    if driver:
        print("\\n测试成功！浏览器已连接。")
        driver.get("https://www.google.com")
        print("已导航到 Google 首页。")
        input("按 Enter 键关闭...")
        driver.quit()
    else:
        print("\\n测试失败。")
