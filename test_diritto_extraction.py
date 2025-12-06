#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify Diritto chapter content extraction from HTML
"""
from bs4 import BeautifulSoup

# Read the sample HTML file
with open('Single_chapter.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')

# Test 1: Extract chapter title
print("=" * 60)
print("Test 1: Extracting Chapter Title")
print("=" * 60)

title_selectors = [
    'span.css-p50amq.e14fx9ai3',
    'span[class*="e14fx9ai3"]',
    '.e14fx9ai0 span',
]

chapter_title = None
for selector in title_selectors:
    elements = soup.select(selector)
    if elements:
        chapter_title = elements[0].get_text(strip=True)
        print(f"✅ Found title using: {selector}")
        print(f"   Title: {chapter_title}")
        break

if not chapter_title:
    print("❌ No title found")

# Test 2: Extract chapter content
print("\n" + "=" * 60)
print("Test 2: Extracting Chapter Content")
print("=" * 60)

content_selectors = [
    'div.tiptap.ProseMirror',
    '.tiptap.ProseMirror',
    '.ProseMirror',
]

content = None
for selector in content_selectors:
    container = soup.select_one(selector)
    if container:
        # Find all <p> tags
        paragraphs = container.find_all('p')
        if paragraphs:
            # Filter out empty paragraphs and those with only <br> tags
            text_paragraphs = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    text_paragraphs.append(text)
            
            if text_paragraphs:
                content = "\n\n".join(text_paragraphs)
                print(f"✅ Found content using: {selector}")
                print(f"   Total paragraphs: {len(text_paragraphs)}")
                print(f"   Content length: {len(content)} characters")
                print(f"\n   First 200 characters:")
                print(f"   {content[:200]}...")
                break

if not content:
    print("❌ No content found")

# Test 3: Show full extraction result
if chapter_title and content:
    print("\n" + "=" * 60)
    print("Test 3: Complete Extraction Result")
    print("=" * 60)
    print(f"Title: {chapter_title}")
    print(f"Content preview (first 500 chars):\n{content[:500]}...\n")
    print(f"✅ Extraction successful!")
    print(f"   Would save to file: 0001_{chapter_title}.txt")
