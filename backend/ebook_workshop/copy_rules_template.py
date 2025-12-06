import argparse
import shutil
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Copy replacement rules template to target directory")
    parser.add_argument("--input", required=True, help="Target directory to copy the template to")
    args = parser.parse_args()
    
    target_dir = Path(args.input)
    if not target_dir.is_dir():
        print(f"[!] 错误: 目标文件夹 '{target_dir}' 不存在。")
        sys.exit(1)
        
    # Locate basic resources
    # This script is in backend/ebook_workshop/
    # Shared assets is in backend/shared_assets/
    project_root = Path(__file__).resolve().parent.parent.parent
    # Actually, let's use relative path from this file
    current_dir = Path(__file__).resolve().parent
    source_file = current_dir.parent / "shared_assets" / "rules.txt"
    
    if not source_file.exists():
        print(f"[!] 错误: 模板文件未找到: {source_file}")
        sys.exit(1)
        
    destination = target_dir / "rules.txt"
    
    try:
        shutil.copy2(source_file, destination)
        print(f"[✓] 成功复制模板文件到: {destination}")
        print(f"    - 您可以在此处编辑替换规则。")
    except Exception as e:
        print(f"[!] 复制失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
