# -*- coding: utf-8 -*-

import os
import shutil
import sys
import re
from PIL import Image, ImageFile
import natsort
import traceback

# --- 全局配置 ---
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

SUCCESS_MOVE_SUBDIR_NAME = "IMG"  # 成功处理的文件夹将被移动到此目录
IMAGE_EXTENSIONS_FOR_MERGE = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tiff', '.tif')

# --- PDF页面与图像质量设置 ---
PDF_TARGET_PAGE_WIDTH_PIXELS = 1600
PDF_DPI = 300
# --- 全局配置结束 ---


def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', print_end="\r"):
    """
    在终端打印一个可视化的进度条。
    """
    if total == 0:
        percent_str = "0.0%"
        filled_length = 0
    else:
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        percent_str = f"{percent}%"
        filled_length = int(length * iteration // total)

    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent_str} {suffix}')
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')
        sys.stdout.flush()


def find_image_folders(root_dir, excluded_dirs):
    """
    递归遍历根目录，找到所有直接包含图片文件的文件夹。
    """
    print("\n--- 步骤 1: 正在扫描并查找所有包含图片的文件夹 ---")
    image_folders = []
    
    # 将排除目录的名称（非完整路径）提取出来用于比较
    excluded_basenames = [os.path.basename(d) for d in excluded_dirs]

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 如果当前目录是需要排除的目录，则跳过它和它的所有子目录
        if os.path.basename(dirpath) in excluded_basenames:
            dirnames[:] = []  # 清空dirnames可以阻止os.walk继续深入这个目录
            continue

        if any(f.lower().endswith(IMAGE_EXTENSIONS_FOR_MERGE) for f in filenames):
            image_folders.append(dirpath)
    
    sorted_folders = natsort.natsorted(image_folders)
    print(f"    🔍 已找到 {len(sorted_folders)} 个需要处理的图片文件夹。")
    return sorted_folders


def create_pdf_from_images(image_paths_list, output_pdf_path,
                           target_page_width_px, pdf_target_dpi):
    """
    从一系列图片文件路径创建一个PDF文件。
    """
    if not image_paths_list:
        print("    警告: 没有有效的图片可用于创建此PDF。")
        return None

    processed_pil_images = []
    total_images_for_pdf = len(image_paths_list)
    print_progress_bar(0, total_images_for_pdf, prefix='      转换图片:', suffix='完成', length=40)

    for i, image_path in enumerate(image_paths_list):
        try:
            with Image.open(image_path) as img:
                img_to_process = img
                if img_to_process.mode in ['RGBA', 'P']:
                    background = Image.new("RGB", img_to_process.size, (255, 255, 255))
                    background.paste(img_to_process, mask=img_to_process.split()[3] if img_to_process.mode == 'RGBA' else None)
                    img_to_process = background
                elif img_to_process.mode != 'RGB':
                    img_to_process = img_to_process.convert('RGB')

                original_width, original_height = img_to_process.size
                if original_width > target_page_width_px:
                    ratio = target_page_width_px / original_width
                    new_height = int(original_height * ratio)
                    img_resized = img_to_process.resize((target_page_width_px, new_height), Image.Resampling.LANCZOS)
                else:
                    img_resized = img_to_process.copy()

                processed_pil_images.append(img_resized)
        except Exception as e:
            sys.stdout.write(f"\r      警告: 处理图片 '{os.path.basename(image_path)}' 失败: {e}。已跳过。\n")
        finally:
            print_progress_bar(i + 1, total_images_for_pdf, prefix='      转换图片:', suffix='完成', length=40)

    if not processed_pil_images:
        print("    错误: 没有图片成功处理，无法创建PDF。")
        return None

    try:
        if len(processed_pil_images) == 1:
            processed_pil_images[0].save(
                output_pdf_path,
                resolution=float(pdf_target_dpi),
                optimize=True
            )
        else:
            first_image = processed_pil_images[0]
            other_images = processed_pil_images[1:]
            first_image.save(
                output_pdf_path,
                save_all=True,
                append_images=other_images,
                resolution=float(pdf_target_dpi),
                optimize=True
            )
        
        print(f"    ✅ 成功创建 PDF: {os.path.basename(output_pdf_path)}")
        return output_pdf_path
    except Exception as e:
        print(f"    ❌ 错误: 保存 PDF '{os.path.basename(output_pdf_path)}' 失败: {e}")
        traceback.print_exc()
        return None
    finally:
        for img_obj in processed_pil_images:
            try:
                img_obj.close()
            except Exception:
                pass


