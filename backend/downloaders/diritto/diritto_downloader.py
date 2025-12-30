import os
import sys
import time
import json
import shutil
import traceback

# Add the project root to sys.path to find backend module
# Assuming this script is at backend/downloaders/diritto/diritto_downloader.py
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# Add the direito directory to sys.path to find browser_launcher
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from backend.downloaders.diritto.browser_launcher import setup_driver_with_auto_launch
from backend.utils import get_default_work_dir

# --- 脚本核心代码 ---

def log(msg, level="INFO"):
    """Enhanced logging with flush=True for real-time output"""
    prefix = f"[{level}]"
    print(f"{prefix} {msg}", flush=True)

def setup_driver():
    """配置并连接到 Chrome 浏览器（自动启动）"""
    return setup_driver_with_auto_launch()

def process_book(driver, start_url, download_path):
    """
    处理单本书籍的完整下载流程，采用从主页开始并滚动加载的策略。
    """
    stats = {'skipped': 0, 'successful': 0, 'failed': 0, 'failed_items': []}
    
    try:
        # 1. 确定书籍的主页URL
        is_chapter_url = "/episodes/" in start_url
        base_url = start_url.split('/episodes/')[0] if is_chapter_url else start_url.split('?')[0]
        base_url = base_url.rstrip('/')

        log(f"正在访问书籍主页: {base_url}")
        driver.get(base_url)
        wait = WebDriverWait(driver, 45)  # 增加超时时间到45秒
        
        # 2. 获取小说标题
        log("正在等待页面加载并获取小说标题...")
        
        # 尝试使用 Meta 标签获取标题 (更稳定)
        novel_title = None
        
        try:
            # 策略1: og:title
            og_title = driver.find_elements(By.CSS_SELECTOR, 'meta[property="og:title"]')
            if og_title:
                novel_title = og_title[0].get_attribute('content')
                log(f"✅ 找到小说标题 (Meta: og:title): {novel_title}")
            
            # 策略2: twitter:title
            if not novel_title:
                tw_title = driver.find_elements(By.CSS_SELECTOR, 'meta[name="twitter:title"]')
                if tw_title:
                    novel_title = tw_title[0].get_attribute('content')
                    log(f"✅ 找到小说标题 (Meta: twitter:title): {novel_title}")

            # 策略3: document.title
            if not novel_title:
                doc_title = driver.title
                if doc_title:
                    # 通常格式为 "Title | Diritto" 或类似，需清理
                    novel_title = doc_title.split('|')[0].strip()
                    log(f"✅ 找到小说标题 (Document Title): {novel_title}")
            
            # 策略4: H1 标签 (作为最后的备选)
            if not novel_title:
                h1_elements = driver.find_elements(By.TAG_NAME, 'h1')
                if h1_elements:
                    novel_title = h1_elements[0].text.strip()
                    log(f"✅ 找到小说标题 (H1): {novel_title}")

        except Exception as e:
            log(f"⚠️ 获取标题时发生错误: {e}", level="WARN")

        # 清理文件名非法字符
        if novel_title:
            original_title = novel_title
            novel_title = novel_title.replace('/', '_').replace('\\', '_').replace(':', '：').replace('?', '？').replace('*', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            if original_title != novel_title:
                log(f"  (文件名已清理: {original_title} -> {novel_title})")
        
        if not novel_title:
            log("⚠️ 警告: 未能获取小说标题，使用默认名称", level="WARN")
            novel_title = "未知小说"
            
        log(f"📘 小说标题: {novel_title}")

        # 3. 滚动到底部以加载所有章节
        log("正在获取章节列表 (滚动加载)...")
        
        # 滚动加载策略，增加尝试次数限制
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 10
        
        while scroll_attempts < max_scroll_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # 增加等待时间
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                log("✅ 已滚动到底部，加载完成。")
                break
            last_height = new_height
            scroll_attempts += 1
            log(f"  滚动中... ({scroll_attempts}/{max_scroll_attempts})")
        
        if scroll_attempts >= max_scroll_attempts:
            log("⚠️ 达到最大滚动尝试次数，停止滚动。", level="WARN")
        
        # 4. 获取所有章节链接 - 这里的逻辑已更新为更鲁棒的"最佳容器"查找策略
        log("正在分析页面结构以定位章节列表...")
        
        # 策略：查找页面上包含最多有效章节链接的容器(ul或div)
        candidate_containers = driver.find_elements(By.TAG_NAME, "ul") + \
                               driver.find_elements(By.CSS_SELECTOR, "div[class*='list']")
        
        best_container = None
        max_valid_links = 0
        
        for container in candidate_containers:
            try:
                # 快速检查容器内是否有链接
                links = container.find_elements(By.TAG_NAME, "a")
                valid_count = 0
                for link in links:
                    href = link.get_attribute('href')
                    if href and ('/episodes/' in href or 'episode' in href):
                        valid_count += 1
                
                if valid_count > max_valid_links:
                    max_valid_links = valid_count
                    best_container = container
            except Exception:
                continue
        
        full_url_list = []
        
        # 如果找到了包含多个链接的容器，使用它；否则回退到全文搜索
        target_scope = best_container if (best_container and max_valid_links > 3) else driver
        scope_name = "最佳匹配容器" if (best_container and max_valid_links > 3) else "整个页面(回退模式)"
        log(f"✅ 使用 {scope_name} 进行链接提取 (发现 {max_valid_links if best_container else 0} 个潜在链接)")

        try:
            # 获取范围内的所有链接
            all_links = target_scope.find_elements(By.TAG_NAME, "a")
            
            for link in all_links:
                href = link.get_attribute('href')
                text = link.text.strip()
                
                # 核心过滤逻辑
                if href and ('/episodes/' in href or 'episode' in href):
                    # 排除"公知"(Notice)类型的链接
                    if "공지" in text:
                        # log(f"   (跳过公告: {text})")
                        continue
                        
                    full_url_list.append(href)
            
            # 去重并排序
            full_url_list = sorted(list(set(full_url_list)))
            
        except Exception as e:
            log(f"❌ 提取链接时发生错误: {e}", level="ERROR")

        if not full_url_list:
            log("❌ 错误: 未能找到任何章节链接。", level="ERROR")
            return None, None, stats
            
        log(f"共找到 {len(full_url_list)} 个章节。")
        if len(full_url_list) > 0:
             log(f"   🔗 首章: {full_url_list[0]}")
             log(f"   🔗 末章: {full_url_list[-1]}")

        # 5. 确定下载起点
        start_index = 0
        if is_chapter_url:
            try:
                clean_start_url = start_url.split('?')[0].rstrip('/')
                clean_full_url_list = [url.split('?')[0].rstrip('/') for url in full_url_list]
                start_index = clean_full_url_list.index(clean_start_url)
                log(f"✅ 找到下载起点，将从第 {start_index + 1} 章开始处理。")
            except ValueError:
                log(f"⚠️ 警告: 您输入的章节URL {start_url} 未在最终的目录列表中找到。将从第一章开始处理。", level="WARN")
        
        # 创建以小说名命名的主目录及子目录结构
        book_dir = os.path.join(download_path, novel_title)
        chapters_subdir = os.path.join(book_dir, "分卷")
        complete_txt_dir = os.path.join(book_dir, "完整txt")
        os.makedirs(chapters_subdir, exist_ok=True)
        os.makedirs(complete_txt_dir, exist_ok=True)
        log(f"所有文件将保存在: {book_dir}")
        log(f"  - 分卷目录: {chapters_subdir}")
        log(f"  - 完整txt目录: {complete_txt_dir}")
        log(f"DEBUG: 实际绝对路径写入测试: {os.path.abspath(chapters_subdir)}", level="INFO")
        
        # 6. 循环下载每个章节，并加入重试逻辑
        consecutive_failures = 0
        for i, url in enumerate(full_url_list[start_index:], start=start_index):
            chapter_number = i + 1
            log(f"--- 正在处理《{novel_title}》- 第 {chapter_number} / {len(full_url_list)} 章 ---")
            
            chapter_prefix = f"{str(chapter_number).zfill(4)}_"
            
            # 检查分卷目录中是否已存在此章节
            existing_files = []
            if os.path.exists(chapters_subdir):
                existing_files = [f for f in os.listdir(chapters_subdir) if f.startswith(chapter_prefix)]

            if existing_files:
                existing_file_name = existing_files[0]
                log(f"✅ 检测到文件 '{existing_file_name}'，本章已下载，将跳过。")
                stats['skipped'] += 1
                consecutive_failures = 0  # 视为成功以重置计数
                continue

            retries = 0
            MAX_RETRIES = 2
            download_successful = False
            
            while retries < MAX_RETRIES and not download_successful:
                try:
                    if retries > 0:
                        log(f"  - 第 {retries} 次重试... URL: {url}", level="WARN")
                    else:
                        log(f"  - URL: {url}")
                        
                    driver.get(url)

                    # 尝试多个可能的章节标题选择器 (避免 hardcode hash)
                    chapter_title_selectors = [
                        'span[class*="css-p50amq"]',  # Diritto 章节标题稳定前缀
                        'h1[class*="title"]',         # 备用选择器1
                        'h1',                         # 通用h1选择器
                        'h2',                         # 备用h2选择器
                        '[class*="title"]'            # 任何包含title的class
                    ]
                    
                    chapter_title = None
                    for selector in chapter_title_selectors:
                        try:
                            # 快速检测(2s)
                            chapter_title_element = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
                            chapter_title = chapter_title_element.text.strip()
                            if chapter_title:  # 确保标题不为空
                                break
                        except (TimeoutException, Exception):
                            continue
                    
                    if not chapter_title:
                        chapter_title = f"第{chapter_number}章"
                        log(f"  ⚠️ 无法获取章节标题，使用默认: {chapter_title}", level="WARN")
                    
                    # 6. 获取章节内容
                    content_selectors = [
                        'div.ProseMirror',           # 最常见的ProseMirror容器
                        'div[class*="ProseMirror"]', # 宽泛匹配
                        '.tiptap.ProseMirror',       
                        'div[contenteditable="false"]',
                        '.viewer-content',
                        'article',
                        '#viewer-content'
                        # 移除 'main' 选择器，因为它会匹配到错误页面的整页内容导致False Positive
                    ]
                    
                    content = None
                    for selector in content_selectors:
                        try:
                            # 快速检测(2s)
                            content_container = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            
                            # 策略1: 尝试获取所有 p 标签 (通常格式更好)
                            content_elements = content_container.find_elements(By.CSS_SELECTOR, 'p')
                            if content_elements:
                                content = "\n\n".join([p.text for p in content_elements if p.text.strip()])
                            
                            # 策略2: 如果没有 p 标签或内容为空，直接获取容器文本 (innerText)
                            if not content or not content.strip():
                                content = content_container.get_attribute('innerText')
                                
                            if content and content.strip():  # 确保内容不为空
                                # --- 核心校验逻辑 ---
                                # 检查是否提取到了错误提示信息
                                if "회차 내용을 볼 수 없는 작품이에요" in content:
                                     raise ValueError("内容无法查看 (可能需要登录或购买)")
                                
                                # 检查内容长度 (如果太短，极有可能是错误提示)
                                if len(content.strip()) < 100:
                                    log(f"⚠️ 提取内容过短 ({len(content.strip())} 字符)，可能为错误提示: {content.strip()[:20]}...", level="WARN")
                                    
                                log(f"✅ 找到章节内容，使用选择器: {selector}")
                                break
                        except (TimeoutException, Exception):
                            continue
                    
                    if not content or not content.strip():
                        # 尝试保存出错页面的HTML以便调试
                        try:
                            debug_file = "Single_chapter_debug.html"
                            with open(debug_file, "w", encoding="utf-8") as f:
                                f.write(driver.page_source)
                            log(f"  ⚠️ 保存出错页面源码至: {debug_file}", level="DEBUG")
                        except:
                            pass
                        raise ValueError("获取到的内容为空，可能页面结构已变化。")

                    sanitized_title = chapter_title.replace('/', '_').replace('\\', '_').replace(':', '：')
                    file_name = f"{chapter_prefix}{sanitized_title}.txt"
                    file_path = os.path.join(chapters_subdir, file_name)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"{chapter_title}\n\n")
                        f.write(content)
                    
                    log(f"  ✅ 已保存至分卷目录: {file_name}")
                    stats['successful'] += 1
                    download_successful = True

                except Exception as e:
                    retries += 1
                    error_msg = str(e)
                    log(f"  - 抓取本章时出错 (尝试 {retries}/{MAX_RETRIES}): {error_msg}", level="ERROR")
                    
                    # 如果是TimeoutException，提供更详细的调试信息
                    if "TimeoutException" in error_msg or "timeout" in error_msg.lower():
                        log(f"  - 超时错误，可能是页面加载过慢或元素选择器已变化", level="WARN")
                        log(f"  - 当前页面URL: {driver.current_url}", level="WARN")
                        try:
                            page_source_preview = driver.page_source[:500]
                            log(f"  - 页面源码预览: {page_source_preview}...", level="DEBUG")
                        except:
                            log("  - 无法获取页面源码预览", level="DEBUG")
                    
                    if retries < MAX_RETRIES:
                        time.sleep(5)  # 增加重试间隔
                    else:
                        log(f"  ❌ 抓取本章失败，已达到最大重试次数。", level="ERROR")
                        stats['failed'] += 1
                        stats['failed_items'].append({'url': url, 'error': error_msg})

            if download_successful:
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= 2:
                    log("!"*60, level="ERROR")
                    log("❌ 错误: 连续 2 章提取内容失败，停止下载当前书籍。", level="ERROR")
                    log("⚠️ 提示: 如果迟迟无法下载，请在现在打开的浏览器里登入已经成人认证过的账号，然后再次使用", level="WARN")
                    log("⚠️ 提示: 如果依然无法下载可能是diritto官方限时免费已经结束", level="WARN")
                    log("!"*60, level="ERROR")
                    stats['notes'] = "diritto官方已经关闭阅读/需要登录"
                    break

            time.sleep(2)
            
        return novel_title, book_dir, stats

    except Exception as e:
        log(f"❌ 在处理书籍 {start_url} 时发生严重错误: {e}", level="FATAL")
        traceback.print_exc()
        return None, None, stats

