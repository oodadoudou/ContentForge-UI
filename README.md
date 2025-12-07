# ContentForge-UI

ContentForge-UI 是一个强大的本地化网页端工具箱，专为处理电子书（EPUB/TXT）和漫画（PDF/Images）的高级用户、翻译人员和归档人员设计。它拥有现代化的 React 前端和稳健的 Python 后端，提供了一系列用于文件转换、编辑和整理的自动化工具。

ContentForge-UI is a powerful, local web-based toolbox designed for power users, translators, and archivists who work with E-books (EPUB/TXT) and Comics (PDF/Images). It features a modern React frontend and a robust Python backend, offering a suite of automation tools for file conversion, editing, and organization.

---

## 🚀 功能特性 (Features)

### 📚 电子书工坊 (Ebook Workshop)
一套用于处理小说和电子书文件的综合套件：
- **TXT ↔ EPUB 转换 (TXT ↔ EPUB Conversion)**: 将文本文件转换为具有自定义样式的 EPUB，或从现有 EPUB 中提取文本。
- **EPUB 编辑 (EPUB Editing)**:
  - **分割 EPUB (Split EPUB)**: 将大型 EPUB 文件分割成较小的部分。
  - **解包/打包 (Pack/Unpack)**: 轻松将 EPUB 反编译为源文件夹并重新编译。
  - **封面修复 (Cover Repair)**: 修复缺失或错误的封面图像。
  - **CSS 修复 (CSS Fixer)**: 提取、分析并修复 CSS 样式。
  - **样式美化 (Styler)**: 对多个 EPUB 应用批量样式更新。
  - **清理工具 (Cleaner)**: 移除不需要的字体或元数据以减小文件大小。
  - **繁简转换 (TC ↔ SC)**: 在繁体中文和简体中文之间转换。
- **文本处理 (Text Processing)**:
  - **批量替换 (Batch Replacer)**: 使用正则表达式和字典文件进行高级文本替换。
  - **标点修复 (Punctuation Fixer)**: 自动更正常见的电子书标点符号错误。
  - **编码修复 (Encoding Fixer)**: 修复损坏的文本编码（GBK/UTF-8）。
  - **重排版 (Reformatter)**: 清理 TXT 文件中的换行和格式。
  - **Markdown 转 HTML (Markdown to HTML)**: 将 Markdown 编写的文档或故事转换为独立的 HTML。

### 🎨 漫画处理 (Comic Processing)
专为漫画管理优化的工具：
- **PDF 合并 (PDF Merge)**: 智能合并子目录中的多个 PDF 文件。
- **图片转 PDF (Image to PDF)**: 将图片文件夹转换为优化后的 PDF 文件。
- **图片处理流 (Image Pipeline)**: 用于图片放大或清理的高级批处理流程 (v5 管道)。

### ⬇️ 下载器 (Downloaders)
- **Diritto 下载器 (Diritto Downloader)**: 针对 *diritto.co.kr* 的专用下载器。
  - **自动浏览器集成 (Auto-Browser Integration)**: 自动启动并连接 Chrome 实例以处理会话。
  - **URL 提取器 (URL Extractor)**: 抓取排行榜页面以批量提取小说 URL。
  - **强大的提取能力 (Robust Extraction)**: 处理复杂的 DOM 结构和 "ProseMirror" 内容。
  - **目录清理 (Auto-Cleanup)**: 自动检测下载失败（0 成功章节）并删除空文件夹。

### 🗂️ 文件整理 (File Organization)
- **文件夹编解码 (Folder Codec)**: 将文件夹安全打包为加密的压缩包 (7z/zip) 并轻松解包。

---

## 🛠️ 安装与设置 (Installation & Setup)

### 前置要求 (Prerequisites)
- **Python 3.10+**
- **Node.js 16+** & **npm**
- **Google Chrome** (用于 Diritto 下载器 / for Diritto downloader)

### 后端设置 (Backend Setup)
1. 进入 `backend` 目录:
   ```bash
   cd backend
   ```
2. 安装 Python 依赖:
   ```bash
   pip install -r requirements.txt
   ```
   *(注意: 确保已安装 `ebooklib`, `Appium-Python-Client`, `selenium`, `fastapi`, `uvicorn`, `pikepdf`, `narsort`, `tqdm`, `opencc`, `beautifulsoup4` 等依赖)*

### 前端设置 (Frontend Setup)
1. 进入 `frontend` 目录:
   ```bash
   cd frontend
   ```
2. 安装 Node 依赖:
   ```bash
   npm install
   ```
3. 构建前端集成:
   ```bash
   npm run build
   ```

---

## 🖥️ 使用方法 (Usage)

### 运行应用程序 (Running the Application)
运行 ContentForge 最简单的方法是使用根目录下的 `run.py` 脚本。该脚本会启动后端服务器并提供前端服务。
The easiest way to run ContentForge is using the provided `run.py` script in the root directory.

```bash
python run.py
```
- 访问 UI 地址: `http://127.0.0.1:8000`

### 手动启动 (Manual Start)
**后端 (Backend):**
```bash
uvicorn app:app --port 8000 --reload
```

**前端 (开发模式) (Frontend Dev Mode):**
```bash
cd frontend
npm run dev
```

---

## ⚙️ 配置 (Configuration)

### 设置 (Settings)
应用程序使用位于 `backend/shared_assets/settings.json` 的集中式配置文件。
您可以通过 UI 中的 "Settings" 选项卡配置 **默认工作目录 (Default Work Directory)**。除非被覆盖，否则所有工具都将默 认使用此目录进行输入/输出操作。

The application uses a centralized `settings.json` located in `backend/shared_assets/settings.json`.
You can configure the **Default Work Directory** via the "Settings" tab in the UI.

### 浏览器自动化 (Browser Automation)
对于需要浏览器自动化的工具（如 Diritto 下载器），系统会尝试自动启动带有远程调试端口 `9222` 的 Chrome。请确保您的 Chrome 安装是标准的，否则脚本将尝试检测 `chrome.exe` 或 `msedge.exe`。

For tools requiring browser automation (like Diritto Downloader), the system attempts to auto-launch Chrome with remote debugging on port `9222`.

---

## ⚠️ 免责声明 (Disclaimer)
本工具仅供教育和个人归档使用。请遵守您交互的任何第三方网站的版权法和服务条款。

This tool is for educational and personal archiving purposes only. Please respect copyright laws and terms of service of any third-party websites you interact with.