def normalize_filenames(pdf_dir):
    """
    清理并规范化PDF文件夹中所有文件的名称。
    """
    print("\n--- 步骤 3: 正在规范化PDF文件名 ---")
    try:
        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    except FileNotFoundError:
        print(f"    目录 '{pdf_dir}' 未找到，跳过文件名规范化。")
        return

    renamed_count = 0
    for filename in pdf_files:
        base, ext = os.path.splitext(filename)
        # 移除常见的分隔符和括号
        cleaned_base = re.sub(r'[\s()\[\]【】。.]', '', base)
        
        normalized_name = cleaned_base + ext
        
        if normalized_name != filename:
            original_path = os.path.join(pdf_dir, filename)
            new_path = os.path.join(pdf_dir, normalized_name)
            try:
                os.rename(original_path, new_path)
                print(f"    重命名: '{filename}' -> '{normalized_name}'")
                renamed_count += 1
            except OSError as e:
                print(f"    ❌ 错误: 重命名 '{filename}' 失败: {e}")
                
def run_conversion_process(root_input_dir):
    """
    运行整个批量转换流程。
    """
    # 1. 扫描文件夹
    # 排除输出目录，避免递归扫描
    excluded_dirs = ["processed_dir", SUCCESS_MOVE_SUBDIR_NAME]
    sorted_image_folders = find_image_folders(root_input_dir, excluded_dirs)
    
    total_folders = len(sorted_image_folders)
    if total_folders == 0:
        print("\n没有找到需要处理的图片文件夹。结束。")
        return

    # 2. 准备输出目录
    overall_pdf_output_dir = os.path.join(root_input_dir, "processed_dir")
    if not os.path.exists(overall_pdf_output_dir):
        os.makedirs(overall_pdf_output_dir)
        print(f"\n--- 步骤 2: 创建 PDF 输出总目录: {overall_pdf_output_dir} ---")
    else:
        print(f"\n--- 步骤 2: PDF 输出总目录已存在: {overall_pdf_output_dir} ---")

    success_move_target_dir = os.path.join(root_input_dir, SUCCESS_MOVE_SUBDIR_NAME)
    if not os.path.exists(success_move_target_dir):
        os.makedirs(success_move_target_dir)

    success_count = 0
    failed_tasks = []

    # 3. 开始循环处理
    print(f"\n--- 步骤 3: 开始批量处理 {total_folders} 个文件夹 ---")
    
    for i, image_dir_path in enumerate(sorted_image_folders):
        folder_name = os.path.basename(image_dir_path)
        print(f"\n--- ({i+1}/{total_folders}) 正在处理: {folder_name} ---")

        # 3.1 规范化文件名
        normalize_filenames(image_dir_path)

        # 3.2 读取图片列表
        try:
            image_filenames = [f for f in os.listdir(image_dir_path)
                               if f.lower().endswith(IMAGE_EXTENSIONS_FOR_MERGE) and not f.startswith('.')]
        except Exception as e:
            print(f"  ❌ 错误: 无法读取文件夹 '{folder_name}' 的内容: {e}")
            failed_tasks.append(folder_name)
            continue
            
        if not image_filenames:
            print("    文件夹内未找到符合条件的图片，已跳过。")
            continue

        # 3.3 生成PDF
        sorted_image_paths = [os.path.join(image_dir_path, f) for f in natsort.natsorted(image_filenames)]
        output_pdf_filename = f"{folder_name}.pdf"
        output_pdf_filepath = os.path.join(overall_pdf_output_dir, output_pdf_filename)

        result_path = create_pdf_from_images(
            sorted_image_paths, output_pdf_filepath,
            PDF_TARGET_PAGE_WIDTH_PIXELS, PDF_DPI
        )
        
        # 3.4 处理结果
        if result_path:
            success_count += 1
            # 移动已成功处理的文件夹
            print(f"    移动已成功处理的文件夹: {folder_name}")
            try:
                # 确保目标文件夹存在
                if os.path.basename(image_dir_path) == os.path.basename(success_move_target_dir):
                    print(f"      -> 跳过移动，源与目标文件夹同名。")
                else:
                    target_move_path = os.path.join(success_move_target_dir, folder_name)
                    # 如果目标已存在，先移除（或者可以改为重命名，这里选择覆盖/合并的逻辑需谨慎，简单起见如果存在则报错或覆盖）
                    # shutil.move 如果目标是已存在目录，会移动到该目录内部，所以最好确保目标路径不存在
                    if os.path.exists(target_move_path):
                        print(f"      警告: 目标位置已存在同名文件夹 '{folder_name}'，将尝试覆盖或合并。")
                        # shutil.move 在这种情况下比较复杂，简单策略: 
                        # 这里我们假设用户已经处理过，或者手动清理。
                        # 为安全起见，我们加个后缀
                        import time
                        target_move_path += f"_{int(time.time())}"
                    
                    shutil.move(image_dir_path, target_move_path)
                    print(f"      -> 已移至 '{SUCCESS_MOVE_SUBDIR_NAME}' 文件夹。")
            except Exception as e:
                print(f"      ❌ 错误: 移动文件夹失败: {e}")
                if folder_name not in failed_tasks:
                    failed_tasks.append(f"{folder_name} (移动失败)")
                success_count -= 1
        else:
            failed_tasks.append(folder_name)

    # 4. 总结
    print("\n" + "=" * 70)
    print("【任务总结报告】")
    print("-" * 70)
    print(f"总计查找项目 (文件夹): {total_folders} 个")
    print(f"  - ✅ 成功处理: {success_count} 个")
    print(f"  - ❌ 失败: {len(failed_tasks)} 个")
    
    if failed_tasks:
        print("\n失败的项目列表:")
        for task in failed_tasks:
            print(f"  - {task}")
    
    print("-" * 70)
    print(f"所有成功生成的PDF文件已保存在: {overall_pdf_output_dir}")
    print(f"所有成功处理的原始文件夹已移至: {success_move_target_dir}")