def merge_chapters(novel_title, book_dir):
    """将分卷目录中所有TXT文件按顺序合并，保存到完整txt目录。小于3KB的文件将被跳过合并。"""
    chapters_subdir = os.path.join(book_dir, "分卷")
    complete_txt_dir = os.path.join(book_dir, "完整txt")
    merged_filename = os.path.join(complete_txt_dir, f"{novel_title}_完整.txt")
    
    log(f"🔄 开始合并所有章节到一个文件: {merged_filename}")
    
    try:
        if not os.path.exists(chapters_subdir):
            log(f"⚠️ 警告: 目录 {chapters_subdir} 不存在，无法合并。", level="WARN")
            return
        
        # 获取分卷目录中所有的 txt 文件
        all_txt_files = sorted([f for f in os.listdir(chapters_subdir) if f.endswith('.txt') and os.path.isfile(os.path.join(chapters_subdir, f))])

        if not all_txt_files:
            log("⚠️ 警告: 未找到可供合并的章节文件。", level="WARN")
            return

        # 筛选出大于等于3KB的文件用于合并
        files_to_merge = []
        for filename in all_txt_files:
            file_path = os.path.join(chapters_subdir, filename)
            # 修改：将判断条件从 800 字节改为 3 KB (3 * 1024 bytes)
            if os.path.getsize(file_path) < 3 * 1024:
                log(f"  - [跳过合并] 文件 '{filename}' 小于 3 KB，视为非正文内容。", level="DEBUG")
            else:
                files_to_merge.append(filename)

        if not files_to_merge:
            log("⚠️ 警告: 筛选后没有符合大小要求的章节文件可供合并。", level="WARN")
        else:
            # 确保完整txt目录存在
            os.makedirs(complete_txt_dir, exist_ok=True)
            
            with open(merged_filename, 'w', encoding='utf-8') as outfile:
                for i, filename in enumerate(files_to_merge):
                    file_path = os.path.join(chapters_subdir, filename)
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                    
                    if i < len(files_to_merge) - 1:
                        outfile.write("\n\n\n==========\n\n\n")
            
            log(f"✅ 合并完成！小说已保存至: {os.path.abspath(merged_filename)}")
            log(f"📂 章节分卷文件保留在: {os.path.abspath(chapters_subdir)}")
        
    except Exception as e:
        log(f"❌ 合并文件时发生错误: {e}", level="ERROR")

