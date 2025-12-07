import pandas as pd
import re
import os
import warnings
import tempfile
import zipfile
import shutil
from pathlib import Path
from ebooklib import epub, ITEM_DOCUMENT, ITEM_STYLE
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from tqdm import tqdm
import html
import sys
import json
import css_fixer

# --- 解决 Windows 控制台编码问题 (Fix Encoding Issues) ---
# 强制将标准输出和错误输出设置为 UTF-8，以支持中文、韩文等字符
# 防止在 GBK 环境下打印特殊字符时出现 UnicodeEncodeError
if sys.platform.startswith('win'):
    if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    if sys.stderr is not None and hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from backend.utils import get_default_work_dir

# --- 屏蔽已知警告 ---
warnings.filterwarnings("ignore", category=UserWarning, module='ebooklib')
warnings.filterwarnings("ignore", category=FutureWarning, module='ebooklib')
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# --- 常量定义 ---
PROCESSED_DIR_NAME = "processed_files"
REPORT_DIR_NAME = "compare_reference"
HIGHLIGHT_STYLE = "background-color: #f1c40f; color: #000; padding: 2px; border-radius: 3px;"

def read_content_auto(file_path_or_bytes) -> str:
    """尝试多种编码读取内容 (UTF-8, UTF-8-SIG, CP949, GBK, etc)"""
    encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'gb18030', 'gbk', 'shift_jis', 'latin1']
    
    if isinstance(file_path_or_bytes, (str, Path)):
        try:
            with open(file_path_or_bytes, 'rb') as f:
                raw_data = f.read()
        except Exception as e:
            print(f"[!] 读取文件失败 {file_path_or_bytes}: {e}")
            return ""
    else:
        raw_data = file_path_or_bytes

    for enc in encodings:
        try:
            return raw_data.decode(enc)
        except UnicodeDecodeError:
            continue
            
    # Fallback
    print(f"[!] 警告: 无法自动识别编码，将使用 utf-8 (errors='replace') 进行解码。")
    return raw_data.decode('utf-8', errors='replace')


def find_rules_file(directory: Path) -> Path:
    """在指定目录中查找规则文件。仅支持: rules.txt, rule.txt, 规则.txt (以及常见的 .txt.txt 错误命名)"""
    candidates = [
        'rules.txt', 'rule.txt', '规则.txt',
        'rules.txt.txt', 'rule.txt.txt', '规则.txt.txt'
    ]
    
    for candidate in candidates:
        f_path = directory / candidate
        if f_path.exists():
            return f_path
            
    for candidate in candidates:
        found = list(directory.glob(candidate)) 
        if found:
            return found[0]
            
    return None

