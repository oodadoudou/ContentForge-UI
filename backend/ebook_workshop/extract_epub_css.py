import os
import zipfile
import sys
import json

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from backend.utils import get_default_work_dir

def extract_css_from_epubs(base_dir):
    """
    遍历指定的基础目录，查找所有子目录中的 .epub 文件，
    并将其中的 .css 文件提取到 .epub 文件所在的目录。

    :param base_dir: 用户指定的要搜索的基础目录路径。
    """
    if not os.path.isdir(base_dir):
        print(f"错误: 目录 '{base_dir}' 不存在或不是一个有效的目录。", file=sys.stderr)
        sys.exit(1)

    print(f"[*] 开始扫描目录: {os.path.abspath(base_dir)}")
    
    for root, dirs, files in os.walk(base_dir):
        for filename in files:
            if filename.endswith('.epub'):
                epub_path = os.path.join(root, filename)
                print(f"\n[+] 找到 EPUB 文件: {epub_path}")

                try:
                    with zipfile.ZipFile(epub_path, 'r') as zf:
                        all_zip_files = zf.namelist()
                        
                        css_files_in_zip = [f for f in all_zip_files if f.endswith('.css')]

                        if not css_files_in_zip:
                            print(f"  -> 在 '{filename}' 中未找到 CSS 文件。")
                            continue

                        print(f"  -> 发现 {len(css_files_in_zip)} 个 CSS 文件，准备提取...")

                        # Output to processed_files
                        output_dir = os.path.join(root, "processed_files")
                        os.makedirs(output_dir, exist_ok=True)

                        for css_file_path in css_files_in_zip:
                            zf.extract(css_file_path, path=output_dir)
                            extracted_filename = os.path.basename(css_file_path)
                            print(f"    - 已提取 '{extracted_filename}' 到 '{output_dir}'")

                except zipfile.BadZipFile:
                    print(f"  [!] 警告: 无法打开 '{filename}'。文件可能已损坏或不是有效的 EPUB/ZIP 文件。")
                except Exception as e:
                    print(f"  [!] 错误: 处理 '{filename}' 时发生未知错误: {e}")

    print("\n[*] 所有操作完成。")


import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract CSS from EPUB files.")
    parser.add_argument("--input", "-i", type=str, help="Directory containing EPUB files")
    
    args = parser.parse_args()
    
    target_directory = None
    
    if args.input:
        target_directory = args.input
    else:
        default_path = get_default_work_dir()
        prompt_message = f"请输入目标目录路径 (直接按回车将使用默认路径: {default_path}): "
        try:
            user_input = input(prompt_message)
            target_directory = user_input.strip() if user_input.strip() else default_path
        except EOFError:
            pass
            
    if not target_directory:
        print("[!] 错误: 未提供输入目录。")
        sys.exit(1)
        
    extract_css_from_epubs(target_directory)