def print_book_report(stats, novel_title):
    """打印单本书籍的执行报告"""
    log("="*40)
    log(f"📋 单本报告: {novel_title or '未知书籍'}")
    log("="*40)
    log(f"✅ 成功下载: {stats['successful']} 章")
    log(f"⏭️ 跳过下载: {stats['skipped']} 章 (已存在)")
    log(f"❌ 下载失败: {stats['failed']} 章")
    
    if 'notes' in stats:
        log(f"⚠️ 状态备注: {stats['notes']}", level="WARN")

    if stats['failed_items']:
        log("--- 失败项目详情 ---", level="WARN")
        for item in stats['failed_items']:
            log(f"- URL: {item['url']}", level="WARN")
            if 'error' in item:
                 log(f"  原因: {item['error']}", level="WARN")
    log("="*40)

def print_total_report(all_book_stats):
    """打印所有任务的总报告"""
    total_stats = {
        'books_processed': len(all_book_stats),
        'books_completed_successfully': 0,
        'books_with_failures': 0,
        'books_aborted': 0,
        'total_successful': 0,
        'total_skipped': 0,
        'total_failed': 0,
    }

    for stats in all_book_stats:
        total_stats['total_successful'] += stats['successful']
        total_stats['total_skipped'] += stats['skipped']
        total_stats['total_failed'] += stats['failed']
        
        if 'notes' in stats and ("停止下载" in stats.get('notes', '') or "关闭免费" in stats.get('notes', '')):
             total_stats['books_aborted'] += 1
        elif stats['failed'] > 0:
            total_stats['books_with_failures'] += 1
        else:
            total_stats['books_completed_successfully'] += 1

    log("#"*50)
    log("📊 所有任务总报告")
    log("#"*50)
    log(f"处理书籍总数: {total_stats['books_processed']}")
    log(f"✅ 完美完成的书籍: {total_stats['books_completed_successfully']}")
    log(f"⚠️ 部分失败的书籍: {total_stats['books_with_failures']}")
    log(f"⛔ 严重错误/中断的书籍: {total_stats['books_aborted']}")
    log("-" * 20)
    log(f"总计成功下载章节: {total_stats['total_successful']}")
    log(f"总计跳过章节: {total_stats['total_skipped']}")
    log(f"总计失败章节: {total_stats['total_failed']}")
    
    if total_stats['books_aborted'] > 0:
        log("-" * 20)
        log("!! 注意 !! 有书籍因连续失败而中断下载。", level="WARN")
        log("可能原因: 1. Diritto官方限时免费结束 2. 未登录账号或Cookie失效", level="WARN")
        log("请尝试在打开的浏览器中登录账号后重试。", level="WARN")
        
    log("#"*50)

