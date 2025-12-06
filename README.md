# ContentForge-UI

ContentForge-UI is a powerful, local web-based toolbox designed for power users, translators, and archivists who work with E-books (EPUB/TXT) and Comics (PDF/Images). It features a modern React frontend and a robust Python backend, offering a suite of automation tools for file conversion, editing, and organization.

## 🚀 Features

### 📚 Ebook Workshop
A comprehensive suite for processing novel and e-book files:
- **TXT ↔ EPUB Conversion**: Convert text files to EPUB with customizable styling, or extract text from existing EPUBs.
- **EPUB Editing**:
  - **Split EPUB**: Break down large EPUB files into smaller parts.
  - **Pack/Unpack**: Easily Decompile EPUBs to source folders and recompile them.
  - **Cover Repair**: Fix missing or incorrect cover images.
  - **CSS Fixer**: Extract, analyze, and repair CSS styles.
  - **Styler**: Apply batch styling updates to multiple EPUBs.
  - **Cleaner**: Remove unwanted fonts or metadata to reduce file size.
  - **TC ↔ SC**: Convert between Traditional and Simplified Chinese.
- **Text Processing**:
  - **Batch Replacer**: Advanced text replacement using regex and dictionary files.
  - **Punctuation Fixer**: Auto-correct common ebook punctuation errors.
  - **Encoding Fixer**: Repair broken text encoding (GBK/UTF-8).
  - **Reformatter**: Clean up line breaks and formatting in TXT files.
  - **Markdown to HTML**: Convert documentation or stories written in Markdown to standalone HTML.

### 🎨 Comic Processing
Tools optimized for manga and comic management:
- **PDF Merge**: intelligently merge multiple PDF files from subdirectories.
- **Image to PDF**: Convert folders of images into optimized PDF files.
- **Image Pipeline**: Advanced batch processing for image upscaling or cleaning (v5 pipeline).

### ⬇️ Downloaders
- **Diritto Downloader**: Specialized downloader for *diritto.co.kr*.
  - **Auto-Browser Integration**: Automatically launches and connects to a Chrome instance for session handling.
  - **URL Extractor**: Scrape ranking pages to bulk-extract novel URLs.
  - **Robust Extraction**: Handles complex DOM structures and "ProseMirror" content.

### 🗂️ File Organization
- **Folder Codec**: Securely pack folders into encrypted archives (7z/zip) and unpack them with ease.

---

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.10+**
- **Node.js 16+** & **npm**
- **Google Chrome** (for Diritto downloader)

### Backend Setup
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Ensure you have `ebooklib`, `Appium-Python-Client`, `selenium`, `fastapi`, `uvicorn`, `pikepdf`, `narsort`, `tqdm`, `opencc`, `beautifulsoup4`, etc.)*

### Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Build the frontend integration:
   ```bash
   npm run build
   ```

---

## 🖥️ Usage

### Running the Application (All-in-One)
The easiest way to run ContentForge is using the provided `run.py` script in the root directory. This script launches both the backend server and serves the frontend.

```bash
python run.py
```
- Access the UI at: `http://127.0.0.1:8000`

### Manual Start
**Backend:**
```bash
uvicorn app:app --port 8000 --reload
```

**Frontend (Dev Mode):**
```bash
cd frontend
npm run dev
```

---

## ⚙️ Configuration

### Settings
The application uses a centralized `settings.json` located in `backend/shared_assets/settings.json`.
You can configure the **Default Work Directory** via the "Settings" tab in the UI. All tools will default to this directory for input/output operations unless overridden.

### Browser Automation
For tools requiring browser automation (like Diritto Downloader), the system attempts to auto-launch Chrome with remote debugging on port `9222`. Ensure your Chrome installation is standard, or the script will try to detect `chrome.exe` or `msedge.exe`.

---

## ⚠️ Disclaimer
This tool is for educational and personal archiving purposes only. Please respect copyright laws and terms of service of any third-party websites you interact with.
