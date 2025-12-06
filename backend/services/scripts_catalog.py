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
     "long_pdf_split": ScriptDef(
        id="long_pdf_split",
        name="Long PDF Splitter",
        path="backend/comic_processing/convert_long_pdf.py",
        command_template="echo {input_dir} | python {script_path}", 
        required_args=["input_dir"]
    ),
    "ai_pipeline_v5": ScriptDef(
        id="ai_pipeline_v5",
        name="AI Pipeline V5",
        path="backend/comic_processing/image_processes_pipeline_v5.py",
        command_template="echo {input_dir} | python {script_path}",
        required_args=["input_dir"]
    ),

    # --- Ebook Workshop ---
    "txt_to_epub": ScriptDef(
        id="txt_to_epub",
        name="TXT to EPUB",
        path="backend/ebook_workshop/txt_to_epub_convertor.py",
        command_template="python {script_path} --input {input_file}", 
        required_args=["input_file"]
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
        command_template="python {script_path} --input {input_file} --output {output_dir}",
        required_args=["input_file", "output_dir"]
    ),
    "epub_cleaner": ScriptDef(
        id="epub_cleaner",
        name="EPUB Cleaner",
        path="backend/ebook_workshop/epub_cleaner.py",
        command_template="python {script_path} --input {input_file}",
        required_args=["input_file"]
    ),
    "epub_rename": ScriptDef(
        id="epub_rename",
        name="EPUB Rename",
        path="backend/ebook_workshop/epub_rename.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),
    "fix_txt_encoding": ScriptDef(
        id="fix_txt_encoding",
        name="Fix TXT Encoding",
        path="backend/ebook_workshop/fix_txt_encoding.py",
        command_template="python {script_path} --input {input_file}",
        required_args=["input_file"]
    ),
    "cover_repair": ScriptDef(
        id="cover_repair",
        name="Cover Repair",
        path="backend/ebook_workshop/cover_repair.py",
        command_template="python {script_path} --input {input_file}",
        required_args=["input_file"]
    ),
     "punctuation_fixer": ScriptDef(
        id="punctuation_fixer",
        name="Punctuation Fixer",
        path="backend/ebook_workshop/punctuation_fixer_v2.py",
        command_template="python {script_path} --input {input_file}",
        required_args=["input_file"]
    ),
     "batch_replacer": ScriptDef(
        id="batch_replacer",
        name="Batch Replacer",
        path="backend/ebook_workshop/batch_replacer_v2.py",
        command_template="python {script_path} --input {input_dir}",
        required_args=["input_dir"]
    ),

    # --- Downloaders ---
    "bomtoon_login": ScriptDef(
        id="bomtoon_login",
        name="Bomtoon Login (Mac)",
        path="backend/downloaders/bomtoon/update_token.py",
        command_template="python {script_path}",
        platforms=["darwin"]
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
     "diritto_dl": ScriptDef(
        id="diritto_dl",
        name="Diritto Download",
        path="backend/downloaders/diritto/diritto_downloader.py",
        command_template="python {script_path}", 
        required_args=[]
    ),

    # --- File Organization ---
    "translate_org": ScriptDef(
        id="translate_org",
        name="Translate & Organize",
        path="backend/file_organization/translate_and_org_dirs.py",
        command_template="echo {target_dir} | python {script_path}", 
        required_args=["target_dir"]
    ),
    "organize_only": ScriptDef(
        id="organize_only",
        name="Organize Only (No Transl)",
        path="backend/file_organization/organize_only.py",
        command_template="echo {target_dir} | python {script_path}", 
        required_args=["target_dir"]
    ),
    "folder_codec": ScriptDef(
        id="folder_codec",
        name="Folder Encryption",
        path="backend/file_organization/folder_codec.py",
        command_template="python {script_path} --target {target_dir} --password {password}", 
        required_args=["target_dir", "password"]
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
    if not os.path.exists(abs_script_path):
        raise FileNotFoundError(f"Script file not found: {abs_script_path}")
        
    cmd_str = script.command_template.format(script_path=abs_script_path, **params)
    
    # Simple shell splitting
    import shlex
    return shlex.split(cmd_str)