if __name__ == "__main__":
    MAX_CONSECUTIVE_FAILURES = 2
    
    # --- 1. 参数解析 ---
    # 简单解析命令行参数，支持 output 和 urls
    output_dir = None
    url_list = []
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--urls':
            if i + 1 < len(args):
                val = args[i+1]
                try:
                    url_list = json.loads(val)
                except:
                    url_list = [u.strip() for u in val.split(',') if u.strip()]
                i += 2
            else:
                log("❌ 错误: --urls 参数缺少值", level="ERROR")
                sys.exit(1)
        elif arg == '--output':
            if i + 1 < len(args):
                output_dir = args[i+1]
                i += 2
            else:
                log("❌ 错误: --output 参数缺少值", level="ERROR")
                sys.exit(1)
        elif arg.startswith("http"):
            url_list.append(arg)
            i += 1
        else:
            i += 1
            
    # --- 2. 确定下载目录 ---
    # 优先使用 --output，否则强制使用系统配置的默认工作目录
    if not output_dir:
        output_dir = get_default_work_dir()
        log(f"未指定输出目录，使用默认下载路径: {output_dir}")
    else:
        log(f"使用指定输出目录: {output_dir}")

    # 确保目录存在
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            log(f"已创建下载目录: {output_dir}")
        except Exception as e:
            log(f"❌ 无法创建目录 {output_dir}: {e}", level="ERROR")
            sys.exit(1)

    # --- 3. 获取URL (交互模式) ---
    if not url_list:
        log("请输入一个或多个Diritto小说URL (可分多行粘贴, 输入完成后按两次回车结束):")
        lines = []
        while True:
            try:
                line = input()
                if not line:
                    break
                lines.append(line)
            except EOFError:
                break
        urls_input = " ".join(lines)
        url_list = [url for url in urls_input.split() if url.startswith("http")]
    
    if not url_list:
        log("❌ 错误: 未输入有效的URL。", level="ERROR")
    else:
        driver = setup_driver()

        if driver:
            all_book_stats = []
            try:
                # --- 顺序处理书籍 ---
                for i, novel_url in enumerate(url_list):
                    log("#"*60)
                    log(f"# 开始处理第 {i + 1} / {len(url_list)} 本书: {novel_url}")
                    log("#"*60)

                    novel_title, book_dir, book_stats = process_book(driver, novel_url, output_dir)
                    
                    if book_stats:
                        all_book_stats.append(book_stats)
                        print_book_report(book_stats, novel_title)

                    if novel_title and book_dir:
                        # cleanup logic: 如果下载完全失败 (0 成功，0 跳过)，清理目录
                        if book_stats and (book_stats['successful'] + book_stats['skipped'] == 0):
                            log(f"⚠️《{novel_title}》下载完全失败 (0 成功，0 跳过)，正在清理目录...", level="WARN")
                            try:
                                if os.path.exists(book_dir):
                                    shutil.rmtree(book_dir)
                                    log(f"✅ 已删除无效目录: {book_dir}")
                            except Exception as e:
                                log(f"❌ 清理目录失败: {e}", level="ERROR")
                        elif book_stats and book_stats['failed'] > 0:
                            log(f"⚠️《{novel_title}》检测到下载失败的项目，已跳过文件合并。", level="WARN")
                            log(f"源文件保留在目录中: {os.path.abspath(book_dir)}")
                        else:
                            merge_chapters(novel_title, book_dir)
            finally:
                if all_book_stats:
                    print_total_report(all_book_stats)
                log("所有任务执行完毕。您可以手动关闭浏览器。")
