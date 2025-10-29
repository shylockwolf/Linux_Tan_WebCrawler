#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终版爬虫程序 - 综合多种策略
目标网站：https://ydydj.univsport.com/level/Levelnotice
"""

import os
import re
import time
import subprocess
import requests
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime

class FinalLevelCrawler:
    def __init__(self, base_url="https://ydydj.univsport.com/level/Levelnotice"):
        self.base_url = base_url
        self.download_dir = "downloads"
        self.log_file = "crawler.log"
        self.setup_directories()
        self.setup_logging()
        
    def setup_directories(self):
        """创建下载目录"""
        Path(self.download_dir).mkdir(exist_ok=True)
    
    def setup_logging(self):
        """设置日志"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"爬虫日志 - 开始时间: {datetime.now()}\n")
            f.write("=" * 60 + "\n")
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    
    def get_page_with_browser(self, url):
        """使用浏览器获取页面内容"""
        try:
            result = subprocess.run([
                'chromium-browser',
                '--headless',
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--window-size=1920,1080',
                '--dump-dom',
                url
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return result.stdout
            else:
                self.log(f"浏览器命令失败: {result.stderr}")
                return None
                
        except Exception as e:
            self.log(f"浏览器操作失败: {e}")
            return None
    
    def analyze_page_structure(self, html_content):
        """分析页面结构"""
        analysis = {
            'has_app_container': False,
            'has_scripts': False,
            'has_forms': False,
            'has_tables': False,
            'link_count': 0,
            'script_count': 0
        }
        
        # 检查关键元素
        if '<div id="app">' in html_content:
            analysis['has_app_container'] = True
        
        if '<script>' in html_content:
            analysis['has_scripts'] = True
        
        if '<form' in html_content:
            analysis['has_forms'] = True
        
        if '<table' in html_content:
            analysis['has_tables'] = True
        
        # 统计链接和脚本数量
        analysis['link_count'] = len(re.findall(r'<a[^>]*href', html_content))
        analysis['script_count'] = len(re.findall(r'<script', html_content))
        
        return analysis
    
    def extract_possible_links(self, html_content, base_url):
        """提取可能的链接"""
        links = []
        
        # 各种链接模式
        patterns = [
            (r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', "普通链接"),
            (r'<button[^>]*onclick="[^\"]*["\']([^"\']+)["\'][^>]*>(.*?)</button>', "按钮链接"),
            (r'<div[^>]*onclick="[^\"]*["\']([^"\']+)["\'][^>]*>(.*?)</div>', "DIV链接"),
            (r'<span[^>]*onclick="[^\"]*["\']([^"\']+)["\'][^>]*>(.*?)</span>', "SPAN链接"),
            (r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', "JS重定向"),
        ]
        
        for pattern, link_type in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    href = match[0]
                    text = match[1] if len(match) > 1 else ""
                else:
                    href = match
                    text = ""
                
                # 清理文本
                text = re.sub(r'<[^>]*>', '', text).strip()
                
                if href and not href.startswith(('javascript:', 'mailto:', 'tel:')):
                    # 转换为绝对URL
                    full_url = urljoin(base_url, href)
                    
                    links.append({
                        'url': full_url,
                        'text': text or self.get_link_text_from_url(full_url),
                        'type': link_type,
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
    
    def is_downloadable_file(self, url):
        """判断是否可下载文件"""
        downloadable_extensions = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.ppt', '.pptx', '.zip', '.rar', '.7z',
            '.txt', '.csv', '.jpg', '.jpeg', '.png'
        ]
        
        return any(url.lower().endswith(ext) for ext in downloadable_extensions)
    
    def download_file(self, url, filename, category=""):
        """下载文件"""
        try:
            # 创建分类目录
            if category:
                category_dir = os.path.join(self.download_dir, self.sanitize_filename(category))
                Path(category_dir).mkdir(exist_ok=True)
                filepath = os.path.join(category_dir, filename)
            else:
                filepath = os.path.join(self.download_dir, filename)
            
            self.log(f"正在下载: {filename}")
            
            # 使用curl下载（更稳定）
            result = subprocess.run([
                'curl', '-s', '-L', '-o', filepath, url
            ], capture_output=True, timeout=120)
            
            if result.returncode == 0:
                file_size = os.path.getsize(filepath)
                self.log(f"下载完成: {filename} ({file_size} 字节)")
                
                return {
                    'filename': filename,
                    'filepath': filepath,
                    'size': file_size,
                    'url': url
                }
            else:
                self.log(f"下载失败: {result.stderr}")
                return None
                
        except Exception as e:
            self.log(f"下载文件失败: {e}")
            return None
    
    def sanitize_filename(self, filename):
        """清理文件名"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext
        
        return filename
    
    def crawl_with_multiple_strategies(self):
        """使用多种策略进行爬取"""
        strategies = [
            ("直接页面分析", self.direct_page_analysis),
            ("深度链接探索", self.deep_link_exploration),
            ("API端点尝试", self.api_endpoint_try),
        ]
        
        total_downloaded = 0
        
        for strategy_name, strategy_func in strategies:
            self.log(f"\n尝试策略: {strategy_name}")
            downloaded = strategy_func()
            total_downloaded += downloaded
            
            if downloaded > 0:
                self.log(f"策略 {strategy_name} 成功下载 {downloaded} 个文件")
            else:
                self.log(f"策略 {strategy_name} 未找到可下载文件")
            
            time.sleep(2)  # 策略间暂停
        
        return total_downloaded
    
    def direct_page_analysis(self):
        """直接页面分析策略"""
        self.log("获取第一层页面内容...")
        html_content = self.get_page_with_browser(self.base_url)
        
        if not html_content:
            return 0
        
        # 分析页面结构
        analysis = self.analyze_page_structure(html_content)
        self.log(f"页面分析结果: {analysis}")
        
        # 提取链接
        links = self.extract_possible_links(html_content, self.base_url)
        self.log(f"找到 {len(links)} 个链接")
        
        # 下载可下载文件
        downloaded = 0
        for link in links:
            if self.is_downloadable_file(link['url']):
                filename = self.sanitize_filename(link['text'] + ".pdf")
                result = self.download_file(link['url'], filename, "直接下载")
                if result:
                    downloaded += 1
        
        return downloaded
    
    def deep_link_exploration(self):
        """深度链接探索策略"""
        self.log("探索深度链接...")
        
        # 常见深度链接模式
        deep_link_patterns = [
            '/notice', '/download', '/file', '/document',
            '/pdf', '/doc', '/list', '/page', '/article'
        ]
        
        downloaded = 0
        
        for pattern in deep_link_patterns:
            test_url = urljoin(self.base_url, pattern)
            self.log(f"测试深度链接: {test_url}")
            
            html_content = self.get_page_with_browser(test_url)
            if html_content:
                links = self.extract_possible_links(html_content, test_url)
                
                for link in links:
                    if self.is_downloadable_file(link['url']):
                        filename = self.sanitize_filename(link['text'] + ".pdf")
                        result = self.download_file(link['url'], filename, "深度探索")
                        if result:
                            downloaded += 1
        
        return downloaded
    
    def api_endpoint_try(self):
        """API端点尝试策略"""
        self.log("尝试API端点...")
        
        # 常见API端点模式
        api_patterns = [
            '/api/', '/data/', '/json/', '/ajax/',
            '/v1/', '/v2/', '/rest/', '/graphql'
        ]
        
        downloaded = 0
        
        for pattern in api_patterns:
            test_url = urljoin(self.base_url, pattern)
            self.log(f"测试API端点: {test_url}")
            
            try:
                # 尝试JSON请求
                response = requests.get(test_url, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'application/json' in content_type:
                        # 分析JSON数据中的链接
                        try:
                            data = response.json()
                            data_str = json.dumps(data)
                            
                            # 从JSON中提取URL
                            url_pattern = r'"(https?://[^"]+)"'
                            urls = re.findall(url_pattern, data_str)
                            
                            for url in urls:
                                if self.is_downloadable_file(url):
                                    filename = self.sanitize_filename("api_file.pdf")
                                    result = self.download_file(url, filename, "API数据")
                                    if result:
                                        downloaded += 1
                        except:
                            pass
            except:
                pass
        
        return downloaded
    
    def crawl(self):
        """执行爬虫"""
        self.log("=" * 60)
        self.log("最终版爬虫开始运行")
        self.log(f"目标网站: {self.base_url}")
        self.log("=" * 60)
        
        start_time = time.time()
        
        try:
            # 使用多种策略进行爬取
            total_downloaded = self.crawl_with_multiple_strategies()
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.log("=" * 60)
            self.log(f"爬虫运行完成!")
            self.log(f"运行时间: {duration:.2f} 秒")
            self.log(f"总共下载: {total_downloaded} 个文件")
            self.log(f"文件保存: {os.path.abspath(self.download_dir)}")
            self.log(f"日志文件: {self.log_file}")
            self.log("=" * 60)
            
            # 显示下载目录内容
            if os.path.exists(self.download_dir):
                files = list(Path(self.download_dir).rglob('*'))
                self.log(f"下载目录包含 {len(files)} 个文件/目录")
            
        except Exception as e:
            self.log(f"爬虫运行出错: {e}")

def main():
    """主函数"""
    crawler = FinalLevelCrawler()
    
    try:
        crawler.crawl()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()