def load_rules(rules_file: Path) -> pd.DataFrame:
    """加载替换规则, 支持标准格式及 Moon Reader (#->#) 格式。"""
    print(f"[*] 正在从 {rules_file.name} 加载替换规则...")
    rules_list = []
    lines_to_write = []
    file_needs_update = False

    try:
        # 1. Read all lines with auto encoding
        content = read_content_auto(rules_file)
        raw_lines = content.splitlines(keepends=True)

        # 2. Process lines
        for i, line in enumerate(raw_lines, 1):
            original_line = line
            line = line.strip()
            
            if not line or line.startswith('#'):
                lines_to_write.append(original_line)
                continue

            # Check for Moon Reader format: "Old#->#New"
            moon_reader_match = re.match(r'^(.*?)#->#(.*?)$', line)
            
            # Check for Standard format: "Old -> New (Mode: Text/Regex)" or just "Old -> New"
            standard_match = re.match(r'^(.*?)\s*->\s*(.*?)(?:\s*\(Mode:\s*(Text|Regex)\s*\))?$', line, re.IGNORECASE)
            
            # Check for Legacy format without replacement: "Old -> (Mode: Text)"
            legacy_no_repl_match = re.match(r'^(.*?)\s*->\s*\(Mode:\s*(Text|Regex)\s*\)$', line, re.IGNORECASE)

            if moon_reader_match:
                # Convert Moon Reader to Standard (Mode: Text)
                original, replacement = moon_reader_match.groups()
                mode = "Text"
                file_needs_update = True
                
                # Create standard formatted string
                new_line_str = f"{original} -> {replacement} (Mode: {mode})\n"
                lines_to_write.append(new_line_str)
                
                rules_list.append({
                    'Original': original,
                    'Replacement': replacement,
                    'Mode': mode
                })

            elif standard_match:
                original, replacement, mode_group = standard_match.groups()
                mode = mode_group if mode_group else "Text"
                
                # If mode was missing, we might want to standardize the file, but for now just load it.
                # Use strict check to see if we should update file:
                if not mode_group:
                     # It matched leniently, let's update file to standard format
                     file_needs_update = True
                     new_line_str = f"{original.strip()} -> {replacement.strip()} (Mode: {mode.capitalize()})\n"
                     lines_to_write.append(new_line_str)
                else:
                     lines_to_write.append(original_line)

                rules_list.append({
                    'Original': original.strip(),
                    'Replacement': replacement.strip(),
                    'Mode': mode.strip().capitalize()
                })

            elif legacy_no_repl_match:
                original, mode = legacy_no_repl_match.groups()
                lines_to_write.append(original_line)
                rules_list.append({
                    'Original': original.strip(),
                    'Replacement': "",
                    'Mode': mode.strip().capitalize()
                })

            else:
                print(f"[!] 警告: 第 {i} 行规则格式不正确，已忽略: \"{line}\"")
                lines_to_write.append(original_line)
                continue

        # 3. Overwrite file if needed
        if file_needs_update:
            try:
                with open(rules_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines_to_write)
                print(f"[*] 已将 {rules_file.name} 转换为标准模板格式。")
            except Exception as e:
                print(f"[!] 警告: 无法更新规则文件格式: {e}")

        df = pd.DataFrame(rules_list)
        
        if df.empty:
            print("[!] 警告: 规则文件为空或所有规则均无效。")
        
        return df

    except Exception as e:
        print(f"[!] 加载规则文件失败: {e}")
        # Return empty DF or exit? Original code exits.
        sys.exit(1)

def process_and_get_changes(content: str, rules: pd.DataFrame) -> tuple[str, list]:
    """
    核心处理函数：对传入的纯文本进行所有替换。
    返回元组: (修改后的文本, 原子化变更列表)
    原子化变更: [{'original_text': '...','replacement_text': '...'}]
    """
    modified_content = content
    atomic_changes = []

    for _, rule in rules.iterrows():
        original, replacement, mode = rule['Original'], rule['Replacement'], rule['Mode']
        if pd.isna(original) or original == "" or original == "nan":
            continue
        
        search_pattern = re.escape(original) if mode.lower() == 'text' else original
        
        try:
            # 必须在最新版本的字符串上查找，以处理链式替换
            matches = list(re.finditer(search_pattern, modified_content))
            if matches:
                # 记录下每次匹配到的原文和它将被替换成的新文本
                for match in matches:
                    original_text = match.group(0)
                    replacement_text = match.expand(replacement)
                    if original_text != replacement_text:
                        atomic_changes.append({
                            "original_text": original_text,
                            "replacement_text": replacement_text
                        })
                # 应用本条规则的替换
                modified_content = re.sub(search_pattern, replacement, modified_content)
        except re.error as e:
            print(f"\n[!] 正则表达式错误: '{search_pattern}'. 错误: {e}. 跳过。")
            continue

    unique_atomic_changes = [dict(t) for t in {tuple(d.items()) for d in atomic_changes}]
    return modified_content, unique_atomic_changes

