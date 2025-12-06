import os
import platform
from typing import Dict, List, Optional
from pydantic import BaseModel

class ScriptDef(BaseModel):
    id: str
    name: str
    path: str  # Relative to project root
    command_template: str  # Python format string
    required_args: List[str] = []
    platforms: List[str] = ["windows", "darwin", "linux"]  # Supported OS

# Helper to get current OS
current_os = platform.system().lower()

# Define all available scripts
SCRIPTS: Dict[str, ScriptDef] = {
    # --- Comic Processing ---
    "img_to_pdf": ScriptDef(
        id="img_to_pdf",
        name="Images to PDF",
        path="backend/comic_processing/convert_img_to_pdf.py",
        command_template="python {script_path} --input {input_dir} --output {output_dir}",
        required_args=["input_dir", "output_dir"]
    ),
    "merge_pdfs": ScriptDef(
        id="merge_pdfs",
        name="Merge PDFs",
        path="backend/comic_processing/merge_pdfs.py",
        command_template="python {script_path} --input {input_dir} --output {output_file}",
        required_args=["input_dir", "output_file"]
    ),

    "ai_pipeline_v5": ScriptDef(
        id="ai_pipeline_v5",
        name="AI Pipeline V5",
        path="backend/comic_processing/image_processes_pipeline_v5.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),

    # --- Ebook Workshop ---
    "txt_to_epub": ScriptDef(
        id="txt_to_epub",
        name="TXT to EPUB",
        path="backend/ebook_workshop/txt_to_epub_convertor.py",
        # txt_to_epub_convertor.py handles --input
        command_template="python {script_path} --input {input_dir}", 
        required_args=["input_dir"]
    ),
    "md_to_html": ScriptDef(
        id="md_to_html",
        name="Markdown to HTML",
        path="backend/ebook_workshop/convert_md_to_html.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),
    "epub_to_txt": ScriptDef(
        id="epub_to_txt",
        name="EPUB to TXT",
        path="backend/ebook_workshop/epub_to_txt_convertor.py",
        command_template="python {script_path} --input {input_dir} --output {output_dir}",
        required_args=["input_dir", "output_dir"]
    ),
    "epub_cleaner": ScriptDef(
        id="epub_cleaner",
        name="EPUB Cleaner",
        path="backend/ebook_workshop/epub_cleaner.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),
    "fix_txt_encoding": ScriptDef(
        id="fix_txt_encoding",
        name="Fix TXT Encoding",
        path="backend/ebook_workshop/fix_txt_encoding.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),
    "css_fixer": ScriptDef(
        id="css_fixer",
        name="CSS Fixer",
        path="backend/ebook_workshop/css_fixer.py",
        command_template="python {script_path}", 
        required_args=[]
    ),
    "cover_repair": ScriptDef(
        id="cover_repair",
        name="Cover Repair",
        path="backend/ebook_workshop/cover_repair.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),
     "punctuation_fixer": ScriptDef(
        id="punctuation_fixer",
        name="Punctuation Fixer",
        path="backend/ebook_workshop/punctuation_fixer.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),
    "download_rules": ScriptDef(
        id="download_rules",
        name="Download Rules Template",
        path="backend/ebook_workshop/copy_rules_template.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),
    "batch_replacer": ScriptDef(
        id="batch_replacer",
        name="Batch Replacer",
        path="backend/ebook_workshop/batch_replacer_v2.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),
    "split_epub": ScriptDef(
        id="split_epub",
        name="Split EPUB",
        path="backend/ebook_workshop/split_epub.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),
    "extract_css": ScriptDef(
        id="extract_css",
        name="Extract CSS",
        path="backend/ebook_workshop/extract_epub_css.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),
    "epub_styler": ScriptDef(
        id="epub_styler",
        name="EPUB Styler",
        path="backend/ebook_workshop/epub_styler.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),

    # --- Downloaders ---
    "bomtoon_login": ScriptDef(
        id="bomtoon_login",
        name="Bomtoon Login (Mac)",
        path="backend/downloaders/bomtoon/update_token.py",
        command_template="python {script_path}",
        platforms=["darwin", "windows"]
    ),
     "bomtoon_list": ScriptDef(
        id="bomtoon_list",
        name="Bomtoon List Comics",
        path="backend/downloaders/bomtoon/bomtoontwext.py",
        command_template="python {script_path} list-comic",
        required_args=[]
    ),
    "bomtoon_search": ScriptDef(
        id="bomtoon_search",
        name="Bomtoon Search",
        path="backend/downloaders/bomtoon/bomtoontwext.py",
        command_template="python {script_path} search {query}",
        required_args=["query"]
    ),
    "bomtoon_dl": ScriptDef(
        id="bomtoon_dl",
        name="Bomtoon Download",
        path="backend/downloaders/bomtoon/bomtoontwext.py",
        command_template="python {script_path} dl -o {output_dir} {comic_id} {chapter_ids}",
        required_args=["output_dir", "comic_id", "chapter_ids"]
    ),
    "bomtoon_dl_all": ScriptDef(
        id="bomtoon_dl_all",
        name="Bomtoon Download All",
        path="backend/downloaders/bomtoon/bomtoontwext.py",
        command_template="python {script_path} dl-all -o {output_dir} {comic_id}",
        required_args=["output_dir", "comic_id"]
    ),
    "bomtoon_dl_seq": ScriptDef(
        id="bomtoon_dl_seq",
        name="Bomtoon Download Sequence",
        path="backend/downloaders/bomtoon/bomtoontwext.py",
        command_template="python {script_path} dl-seq -o {output_dir} {comic_id} {chapter_range}",
        required_args=["output_dir", "comic_id", "chapter_range"]
    ),
    "diritto_extract_urls": ScriptDef(
        id="diritto_extract_urls",
        name="Diritto URL Extractor",
        path="backend/downloaders/diritto/diritto_url_extractor.py",
        command_template="python {script_path} --count {count}",
        required_args=[]
    ),
    "diritto_download_novels": ScriptDef(
        id="diritto_download_novels",
        name="Diritto Novel Downloader",
        path="backend/downloaders/diritto/diritto_downloader.py",
        command_template="python {script_path} --urls {urls}",
        required_args=["urls"]
    ),

    # --- File Organization ---
    "translate_org": ScriptDef(
        id="translate_org",
        name="Translate & Organize",
        path="backend/file_organization/translate_and_org_dirs.py",
        command_template="python {script_path} --target_dir {target_dir}", 
        required_args=["target_dir"]
    ),
    "organize_only": ScriptDef(
        id="organize_only",
        name="Organize Only (No Transl)",
        path="backend/file_organization/organize_only.py",
        command_template="python {script_path} --target_dir {target_dir}", 
        required_args=["target_dir"]
    ),
    "folder_codec": ScriptDef(
        id="folder_codec",
        name="Folder Encryption",
        path="backend/file_organization/folder_codec.py",
        command_template="python {script_path} --target {target_dir} --mode {mode}", 
        required_args=["target_dir", "mode"]
    ),
}

def get_script_command(script_id: str, params: Dict[str, str], project_root: str) -> List[str]:
    script = SCRIPTS.get(script_id)
    if not script:
        raise ValueError(f"Script {script_id} not found")
    
    if current_os == "windows" and "windows" not in script.platforms:
         raise ValueError(f"Script {script_id} requires {script.platforms}, but running on Windows")
    if current_os == "darwin" and "darwin" not in script.platforms:
         raise ValueError(f"Script {script_id} requires {script.platforms}, but running on Mac")

    # Resolve absolute path
    abs_script_path = os.path.join(project_root, script.path)
    # Normalize to forward slashes to avoid shlex escaping issues on Windows
    abs_script_path = abs_script_path.replace(os.sep, '/')
    
    if not os.path.exists(abs_script_path) and not os.path.exists(abs_script_path.replace('/', os.sep)):
        # Check both normalized and OS-specific path existence just in case
        raise FileNotFoundError(f"Script file not found: {abs_script_path}")
        
    # Quote parameters to handle spaces and backslashes for shlex
    quoted_params = {}
    for k, v in params.items():
        s_val = str(v)
        # Escape backslashes for shlex (posix=True consumes one level of backslashes)
        s_val_escaped = s_val.replace("\\", "\\\\")
        
        # If value has spaces, wrap in quotes
        if ' ' in s_val_escaped:
             quoted_params[k] = f'"{s_val_escaped}"'
        else:
             quoted_params[k] = s_val_escaped

    cmd_str = script.command_template.format(script_path=abs_script_path, **quoted_params)
    
    # Ensure unbuffered output for real-time logging
    if cmd_str.startswith("python "):
        cmd_str = cmd_str.replace("python ", "python -u ", 1)
    
    # Simple shell splitting
    import shlex
    # On Windows, posix=False is generally recommended for shlex if we want to preserve backslashes,
    # but since we normalized to forward slashes, posix=True (default) should be fine for the path.
    # However, other args might have backslashes and spaces.
    # posix=True is usually better for parsing quoted strings like "A B" into one arg.
    return shlex.split(cmd_str, posix=True)
