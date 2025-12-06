import os
import re
import pikepdf
import natsort
import logging
import json  # 新增: 用于解析JSON

# --- 配置 ---
# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 定义合并后PDF存放的子目录名称
MERGED_PDF_SUBDIR_NAME = "merged_pdf"

# 删除了旧的硬编码 DEFAULT_INPUT_DIR

def natural_sort_key(s: str) -> list:
    """
    为文件名生成自然排序的键。
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]


def merge_pdfs_in_directory(root_dir: str):
    """
    合并指定目录结构下的PDF文件。
    """
    # 创建 merged_pdf 输出目录
    output_dir = os.path.join(root_dir, MERGED_PDF_SUBDIR_NAME)
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"输出目录 '{output_dir}' 已准备就绪。")

    subfolders = [d.path for d in os.scandir(root_dir) if d.is_dir() and d.name != MERGED_PDF_SUBDIR_NAME]

    if not subfolders:
        logging.warning(f"在根目录 '{root_dir}' 下没有找到需要处理的子文件夹。")
        return

    print(f"\n--- 发现 {len(subfolders)} 个子文件夹,准备开始合并 ---")

    for subfolder_path in natsort.natsorted(subfolders):
        subfolder_name = os.path.basename(subfolder_path)
        logging.info(f"===== 开始处理子文件夹: {subfolder_name} =====")

        pdf_files_to_merge = []
        logging.info(f"正在 '{subfolder_name}' 及其所有子目录中搜索PDF文件...")
        for dirpath, _, filenames in os.walk(subfolder_path):
            for filename in filenames:
                if filename.lower().endswith('.pdf'):
                    pdf_path = os.path.join(dirpath, filename)
                    pdf_files_to_merge.append(pdf_path)
                    logging.info(f"  [找到文件] {os.path.relpath(pdf_path, subfolder_path)}")

        pdf_files_to_merge = natsort.natsorted(pdf_files_to_merge)
        if not pdf_files_to_merge:
            logging.info("  [提示] 此文件夹中未找到PDF文件,跳过。")
            continue

        output_pdf_name = f"{subfolder_name}.pdf"
        output_pdf_path = os.path.join(output_dir, output_pdf_name)
        logging.info(f"  [准备合并] 将合并 {len(pdf_files_to_merge)} 个文件 -> {output_pdf_name}")

        try:
            pdf = pikepdf.Pdf.new()
            for file_path in pdf_files_to_merge:
                try:
                    src_pdf = pikepdf.Pdf.open(file_path)
                    pdf.pages.extend(src_pdf.pages)
                except Exception as e:
                    logging.error(f"    [错误] 无法读取文件 '{file_path}': {e}")
            
            pdf.save(output_pdf_path)
            logging.info(f"  [完成] 成功保存: {output_pdf_path}")
        except Exception as e:
            logging.error(f"  [失败] 合并过程出错: {e}")

def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="PDF 合并工具")
    parser.add_argument("--input", help="输入根目录路径")
    parser.add_argument("--output", help="输出文件路径 (未使用，仅兼容接口)")
    args = parser.parse_args()

    print("\n--- PDF 合并工具 ---")
    print("本工具将自动查找每个子文件夹(及其所有后代目录)中的PDF文件,")
    print("并将它们合并成一个以该子文件夹命名的PDF文件。")

    # --- 新增：与 pipeline 脚本一致的动态路径读取函数 ---
    def load_default_path_from_settings():
        """从共享设定档中读取预设工作目录。"""
        try:
            # 假设此脚本位于项目子目录，向上两层找到项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            settings_path = os.path.join(project_root, 'shared_assets', 'settings.json')
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            # 如果 default_work_dir 为空或 None，也视为无效
            default_dir = settings.get("default_work_dir")
            return default_dir if default_dir else "."
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            # 仅在交互模式下打印警告，避免污染日志
            if not args.input:
                print(f"警告：读取 settings.json 失败 ({e})，将使用内建备用路径。")
            # 在无法读取设定档时，提供一个通用的备用路径
            return os.path.join(os.path.expanduser("~"), "Downloads")
    # --- 新增结束 ---

    root_dir = ""

    # 1. 优先使用命令行参数
    if args.input:
        if os.path.isdir(args.input):
            root_dir = os.path.abspath(args.input)
            print(f"[*] 使用命令行提供的目录: {root_dir}")
        else:
            print(f"错误: 命令行提供的路径 '{args.input}' 无效。")
            sys.exit(1)
    else:
        # 2. 交互式回退
        default_root_dir_name = load_default_path_from_settings()

        # --- 标准化的路径处理逻辑 ---
        while True:
            prompt_message = (
                f"\n- 请输入目标根文件夹的路径。\n"
                f"  (直接按 Enter 将使用默认路径: '{default_root_dir_name}'): "
            )
            user_input = input(prompt_message).strip()

            # 如果用户未输入内容，则使用默认路径，否则使用用户输入的路径
            root_dir_to_check = user_input if user_input else default_root_dir_name
            
            abs_path_to_check = os.path.abspath(root_dir_to_check)

            if os.path.isdir(abs_path_to_check):
                root_dir = abs_path_to_check
                print(f"\n[*] 将要处理的目录是: {root_dir}")
                break
            else:
                print(f"错误：路径 '{abs_path_to_check}' 不是一个有效的目录或不存在。")
        # --------------------------

    print(f"\n--- 开始处理, 根目录: {root_dir} ---")
    merge_pdfs_in_directory(root_dir)
    print("\n--- 所有操作完成 ---")

if __name__ == "__main__":
    main()