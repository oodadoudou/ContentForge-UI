#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diritto URL Extractor - 从 Diritto 榜单页面提取指定数量的小说 URL
"""
import os
import sys
import time
import json
import argparse

# Add the diritto directory to sys.path to find browser_launcher
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from browser_launcher import setup_driver_with_auto_launch


def setup_driver():
    """配置并连接到 Chrome 浏览器（自动启动）"""
    return setup_driver_with_auto_launch()


def extract_novel_urls(driver, page_url, count):
    """
    从榜单页面提取指定数量的小说 URL
    
    Args:
        driver: Selenium WebDriver 实例
        page_url: 榜单页面 URL
        count: 要提取的小说数量
    
    Returns:
        list: 小说 URL 列表
    """
    print(f"\n[信息] 正在访问榜单页面: {page_url}")
    driver.get(page_url)
    
    # 等待初始加载
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/contents/"]')))
    except:
        print("⚠️ 页面加载较慢或未找到小说列表...")

    extracted_urls = set()
    scroll_attempts = 0
    max_scroll_attempts = 100  # 增加最大滚动次数
    last_height = driver.execute_script("return document.body.scrollHeight")
    consecutive_no_change = 0
    max_consecutive_no_change = 5 # 允许重试的次数

    print(f"[信息] 正在滚动页面以加载至少 {count} 个小说...")
    
    while scroll_attempts < max_scroll_attempts:
        # 1. 提取当前页面上的所有小说链接
        try:
            # Diritto 的小说链接通常是 /contents/数字
            elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/contents/"]')
            
            for elem in elements:
                url = elem.get_attribute('href')
                # 简单的过滤，确保是内容链接
                if url and '/contents/' in url and url not in extracted_urls:
                    # 清理 URL (移除查询参数)
                    clean_url = url.split('?')[0]
                    # 确保是小说详情页而非章节页
                    if '/episodes/' not in clean_url:
                        extracted_urls.add(clean_url)
        except Exception as e:
            print(f"⚠️ 提取链接时出错: {e}")

        current_count = len(extracted_urls)
        print(f"  当前找到 {current_count} 个唯一小说...")

        if current_count >= count:
            print(f"✅ 已找到足够的小说 ({current_count} >= {count})")
            break
        # 2. 滚动页面 (使用键盘事件)
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            
            # 尝试点击 body 以确保获得焦点 (如果不拦截)
            try:
                body.click()
            except:
                pass

            # 模拟用户行为：End 键到底
            body.send_keys(Keys.END)
            time.sleep(1)
            
            # 再按一次 PageDown 确保底部
            body.send_keys(Keys.PAGE_DOWN)
            
        except Exception as e:
            print(f"⚠️ 滚动失败: {e}")
            # 降级到 JS 滚动
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # 等待加载
        time.sleep(2)

        # 3. 检查高度变化
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            consecutive_no_change += 1
            print(f"  ⚠️ 页面高度未变化 ({consecutive_no_change}/{max_consecutive_no_change})...")
            
            # 尝试强制触发：向上滚动一点点再向下 (Oscillation)
            if consecutive_no_change < max_consecutive_no_change:
                 try:
                    # 使用 JS 回滚 1000px，模拟用户往回看
                    driver.execute_script("window.scrollBy(0, -1000);")
                    time.sleep(1)
                    # 再滚动到底部
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                 except Exception as e:
                    print(f"  ⚠️ 重试滚动失败: {e}")
                 
                 time.sleep(2)
                 # 更新高度
                 new_height = driver.execute_script("return document.body.scrollHeight")
            else:
                print(f"⚠️ 已多次滚动到底部且无新内容，停止滚动。")
                break
        else:
            consecutive_no_change = 0 # 重置计数器
            last_height = new_height
            
        scroll_attempts += 1
    
    # 返回前 N 个 URL
    result_urls = sorted(list(extracted_urls))[:count]
    
    print(f"\n✅ 成功提取 {len(result_urls)} 个小说 URL")
    return result_urls


def main():
    parser = argparse.ArgumentParser(description='从 Diritto 榜单页面提取小说 URL')
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='要提取的小说数量 (默认: 10)'
    )
    parser.add_argument(
        '--url',
        type=str,
        default='https://www.diritto.co.kr/explore/completed-or-published/bl?exploreSubMenu=Completed',
        help='榜单页面 URL (默认: BL完结榜单)'
    )
    
    args = parser.parse_args()
    
    # 验证数量范围
    if args.count < 1 or args.count > 100:
        print("❌ 错误: 提取数量必须在 1-100 之间")
        sys.exit(1)

    # 清理旧的结果文件，防止前端读取到缓存
    output_file = "diritto_extracted_urls.json"
    if os.path.exists(output_file):
        try:
            os.remove(output_file)
            print(f"[信息] 已清理旧的缓存文件: {output_file}")
        except Exception as e:
            print(f"[警告] 无法清理旧文件: {e}")
    
    # 连接浏览器
    driver = setup_driver()
    if not driver:
        sys.exit(1)
    
    try:
        # 提取 URL
        urls = extract_novel_urls(driver, args.url, args.count)
        
        # 输出 JSON 格式（供前端使用）
        result = {"urls": urls}
        print("\n" + "="*60)
        print("JSON 输出:")
        print("="*60)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 也保存到文件（方便查看）
        output_file = "diritto_extracted_urls.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("\n✅ 任务完成。浏览器保持打开状态。")


if __name__ == "__main__":
    main()
