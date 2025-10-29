#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门针对 https://ydydj.univsport.com/level/Levelnotice 网站的PDF下载爬虫
"""

import os
import re
import time
import subprocess
import tempfile
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests

class LevelPDFCrawler:
    def __init__(self, base_url="https://ydydj.univsport.com/level/Levelnotice"):
        self.base_url = base_url
        self.download_dir = "level_pdf_downloads"
        self.visited_urls = set()
        self.downloaded_files = []
        self.setup_directories()
        
    def setup_directories(self):
        """创建下载目录"""
        Path(self.download_dir).mkdir(exist_ok=True)
    
    def get_page_content(self, url):
        """获取页面内容，对于SPA网站必须使用浏览器"""
        return self.get_page_with_browser(url)
    
    def get_page_with_browser(self, url):
        """使用浏览器获取页面内容"""
        try:
            # 尝试使用google-chrome
            result = subprocess.run([
                'google-chrome',
                '--headless',
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--window-size=1920,1080',
                '--dump-dom',
                url
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Chrome命令失败: {result.stderr}")
                # 尝试使用curl获取基础页面
                return self.get_page_with_curl(url)
                
        except subprocess.TimeoutExpired:
            print("浏览器操作超时")
            return ""
        except Exception as e:
            print(f"浏览器操作失败: {e}")
            return ""
    
    def get_page_with_curl(self, url):
        """使用curl获取页面内容"""
        try:
            result = subprocess.run([
                'curl', '-s', '-L', url
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Curl命令失败: {result.stderr}")
                return ""
        except Exception as e:
            print(f"Curl操作失败: {e}")
            return ""
    
    def extract_links(self, content, base_url):
        """从HTML内容中提取链接"""
        links = []
        
        # 提取a标签链接
        a_pattern = r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
        a_matches = re.findall(a_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for href, text in a_matches:
            if href and not href.startswith(('javascript:', 'mailto:', 'tel:')):
                full_url = urljoin(base_url, href)
                text = re.sub(r'<[^>]*>', '', text).strip()
                
                links.append({
                    'url': full_url,
                    'text': text or self.get_link_text_from_url(full_url),
                    'type': 'link',
                    'original_href': href
                })
        
        # 去重
        unique_links = []
        seen_urls = set()
        
        for link in links:
            if link['url'] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        return unique_links
    
    def get_link_text_from_url(self, url):
        """从URL中提取有意义的文本"""
        parsed = urlparse(url)
        path = parsed.path
        
        if path:
            parts = [p for p in path.split('/') if p]
            if parts:
                last_part = parts[-1]
                name = re.sub(r'\.[^.]+$', '', last_part)
                name = re.sub(r'[_-]', ' ', name)
                return name.title() if name else "未命名链接"
        
        return "未命名链接"
    
    def is_pdf_link(self, url):
        """判断URL是否指向PDF文件"""
        return url.lower().endswith('.pdf')
    
    def download_pdf(self, url, filename):
        """下载PDF文件"""
        try:
            # 使用curl下载
            result = subprocess.run([
                'curl', '-s', '-L', '-o', filename, url
            ], capture_output=True, timeout=60)
            
            if result.returncode == 0:
                # 检查文件是否有效
                if os.path.getsize(filename) > 0:
                    return True
            
            return False
            
        except Exception as e:
            print(f"下载失败: {e}")
            return False
    
    def crawl_level_page(self, url, depth=0, max_depth=3):
        """递归爬取页面"""
        if depth > max_depth or url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        
        print(f"{'  ' * depth}[深度 {depth}] 访问: {url}")
        
        # 获取页面内容
        content = self.get_page_content(url)
        if not content:
            print(f"{'  ' * depth}✗ 无法获取页面内容")
            return
        
        # 提取链接
        links = self.extract_links(content, url)
        
        if not links:
            print(f"{'  ' * depth}未找到链接")
            return
        
        # 处理当前页面的PDF链接
        pdf_links = [link for link in links if self.is_pdf_link(link['url'])]
        
        if pdf_links:
            print(f"{'  ' * depth}发现 {len(pdf_links)} 个PDF文件")
            
            for pdf_link in pdf_links:
                filename = self.sanitize_filename(pdf_link['text'] + ".pdf")
                filepath = os.path.join(self.download_dir, filename)
                
                if not os.path.exists(filepath):
                    print(f"{'  ' * depth}下载: {filename}")
                    
                    if self.download_pdf(pdf_link['url'], filepath):
                        file_size = os.path.getsize(filepath)
                        print(f"{'  ' * depth}✓ 下载完成: {file_size} 字节")
                        self.downloaded_files.append({
                            'filename': filename,
                            'url': pdf_link['url'],
                            'size': file_size
                        })
                    else:
                        print(f"{'  ' * depth}✗ 下载失败")
                else:
                    print(f"{'  ' * depth}✓ 文件已存在: {filename}")
        
        # 递归处理非PDF链接
        non_pdf_links = [link for link in links if not self.is_pdf_link(link['url'])]
        
        if non_pdf_links:
            print(f"{'  ' * depth}继续处理 {len(non_pdf_links)} 个非PDF链接")
            
            for link in non_pdf_links:
                # 避免无限循环
                if link['url'] not in self.visited_urls:
                    self.crawl_level_page(link['url'], depth + 1, max_depth)
                    time.sleep(1)  # 短暂暂停
    
    def crawl(self):
        """执行爬虫"""
        print("=" * 60)
        print("PDF爬虫开始运行")
        print("目标网站:", self.base_url)
        print("下载目录:", self.download_dir)
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # 开始递归爬取
            self.crawl_level_page(self.base_url)
            
            # 输出结果
            print("\n" + "=" * 60)
            print("爬虫运行完成!")
            print(f"运行时间: {time.time() - start_time:.2f} 秒")
            print(f"访问页面数: {len(self.visited_urls)}")
            print(f"下载文件数: {len(self.downloaded_files)}")
            
            if self.downloaded_files:
                print("\n下载的文件列表:")
                for i, file_info in enumerate(self.downloaded_files, 1):
                    print(f"{i}. {file_info['filename']} ({file_info['size']} 字节)")
            
            print(f"\n文件保存在: {os.path.abspath(self.download_dir)}")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n程序被用户中断")
        except Exception as e:
            print(f"程序运行出错: {e}")
    
    def sanitize_filename(self, filename):
        """清理文件名"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 限制文件名长度
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext
        
        return filename

def main():
    """主函数"""
    crawler = LevelPDFCrawler()
    
    try:
        crawler.crawl()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()