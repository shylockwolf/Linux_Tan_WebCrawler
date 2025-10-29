#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版爬虫程序 - 使用requests和正则表达式
目标网站：https://ydydj.univsport.com/level/Levelnotice
"""

import os
import re
import requests
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time

class SimpleLevelCrawler:
    def __init__(self, base_url="https://ydydj.univsport.com/level/Levelnotice"):
        self.base_url = base_url
        self.download_dir = "downloads"
        self.session = requests.Session()
        self.setup_session()
        self.setup_directories()
        
    def setup_session(self):
        """设置请求会话"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
    def setup_directories(self):
        """创建下载目录"""
        Path(self.download_dir).mkdir(exist_ok=True)
        
    def get_page_content(self, url):
        """获取页面内容"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"获取页面失败: {url}, 错误: {e}")
            return None
    
    def extract_links(self, html_content, base_url):
        """从HTML内容中提取链接"""
        links = []
        
        # 正则表达式匹配各种链接
        link_patterns = [
            r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',  # a标签链接
            r'href="([^"]*\.html?)"[^>]*>',           # html页面链接
            r'href="([^"]*\.php)"[^>]*>',             # php页面链接
            r'onclick="[^"]*["\']([^"\']+)["\']',    # onclick事件中的链接
        ]
        
        for pattern in link_patterns:
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
            # 从路径中提取文件名或最后一部分
            parts = [p for p in path.split('/') if p]
            if parts:
                last_part = parts[-1]
                # 移除文件扩展名
                name = re.sub(r'\.[^.]+$', '', last_part)
                # 将下划线或连字符转换为空格
                name = re.sub(r'[_-]', ' ', name)
                return name.title() if name else "未命名链接"
        
        return "未命名链接"
    
    def is_downloadable_file(self, url):
        """判断URL是否指向可下载文件"""
        downloadable_extensions = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.ppt', '.pptx', '.zip', '.rar', '.7z',
            '.txt', '.csv', '.jpg', '.jpeg', '.png', '.gif'
        ]
        
        return any(url.lower().endswith(ext) for ext in downloadable_extensions)
    
    def download_file(self, url, filename, category):
        """下载文件"""
        try:
            # 创建分类目录
            category_dir = os.path.join(self.download_dir, self.sanitize_filename(category))
            Path(category_dir).mkdir(exist_ok=True)
            
            filepath = os.path.join(category_dir, filename)
            
            print(f"正在下载: {filename}")
            
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(filepath)
            print(f"✓ 下载完成: {filepath} ({file_size} 字节)")
            
            return {
                'filename': filename,
                'filepath': filepath,
                'size': file_size,
                'url': url
            }
            
        except Exception as e:
            print(f"下载文件失败: {url}, 错误: {e}")
            return None
    
    def sanitize_filename(self, filename):
        """清理文件名，移除非法字符"""
        # 移除非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 限制文件名长度
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext
        
        return filename
    
    def get_filename_from_url(self, url, link_text=""):
        """从URL或链接文本中提取文件名"""
        parsed = urlparse(url)
        path = parsed.path
        
        if path and '/' in path:
            # 从URL路径中提取文件名
            filename = path.split('/')[-1]
            if filename and '.' in filename:
                return self.sanitize_filename(filename)
        
        # 从链接文本创建文件名
        if link_text:
            filename = link_text + ".pdf"  # 默认PDF格式
        else:
            # 从URL创建文件名
            netloc = parsed.netloc.replace('www.', '')
            path_parts = [p for p in path.split('/') if p]
            if path_parts:
                filename = netloc + "_" + "_".join(path_parts) + ".pdf"
            else:
                filename = netloc + "_download.pdf"
        
        return self.sanitize_filename(filename)
    
    def crawl(self):
        """执行爬虫"""
        print("=" * 60)
        print("简化版爬虫开始运行")
        print("目标网站:", self.base_url)
        print("=" * 60)
        
        # 获取第一层页面
        print("\n正在访问第一层页面...")
        first_level_html = self.get_page_content(self.base_url)
        
        if not first_level_html:
            print("无法访问目标网站，程序结束")
            return
        
        print("页面获取成功，正在分析链接...")
        
        # 提取第一层链接
        first_level_links = self.extract_links(first_level_html, self.base_url)
        
        if not first_level_links:
            print("未找到任何链接，程序结束")
            return
        
        print(f"找到 {len(first_level_links)} 个第一层链接")
        
        # 显示找到的链接
        print("\n第一层链接列表:")
        for i, link in enumerate(first_level_links, 1):
            print(f"{i}. {link['text']}")
            print(f"   URL: {link['url']}")
        
        # 爬取第二层页面
        total_downloaded = 0
        
        for i, link in enumerate(first_level_links, 1):
            print(f"\n[{i}/{len(first_level_links)}] 处理链接: {link['text']}")
            print(f"URL: {link['url']}")
            
            # 获取第二层页面
            second_level_html = self.get_page_content(link['url'])
            
            if not second_level_html:
                print("  无法访问第二层页面")
                continue
            
            # 在第二层页面中查找下载链接
            second_level_links = self.extract_links(second_level_html, link['url'])
            download_links = [l for l in second_level_links if self.is_downloadable_file(l['url'])]
            
            print(f"  在第二层页面中找到 {len(download_links)} 个可下载文件")
            
            # 下载文件
            downloaded_files = []
            for dl_link in download_links:
                filename = self.get_filename_from_url(dl_link['url'], dl_link['text'])
                downloaded_file = self.download_file(dl_link['url'], filename, link['text'])
                if downloaded_file:
                    downloaded_files.append(downloaded_file)
            
            total_downloaded += len(downloaded_files)
            
            # 显示下载结果
            if downloaded_files:
                print(f"  成功下载 {len(downloaded_files)} 个文件:")
                for file_info in downloaded_files:
                    print(f"    ✓ {file_info['filename']}")
            else:
                print("  未找到可下载文件")
            
            # 短暂暂停，避免请求过快
            time.sleep(1)
        
        print(f"\n" + "=" * 60)
        print(f"爬虫运行完成!")
        print(f"总共处理了 {len(first_level_links)} 个第一层链接")
        print(f"总共下载了 {total_downloaded} 个文件")
        print(f"文件保存在: {os.path.abspath(self.download_dir)}")
        print("=" * 60)

def main():
    """主函数"""
    crawler = SimpleLevelCrawler()
    
    try:
        crawler.crawl()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()