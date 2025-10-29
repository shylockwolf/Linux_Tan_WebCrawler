#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级爬虫程序 - 使用系统浏览器工具
目标网站：https://ydydj.univsport.com/level/Levelnotice
"""

import os
import re
import time
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urljoin, urlparse

class AdvancedLevelCrawler:
    def __init__(self, base_url="https://ydydj.univsport.com/level/Levelnotice"):
        self.base_url = base_url
        self.download_dir = "downloads"
        self.setup_directories()
        
    def setup_directories(self):
        """创建下载目录"""
        Path(self.download_dir).mkdir(exist_ok=True)
    
    def open_browser_and_save_page(self, url, output_file):
        """使用浏览器打开页面并保存内容"""
        try:
            # 使用chromium-browser保存页面
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
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                return True
            else:
                print(f"浏览器命令失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("浏览器操作超时")
            return False
        except Exception as e:
            print(f"浏览器操作失败: {e}")
            return False
    
    def extract_links_from_html(self, html_file):
        """从HTML文件中提取链接"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            links = []
            
            # 各种链接模式
            link_patterns = [
                (r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', "a标签"),
                (r'<button[^>]*onclick="[^\"]*["\']([^"\']+)["\'][^>]*>(.*?)</button>', "按钮"),
                (r'<div[^>]*onclick="[^\"]*["\']([^"\']+)["\'][^>]*>(.*?)</div>', "div点击"),
                (r'<span[^>]*onclick="[^\"]*["\']([^"\']+)["\'][^>]*>(.*?)</span>', "span点击"),
            ]
            
            for pattern, link_type in link_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
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
                        full_url = urljoin(self.base_url, href)
                        
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
            
        except Exception as e:
            print(f"解析HTML文件失败: {e}")
            return []
    
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
        """判断URL是否指向可下载文件"""
        downloadable_extensions = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.ppt', '.pptx', '.zip', '.rar', '.7z',
            '.txt', '.csv'
        ]
        
        return any(url.lower().endswith(ext) for ext in downloadable_extensions)
    
    def download_with_curl(self, url, output_file):
        """使用curl下载文件"""
        try:
            result = subprocess.run([
                'curl', '-s', '-L', '-o', output_file, url
            ], capture_output=True, timeout=60)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"下载失败: {e}")
            return False
    
    def crawl(self):
        """执行爬虫"""
        print("=" * 60)
        print("高级爬虫开始运行")
        print("目标网站:", self.base_url)
        print("=" * 60)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
            temp_html = temp_file.name
        
        try:
            # 第一步：使用浏览器获取页面内容
            print("\n第一步：使用浏览器获取页面内容...")
            if not self.open_browser_and_save_page(self.base_url, temp_html):
                print("无法获取页面内容，程序结束")
                return
            
            print("✓ 页面内容获取成功")
            
            # 第二步：分析页面内容
            print("\n第二步：分析页面链接...")
            first_level_links = self.extract_links_from_html(temp_html)
            
            if not first_level_links:
                print("未找到任何链接，程序结束")
                return
            
            print(f"找到 {len(first_level_links)} 个第一层链接")
            
            # 显示链接信息
            print("\n第一层链接列表:")
            for i, link in enumerate(first_level_links, 1):
                print(f"{i}. {link['text']} ({link['type']})")
                print(f"   URL: {link['url']}")
            
            # 第三步：处理第二层页面
            print("\n第三步：处理第二层页面...")
            total_downloaded = 0
            
            for i, link in enumerate(first_level_links, 1):
                print(f"\n[{i}/{len(first_level_links)}] 处理链接: {link['text']}")
                
                # 检查是否可直接下载
                if self.is_downloadable_file(link['url']):
                    print("  ✓ 发现可直接下载的文件")
                    filename = self.sanitize_filename(link['text'] + ".pdf")
                    filepath = os.path.join(self.download_dir, filename)
                    
                    if self.download_with_curl(link['url'], filepath):
                        file_size = os.path.getsize(filepath)
                        print(f"  ✓ 下载完成: {filename} ({file_size} 字节)")
                        total_downloaded += 1
                    else:
                        print("  ✗ 下载失败")
                    
                    continue
                
                # 如果不是直接下载链接，尝试访问第二层页面
                print("  访问第二层页面...")
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as second_temp:
                    second_temp_html = second_temp.name
                
                if self.open_browser_and_save_page(link['url'], second_temp_html):
                    # 分析第二层页面
                    second_level_links = self.extract_links_from_html(second_temp_html)
                    
                    if second_level_links:
                        print(f"  在第二层页面中找到 {len(second_level_links)} 个链接")
                        
                        # 查找下载链接
                        download_links = [l for l in second_level_links if self.is_downloadable_file(l['url'])]
                        
                        if download_links:
                            print(f"  发现 {len(download_links)} 个可下载文件")
                            
                            for dl_link in download_links:
                                filename = self.sanitize_filename(dl_link['text'] + ".pdf")
                                category_dir = os.path.join(self.download_dir, self.sanitize_filename(link['text']))
                                Path(category_dir).mkdir(exist_ok=True)
                                
                                filepath = os.path.join(category_dir, filename)
                                
                                if self.download_with_curl(dl_link['url'], filepath):
                                    file_size = os.path.getsize(filepath)
                                    print(f"  ✓ 下载完成: {filename} ({file_size} 字节)")
                                    total_downloaded += 1
                                else:
                                    print(f"  ✗ 下载失败: {filename}")
                        else:
                            print("  未找到可下载文件")
                    else:
                        print("  第二层页面中没有找到链接")
                    
                    # 清理临时文件
                    os.unlink(second_temp_html)
                else:
                    print("  无法访问第二层页面")
                
                # 短暂暂停
                time.sleep(2)
            
            print(f"\n" + "=" * 60)
            print(f"爬虫运行完成!")
            print(f"总共处理了 {len(first_level_links)} 个第一层链接")
            print(f"总共下载了 {total_downloaded} 个文件")
            print(f"文件保存在: {os.path.abspath(self.download_dir)}")
            print("=" * 60)
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_html):
                os.unlink(temp_html)
    
    def sanitize_filename(self, filename):
        """清理文件名"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext
        
        return filename

def main():
    """主函数"""
    crawler = AdvancedLevelCrawler()
    
    try:
        crawler.crawl()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()