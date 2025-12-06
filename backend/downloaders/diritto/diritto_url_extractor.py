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
    wait = WebDriverWait(driver, 30)
    
    # 等待页面加载
    time.sleep(3)
    
    print(f"[信息] 正在滚动页面以加载至少 {count} 个小说...")
    
    # 滚动加载策略
    scroll_attempts = 0
    max_scroll_attempts = 20
    
    while scroll_attempts < max_scroll_attempts:
        # 查找所有小说链接
        novel_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/contents/"]')
        
        # 提取唯一的小说 URL
        unique_urls = set()
        for link in novel_links:
            href = link.get_attribute('href')
            if href and '/contents/' in href:
                # 清理 URL (移除查询参数)
                clean_url = href.split('?')[0]
                # 确保是小说详情页而非章节页
                if '/episodes/' not in clean_url:
                    unique_urls.add(clean_url)
        
        current_count = len(unique_urls)
        print(f"  当前找到 {current_count} 个唯一小说...")
        
        # 如果已经找到足够的小说，停止滚动
        if current_count >= count:
            print(f"✅ 已找到足够的小说 ({current_count} >= {count})")
            break
        
        # 滚动到页面底部
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print(f"⚠️ 已滚动到底部，共找到 {current_count} 个小说")
            break
        
        scroll_attempts += 1
    
    # 返回前 N 个 URL
    result_urls = sorted(list(unique_urls))[:count]
    
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
    if args.count < 1 or args.count > 50:
        print("❌ 错误: 提取数量必须在 1-50 之间")
        sys.exit(1)
    
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
