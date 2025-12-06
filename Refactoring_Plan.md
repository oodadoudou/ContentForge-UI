# ContentForge Desktop Refactoring Plan

## 1. 目标 (Goal)
将现有的 Python 脚本集合重构为一个 **Windows Desktop Application**。
核心要求：
*   **UI 框架**: Flet (Python)。
*   **架构**: 前端 UI + 后端脚本 (直接调用现有脚本逻辑，而非 API)。
*   **特性**: 实时显示脚本运行日志 (stdout/stderr) 到 UI 控制台。
*   **结构调整**: 遵循 `structure.txt` 的目录重构要求。

## 2. 目录重构 (Directory Restructuring)

根据 `structure.txt`，将执行以下文件移动和重命名操作：

### 2.1 模块合并与重命名
*   **[MERGE]** 将 `04_file_repair` 目录下的所有脚本移动到 `03_ebook_workshop`：
    *   `cover_repair.py` -> `03_ebook_workshop/cover_repair.py`
    *   `css_fixer.py` -> `03_ebook_workshop/css_fixer.py`
    *   `fix_txt_encoding.py` -> `03_ebook_workshop/fix_txt_encoding.py`
    *   `txt_reformat.py` -> `03_ebook_workshop/txt_reformat.py`
    *   *Action*: 移动后删除空目录 `04_file_repair`。
*   **[RENAME]** 将 `05_library_organization` 重命名为 `file_organization`。
*   **[MOVE]** 将 `extract_epub_css.py` 从 `file_organization` (原 05) 移动到 `03_ebook_workshop`。

### 2.2 平台相关调整
*   `01_acquisition/update_token.py`: 标注为 "supported only on mac"。
    *   *Refactor*: 需要检查代码中的平台依赖代码 (如 AppleScript 或 macOS 特定路径)，并尝试添加 Windows 支持，或者在 Windows 上禁用/提示不可用。

### 2.3 Bug Fixes
*   `07_downloader/diritto_downloader.py`: 标记为 needs bugfix。
    *   *Action*: 需要读取代码并分析潜在错误（需用户提供具体 bug 描述，或自行进行静态代码分析检查常见错误）。

## 3. 技术架构设计 (Technical Architecture)

### 3.1 核心模式: UI Wrapper
不重写业务逻辑，而是将 Flet UI 作为"壳" (Wrapper) 包裹现有脚本。

*   **前端 (Frontend)**: Flet 页面，负责接收用户输入 (路径、选项) 并显示日志。
*   **后端 (Backend)**: Python `subprocess` 或 `threading` 调用。

### 3.2 实时日志系统 (Real-time Logging System)
为了将脚本的 `print()` 输出实时显示在 UI console 中，采用 **重定向标准输出** 或 **子进程管道**。

#### 方案 A: 子进程 (Subprocess) - 推荐
适用于独立运行的脚本 (如 `main.py` 调用的那些)。
```python
import subprocess
import threading

def run_script(script_path, args, log_callback):
    process = subprocess.Popen(
        ['python', script_path] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # 读取输出并回调给 UI
    def read_output(pipe):
        for line in pipe:
            log_callback(line.strip())
            
    threading.Thread(target=read_output, args=(process.stdout,)).start()
    threading.Thread(target=read_output, args=(process.stderr,)).start()
```

#### 方案 B: 导入调用 (Import & Invoke)
直接导入模块中的 `main()` 函数。需要重写 `sys.stdout` 来捕获输出。
*   *优点*: 进程内通信，控制更灵活。
*   *缺点*: 现有脚本如果大量使用全局变量或没有良好的封装，可能会污染 UI 进程状态。
*   *决定*: 鉴于脚本独立性较高，**优先混合使用**：对于简单的功能函数直接导入调用；对于复杂的全流程脚本使用子进程调用。

## 4. 详细实施步骤 (Implementation Details)

### Phase 1: 准备工作
1.  **备份**: 备份当前项目。
2.  **重构目录**: 执行 Section 2 中的文件移动和重命名。
3.  **依赖安装**: 添加 `flet` 到 `requirements.txt`。

### Phase 2: UI 框架搭建
1.  **Main Window**: 使用 Flet 构建侧边栏布局 (Sidebar + Main Content + Console)。
2.  **Global Settings**: 实现顶部 "工作目录" 状态管理 (使用 Flet 的 `page.client_storage` 或全局单例类 `AppState`)。
3.  **Console Component**: 封装一个可重用的 `ConsoleView` 组件，支持 `append_log(text)` 方法。

### Phase 3: 模块集成 (按模块逐个实现)
对每个功能模块：
1.  **UI 构建**: 根据设计文档创建输入表单。
2.  **逻辑绑定**: 
    *   将 UI 参数拼装为 CLI 参数或函数参数。
    *   调用脚本执行。
    *   将输出流导向底部 Console。

#### 3.1 模块: Acquisition (01)
*   界面: 需适配 Windows。若 `update_token` 仅限 Mac，则在 Windows 端隐藏该按钮或显示提示。

#### 3.2 模块: Comic Processing (02)
*   功能: 图片转 PDF、合并 PDF 等。
*   集成: 调用 `image_processes_pipeline_v5.py` 等。

#### 3.3 模块: Ebook Workshop (03 + 04 Merged)
*   功能: 包含原 03 和 04 的所有 EPUB 修复/转换功能。
*   集成: 整合大量工具脚本，建议按功能分组 (转换组、修复组)。

#### 3.4 模块: File Organization (Old 05)
*   集成: `translate_and_org_dirs.py`。需要用户输入 OpenAI Key。

#### 3.5 模块: Downloader (07)
*   **任务**: 修复 `diritto_downloader.py` (需先诊断问题)。
*   集成: 通用下载界面。

### Phase 4: 打包与测试
1.  **Windows 兼容性检查**: 确保所有路径拼接使用 `os.path.join` 或 `pathlib`。
2.  **打包**: 使用 `flet pack main_ui.py` 生成 exe。