if __name__ == "__main__":
    import argparse
    
    print("=" * 70)
    print("=== 批量图片文件夹转PDF脚本 (V2 - 支持成功后移动) ===")
    print("=" * 70)
    
    parser = argparse.ArgumentParser(description="图片转PDF工具")
    parser.add_argument("--input", help="输入根目录路径")
    parser.add_argument("--output", help="输出根目录路径 (可选)")
    args = parser.parse_args()

    root_input_dir = ""
    default_root_dir_name = ""

    # 尝试从共享设置加载默认路径
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # 尝试导入，可能需要根据实际路径结构调整
        try:
             from shared_utils import utils
             settings = utils.load_settings()
             default_root_dir_name = settings.get("default_work_dir", "")
        except ImportError:
             pass # 忽略导入错误
    except (ImportError, FileNotFoundError):
        pass

    if not default_root_dir_name:
         default_root_dir_name = os.path.join(os.path.expanduser("~"), "Downloads")
    
    if args.input:
        if os.path.isdir(args.input):
            root_input_dir = os.path.abspath(args.input)
            print(f"[*] 使用命令行提供的目录: {root_input_dir}")
        else:
            print(f"错误: 命令行提供的路径 '{args.input}' 无效。")
            sys.exit(1)
    else:
        while True:
            prompt_message = (
                f"请输入包含多个图片子文件夹的【根目录】路径。\n"
                f"(直接按 Enter 键将使用默认路径: '{default_root_dir_name}'): "
            )
            user_provided_path = input(prompt_message).strip()
            
            current_path_to_check = user_provided_path if user_provided_path else default_root_dir_name
            if not user_provided_path:
                print(f"\n使用默认路径: {current_path_to_check}")

            abs_path_to_check = os.path.abspath(current_path_to_check)
            if os.path.isdir(abs_path_to_check):
                root_input_dir = abs_path_to_check
                print(f"已确认根处理目录: {root_input_dir}")
                break
            else:
                print(f"\n错误：路径 '{abs_path_to_check}' 不是一个有效的目录或不存在。请重试。\n")
    
    try:
        run_conversion_process(root_input_dir)
    except Exception as e:
        print("\n" + "!"*70)
        print("脚本在执行过程中遇到意外的严重错误，已终止。")
        print(f"错误详情: {e}")
        traceback.print_exc()
        print("!"*70)

    print("\n脚本执行完毕。")