def generate_report(report_path: Path, changes_log: list, source_filename: str):
    """生成HTML格式的变更报告。"""
    if not changes_log:
        print(f"[!] 没有变更记录，跳过报告生成: {report_path}")
        return
    
    # 获取项目根目录和模板路径
    project_root = Path(__file__).parent.parent
    template_path = project_root / 'shared_assets' / 'report_template.html'
    
    if not template_path.exists():
        print(f"[!] 模板文件不存在: {template_path}")
        return
    
    # 获取CSS和JS内容
    shared_assets_dir = project_root / 'shared_assets'
    css_file_path = shared_assets_dir / 'report_styles.css'
    js_file_path = shared_assets_dir / 'report_scripts.js'
    
    css_content = ""
    try:
        css_content = css_file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"[!] 读取CSS文件失败: {e}")
        css_content = "/* CSS load failed */"

    js_content = ""
    try:
        js_content = js_file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"[!] 读取JS文件失败: {e}")
        js_content = "// JS load failed"
    
    # ... (rule groups logic unchanged) ...
    # 按替换规则归类
    rule_groups = {}
    for change in changes_log:
        # 提取高亮的原文和替换文本
        original_match = re.search(r'<span class="highlight">([^<]+)</span>', change['original'])
        modified_match = re.search(r'<span class="highlight">([^<]+)</span>', change['modified'])
        
        if original_match and modified_match:
            original_text = original_match.group(1)
            replacement_text = modified_match.group(1)
            rule_key = f"{original_text} → {replacement_text}"
            
            if rule_key not in rule_groups:
                rule_groups[rule_key] = {
                    'original_text': original_text,
                    'replacement_text': replacement_text,
                    'instances': []
                }
            
            rule_groups[rule_key]['instances'].append(change)
    
    # 按实例数量排序
    sorted_rule_groups = sorted(rule_groups.values(), key=lambda x: len(x['instances']), reverse=True)
    total_instances = sum(len(group['instances']) for group in sorted_rule_groups)
    
    # 读取模板文件
    template_content = template_path.read_text(encoding='utf-8')
    
    # 生成规则列表项
    rules_list_items = ""
    for i, group in enumerate(sorted_rule_groups):
        rules_list_items += f'''
                    <div class="rule-list-item" onclick="jumpToRule({i})">
                        <div class="rule-text">
                            <span class="rule-original">{html.escape(group["original_text"])}</span> → 
                            <span class="rule-replacement">{html.escape(group["replacement_text"])}</span>
                        </div>
                        <div class="rule-count">{len(group["instances"])} 次</div>
                    </div>
        '''
    
    # 生成内容区域
    content_sections = ""
    for group_index, group in enumerate(sorted_rule_groups):
        instance_count = len(group['instances'])
        content_sections += f'''
            <div class="rule-group" data-group-index="{group_index}">
                <div class="rule-header" onclick="toggleInstances({group_index})">
                    <div class="rule-title">
                        <span class="rule-badge">{instance_count} 次</span>
                        <span class="toggle-icon" id="toggle-{group_index}">▼</span>
                    </div>
                    <div class="rule-description">
                        <span><strong>{html.escape(group['original_text'])}</strong></span>
                        <span class="rule-arrow">→</span>
                        <span><strong>{html.escape(group['replacement_text'])}</strong></span>
                    </div>
                </div>
                <div class="instances-container" id="instances-{group_index}">
        '''
        
        # 按位置排序实例
        sorted_instances = sorted(group['instances'], key=lambda x: x.get('position', 0))
        
        for instance in sorted_instances:
            content_sections += f'''
                    <div class="instance-item">
                        <div class="instance-content">
                            <div class="original-section">
                                <div class="section-title">原文</div>
                                <div class="text-content">{instance['original']}</div>
                            </div>
                            <div class="modified-section">
                                <div class="section-title">修改后</div>
                                <div class="text-content">{instance['modified']}</div>
                            </div>
                        </div>
                    </div>
            '''
        
        content_sections += '''
                </div>
            </div>
        '''
    
    # 替换模板中的占位符
    html_content = template_content.replace('{{source_filename}}', html.escape(source_filename))
    html_content = html_content.replace('{{rules_count}}', str(len(sorted_rule_groups)))
    html_content = html_content.replace('{{total_instances}}', str(total_instances))
    html_content = html_content.replace('{{rules_list_items}}', rules_list_items)
    html_content = html_content.replace('{{content_sections}}', content_sections)
    html_content = html_content.replace('{{generation_time}}', html.escape(str(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
    
    # 嵌入CSS和JS（替换标签）
    html_content = html_content.replace('<link rel="stylesheet" href="shared_assets/report_styles.css">', f'<style>\n{css_content}\n</style>')
    html_content = html_content.replace('<script src="shared_assets/report_scripts.js"></script>', f'<script>\n{js_content}\n</script>')
    
    try:
        report_path.write_text(html_content, encoding='utf-8')
        print(f"[✓] 报告已生成: {report_path}")
    except Exception as e:
        print(f"[!] 无法写入报告文件 {report_path}: {e}")

def process_txt_file(file_path: Path, rules: pd.DataFrame, processed_dir: Path, report_dir: Path):
    """处理单个 .txt 文件。"""
    replacement_count = 0
    try:
        content = read_content_auto(file_path)
        paragraphs = content.split('\n\n')
        processed_paragraphs = []
        changes_log_for_report = []
        file_was_modified = False
        current_position = 0

        for paragraph_index, p_original in enumerate(paragraphs):
            p_modified, atomic_changes = process_and_get_changes(p_original, rules)
            processed_paragraphs.append(p_modified)

            if atomic_changes:
                file_was_modified = True
                replacement_count += len(atomic_changes)
                original_report = html.escape(p_original)
                modified_report = html.escape(p_modified)

                for change in atomic_changes:
                    orig_esc = html.escape(change["original_text"])
                    repl_esc = html.escape(change["replacement_text"])
                    original_report = original_report.replace(orig_esc, f'<span class="highlight">{orig_esc}</span>')
                    modified_report = modified_report.replace(repl_esc, f'<span class="highlight">{repl_esc}</span>')
                
                changes_log_for_report.append({
                    'original': original_report.replace('\n', '<br>'),
                    'modified': modified_report.replace('\n', '<br>'),
                    'position': current_position + paragraph_index
                })
            
            current_position += len(p_original) + 2

        if file_was_modified:
            new_content = "\n\n".join(processed_paragraphs)
            processed_file_path = processed_dir / file_path.name
            processed_file_path.write_text(new_content, encoding='utf-8')
            report_path = report_dir / f"{file_path.name}.html"
            generate_report(report_path, changes_log_for_report, file_path.name)
            return {'modified': True, 'replacement_count': replacement_count, 'css_fixed': False, 'error': None}

    except Exception as e:
        print(f"\n[!] 处理TXT文件失败 {file_path.name}: {e}")
        return {'modified': False, 'replacement_count': 0, 'css_fixed': False, 'error': str(e)}
    return {'modified': False, 'replacement_count': 0, 'css_fixed': False, 'error': None}

def process_epub_file(file_path: Path, rules: pd.DataFrame, processed_dir: Path, report_dir: Path):
    """处理EPUB文件，采用两阶段处理：1.文本替换 2.CSS链接修复"""
    
    changes_log = []
    book_is_modified = False
    global_position = 0
    replacement_count = 0
    
    try:
        # 第一阶段：使用BeautifulSoup进行文本替换
        book = epub.read_epub(str(file_path))
        
        for item in book.get_items():
            if item.get_type() == ITEM_DOCUMENT:
                content = read_content_auto(item.get_content())
                soup = BeautifulSoup(content, 'xml')
                item_is_modified = False
                
                if not soup.body:
                    continue
                
                for p_tag in soup.body.find_all('p'):
                    if not p_tag.get_text(strip=True):
                        continue

                    p_text_original = p_tag.get_text()
                    p_text_modified, atomic_changes = process_and_get_changes(p_text_original, rules)

                    if atomic_changes:
                        book_is_modified = True
                        item_is_modified = True
                        replacement_count += len(atomic_changes)
                        
                        p_tag.string = p_text_modified

                        original_report = html.escape(p_text_original)
                        modified_report = html.escape(p_text_modified)

                        for change in atomic_changes:
                            orig_esc = html.escape(change["original_text"])
                            repl_esc = html.escape(change["replacement_text"])
                            original_report = original_report.replace(orig_esc, f'<span class="highlight">{orig_esc}</span>')
                            modified_report = modified_report.replace(repl_esc, f'<span class="highlight">{repl_esc}</span>')
                        
                        changes_log.append({
                            'original': original_report.replace('\n', '<br>'),
                            'modified': modified_report.replace('\n', '<br>'),
                            'position': global_position
                        })
                    
                    global_position += len(p_text_original)

                # 如果文件被修改，更新item内容
                if item_is_modified:
                    item.set_content(str(soup).encode('utf-8'))

        # 保存第一阶段修复后的EPUB文件
        temp_epub_path = processed_dir / f"temp_{file_path.name}"
        if book_is_modified:
            # 检查并确保EPUB有必需的identifier元数据
            if not book.get_metadata('DC', 'identifier'):
                # 如果没有identifier，添加一个默认的
                import uuid
                default_identifier = f"urn:uuid:{uuid.uuid4()}"
                book.add_metadata('DC', 'identifier', default_identifier)
            
            epub.write_epub(str(temp_epub_path), book, {})
        else:
            # 如果没有修改，复制原文件作为临时文件
            shutil.copy2(file_path, temp_epub_path)
        
        # 第二阶段：修复CSS链接 (使用 css_fixer 模块)
        fix_status, _ = css_fixer.fix_epub_css(str(temp_epub_path), str(temp_epub_path.parent))
        css_fixed = (fix_status == "fixed")
        
        if css_fixed:
            book_is_modified = True
        
        # 将最终文件移动到目标位置
        final_epub_path = processed_dir / file_path.name
        if temp_epub_path.exists():
            shutil.move(str(temp_epub_path), str(final_epub_path))
        
        # 生成报告
        if book_is_modified and changes_log:
            unique_changes = [dict(t) for t in {tuple(d.items()) for d in changes_log}]
            report_path = report_dir / f"{file_path.name}.html"
            generate_report(report_path, unique_changes, file_path.name)
        
        return {'modified': book_is_modified, 'replacement_count': replacement_count, 'css_fixed': css_fixed, 'error': None}
        
    except Exception as e:
        print(f"\n[!] 处理EPUB文件失败 {file_path.name}: {e}")
        # 清理临时文件
        temp_epub_path = processed_dir / f"temp_{file_path.name}"
        if temp_epub_path.exists():
            temp_epub_path.unlink()
        return {'modified': False, 'replacement_count': 0, 'css_fixed': False, 'error': str(e)}


def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description="Batch Replacer Tool")
    parser.add_argument("--input", "-i", help="Directory containing files and rules.txt")
    args = parser.parse_args()

    # --- 1. 获取目标目录 ---
    if args.input:
        directory_path = args.input
    else:
        # 动态加载默认路径
        default_path = get_default_work_dir()
        
        try:
            prompt_message = (
                f"请输入包含源文件和规则文件的文件夹路径。\n"
                f"(直接按 Enter 键，将使用默认路径 '{default_path}') : "
            )
            user_input = input(prompt_message)
            if not user_input.strip():
                directory_path = default_path
                print(f"[*] 未输入路径，已使用默认路径: {directory_path}")
            else:
                directory_path = user_input.strip()
        except EOFError:
             directory_path = default_path

    if not directory_path:
        # Should not happen given logic above, but safety check
        print("[!] 错误: 未能确定有效的工作目录。")
        sys.exit(1)

    base_dir = Path(directory_path)
    if not base_dir.is_dir():
        print(f"[!] 错误: 文件夹 '{base_dir}' 不存在。")
        sys.exit(1)

    processed_dir = base_dir / PROCESSED_DIR_NAME
    report_dir = base_dir / REPORT_DIR_NAME
    processed_dir.mkdir(exist_ok=True)
    report_dir.mkdir(exist_ok=True)

    print(f"[*] 工作目录: {base_dir}")
    print(f"[*] 输出文件夹已准备就绪:\n    - 处理后文件: {processed_dir}\n    - 变更报告: {report_dir}")

    rules_file = find_rules_file(base_dir)
    if not rules_file:
        print("[!] 错误: 在指定文件夹中未找到 'rules.txt' 格式的规则文件。")
        return
    
    print("[*] 正在从 rules.txt 加载替换规则...")
    rules = load_rules(rules_file)

    if rules.empty:
        print("[!] 规则为空，未执行任何替换。")
        return

    all_target_files = list(base_dir.glob('*.txt')) + list(base_dir.glob('*.epub'))
    files_to_process = [f for f in all_target_files if f.resolve() != rules_file.resolve()]

    if not files_to_process:
        print("[!] 在指定文件夹中没有找到任何需要处理的 .txt 或 .epub 文件。")
        return

    print(f"[+] 成功加载 {len(rules)} 条规则。")
    print(f"[*] 发现 {len(files_to_process)} 个待处理文件。")
    print()

    # 收集处理统计信息
    processing_results = []
    modified_count = 0
    
    with tqdm(total=len(files_to_process), desc="处理进度", unit="个文件", file=sys.stdout) as pbar:
        for file_path in files_to_process:
            pbar.set_postfix_str(file_path.name, refresh=True)
            
            if file_path.suffix == '.txt':
                result = process_txt_file(file_path, rules, processed_dir, report_dir)
            elif file_path.suffix == '.epub':
                result = process_epub_file(file_path, rules, processed_dir, report_dir)
            else:
                result = {'modified': False, 'replacement_count': 0, 'css_fixed': False, 'error': '不支持的文件类型'}
            
            # 添加文件信息到结果中
            result['filename'] = file_path.name
            result['file_type'] = file_path.suffix.upper()[1:]  # 去掉点号并转大写
            processing_results.append(result)
            
            if result['modified']:
                modified_count += 1
            
            pbar.update(1)

    # 以表格形式显示处理结果
    print("\n" + "="*80)
    print("处理结果汇总表")
    print("="*80)
    
    # 表头
    print(f"{'文件名':<40} {'类型':<6} {'替换次数':<8} {'CSS修复':<8} {'状态':<10}")
    print("-"*80)
    
    # 表格内容
    for result in processing_results:
        filename = result['filename']
        if len(filename) > 37:
            filename = filename[:34] + "..."
        
        file_type = result['file_type']
        replacement_count = result['replacement_count']
        css_fixed = "是" if result['css_fixed'] else "否"
        
        if result['error']:
            status = "失败"
        elif result['modified']:
            status = "已修改"
        else:
            status = "无变化"
        
        print(f"{filename:<40} {file_type:<6} {replacement_count:<8} {css_fixed:<8} {status:<10}")
    
    print("-"*80)
    print(f"总计: {len(files_to_process)} 个文件 | 修改: {modified_count} 个 | 总替换次数: {sum(r['replacement_count'] for r in processing_results)}")
    print(f"结果已保存至 '{PROCESSED_DIR_NAME}' 和 '{REPORT_DIR_NAME}' 文件夹")
    print("="*80)

if __name__ == '__main__':
    main()