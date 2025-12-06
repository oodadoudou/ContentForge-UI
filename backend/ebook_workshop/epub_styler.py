import os
import sys
import zipfile
import shutil
import tempfile
import json

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # backend/ebook_workshop -> backend
# Wait, PROJECT_ROOT in this file is dirname(dirname(abspath)). line 13.
# So I can use that var or just be explicit.
# To match others:
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from backend.utils import get_default_work_dir

# --- 配置 ---
NEW_CSS_FILENAME = "new_style.css"
SHARED_ASSETS_DIR_NAME = "shared_assets"
OUTPUT_DIR_NAME = "processed_files"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_new_css_content(custom_css_path=None):
    """根据新的目录结构，读取shared_assets中的CSS文件内容，或者读取自定义CSS文件"""
    if custom_css_path:
        css_path = custom_css_path
    else:
        css_path = os.path.join(PROJECT_ROOT, SHARED_ASSETS_DIR_NAME, NEW_CSS_FILENAME)
    
    if not os.path.exists(css_path):
        print(f"错误: 样式文件 '{css_path}' 未找到。")
        return None
    
    with open(css_path, 'r', encoding='utf-8') as f:
        return f.read()

def modify_single_epub(epub_path, output_dir, new_css_content):
    """
    修改单个ePub文件:
    1. 解压
    2. 添加/替换 CSS 文件
    3. 更新所有 HTML 文件引入该 CSS
    4. 重新打包
    """
    filename = os.path.basename(epub_path)
    print(f"处理: {filename}")
    
    # 创建临时解压目录
    temp_dir = tempfile.mkdtemp(prefix=f"styler_{filename}_")
    
    try:
        # 1. 解压
        with zipfile.ZipFile(epub_path, 'r') as zf:
            zf.extractall(temp_dir)
            
        # 2. 确定 CSS 存放位置 (通常在 OEBPS/Styles 或 OEBPS/css，或者直接在根目录)
        # 我们尝试找一个现有的 css 目录，如果没找到就在 OEBPS 下创建，或者根目录下
        # 简单起见，我们搜索 OEBPS 目录
        oebps_dir = None
        for root, dirs, files in os.walk(temp_dir):
            if "content.opf" in files:
                oebps_dir = root
                break
        
        if not oebps_dir:
            # 如果没找到 standard structure, use root
            oebps_dir = temp_dir
            
        styles_dir = os.path.join(oebps_dir, "Styles")
        if not os.path.exists(styles_dir):
            # 尝试找 css 目录
            styles_dir = os.path.join(oebps_dir, "css")
            if not os.path.exists(styles_dir):
                # 默认创建 Styles
                styles_dir = os.path.join(oebps_dir, "Styles")
                os.makedirs(styles_dir, exist_ok=True)
                
        # 写入新 CSS 文件
        css_file_path = os.path.join(styles_dir, NEW_CSS_FILENAME)
        with open(css_file_path, 'w', encoding='utf-8') as f:
            f.write(new_css_content)
            
        # 计算 CSS 相对路径 (用于 HTML 引用)
        # 注意: HTML 可能在 OEBPS/Text, OEBPS/, 等等.
        
        # 3. 遍历所有 HTML 文件并添加/更新链接
        from bs4 import BeautifulSoup
        
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith(('.html', '.xhtml', '.htm')):
                    html_path = os.path.join(root, file)
                    
                    # 计算从 HTML 到 CSS 的相对路径
                    rel_css_path = os.path.relpath(css_file_path, root).replace("\\", "/")
                    
                    with open(html_path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f, 'html.parser')
                    
                    # 检查是否已有该 link
                    head = soup.find('head')
                    if not head:
                        # 如果没有 head, 创建一个 (针对不规范文档)
                        head = soup.new_tag('head')
                        if soup.html:
                            soup.html.insert(0, head)
                        else:
                            # 极度不规范，跳过或整个包裹
                            continue
                            
                    # 移除旧的同名 link (如果我们需要强制替换)
                    # 或者我们只追加新的?
                    # 现在的逻辑是追加/确保存在
                    
                    link_exists = False
                    for link in head.find_all('link', rel='stylesheet'):
                        if link.get('href') == rel_css_path:
                            link_exists = True
                            break
                    
                    if not link_exists:
                        new_link = soup.new_tag('link', rel='stylesheet', type='text/css', href=rel_css_path)
                        head.append(new_link)
                        
                        # 保存修改
                        with open(html_path, 'w', encoding='utf-8') as f:
                            f.write(str(soup))

        # 4. 重新打包
        output_file_path = os.path.join(output_dir, filename)
        
        # 确保 manifest (content.opf) 包含新的 CSS 文件
        # 这步比较复杂，因为需要解析 XML。
        # 如果不加到 manifest，某些阅读器可能不加载。
        # 简单起见，我们使用 epub_toolkit 的逻辑或尝试 patch content.opf
        
        # 简易版：先不改 content.opf，很多阅读器容错。
        # 但为了稳健，我们应该尝试添加。
        if oebps_dir:
            opf_path = os.path.join(oebps_dir, "content.opf")
            if os.path.exists(opf_path):
                 update_manifest(opf_path, os.path.relpath(css_file_path, oebps_dir).replace("\\", "/"))

        # Zip it up
        with zipfile.ZipFile(output_file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zf.write(file_path, arcname)
                    
        return True
        
    except Exception as e:
        print(f"处理失败 {filename}: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)

def update_manifest(opf_path, css_rel_path):
    """简单的 XML 处理以添加 item 到 manifest"""
    try:
        from xml.dom.minidom import parse
        dom = parse(opf_path)
        manifest = dom.getElementsByTagName('manifest')[0]
        
        # 检查是否已存在
        for item in manifest.getElementsByTagName('item'):
            if item.getAttribute('href') == css_rel_path:
                return # 已存在
        
        # 添加 item
        item = dom.createElement('item')
        item.setAttribute('id', 'new_style_css')
        item.setAttribute('href', css_rel_path)
        item.setAttribute('media-type', 'text/css')
        manifest.appendChild(item)
        
        with open(opf_path, 'w', encoding='utf-8') as f:
            dom.writexml(f)
    except Exception as e:
        print(f"无法更新 manifest: {e}")


def process_epub_directory(root_dir, css_file=None):
    """处理指定根目录下的所有ePub文件"""
    print("--- ePub 样式批量替换工具 ---")
    
    new_css_content = get_new_css_content(css_file)
    if new_css_content is None:
        return

    # 在目标ePub目录下创建输出文件夹
    output_path = os.path.join(root_dir, OUTPUT_DIR_NAME)
    os.makedirs(output_path, exist_ok=True)
    
    print(f"\n扫描目录: {os.path.abspath(root_dir)}")
    print(f"处理后的文件将存放在: {os.path.abspath(output_path)}")
    
    epub_files = [f for f in os.listdir(root_dir) if f.lower().endswith('.epub')]
    
    if not epub_files:
        print("\n未在指定目录中找到任何 .epub 文件。")
        return
        
    success_count = 0
    fail_count = 0
    
    for epub_file in epub_files:
        epub_full_path = os.path.join(root_dir, epub_file)
        if modify_single_epub(epub_full_path, output_path, new_css_content):
            success_count += 1
        else:
            fail_count += 1
            
    print("\n--- 处理完毕 ---")
    print(f"总计: {len(epub_files)} 个文件 | 成功: {success_count} 个 | 失败: {fail_count} 个")

# --- 新增：函数用于从 settings.json 加载默认路径 ---

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EPUB Styler")
    parser.add_argument("--input", help="Input directory containing EPUB files")
    parser.add_argument("--css", help="Path to CSS file (Optional, defaults to shared_assets/new_style.css)")
    args = parser.parse_args()

    # --- 修改：动态加载所有配置 ---
    default_path = get_default_work_dir()
    target_dir = ""

    if args.input:
        if os.path.isdir(args.input):
            target_dir = args.input
        else:
            print(f"错误: 命令行提供的路径 '{args.input}' 无效。")
            sys.exit(1)
    else:
        # 获取用户输入
        prompt_message = (
            "请输入要处理的 ePub 文件所在的目录路径\n"
            f"(直接按 Enter 键将使用默认路径: {default_path}): "
        )
        target_dir_input = input(prompt_message)

        # 如果用户未输入（或输入为空白），则使用默认路径
        target_dir = target_dir_input.strip().strip('\'"') if target_dir_input.strip() else default_path
        
        if not target_dir_input.strip():
            print(f"未输入路径，将使用默认目录: {target_dir}")

    # 检查最终确定的目录是否存在
    if not os.path.isdir(target_dir):
        print(f"\n错误: 目录 '{target_dir}' 不存在或不是一个有效的目录。")
        print("请检查路径是否正确，或者默认路径是否存在。")
        sys.exit(1)
        
    process_epub_directory(target_dir, css_file=args.css)