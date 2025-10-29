#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统浏览器爬虫 - 使用系统工具模拟真实浏览器行为
目标网站：https://ydydj.univsport.com/level/Levelnotice
"""

import os
import re
import time
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urljoin, urlparse

class SystemBrowserCrawler:
    def __init__(self, base_url="https://ydydj.univsport.com/level/Levelnotice"):
        self.base_url = base_url
        self.download_dir = "system_downloads"
        self.visited_urls = set()
        self.downloaded_files = []
        self.setup_directories()
        
    def setup_directories(self):
        """创建下载目录"""
        Path(self.download_dir).mkdir(exist_ok=True)
    
    def save_page_with_browser(self, url, output_file):
        """使用系统浏览器保存页面"""
        try:
            # 尝试使用wget保存完整页面
            result = subprocess.run([
                'wget',
                '--page-requisites',  # 下载所有必要文件
                '--html-extension',    # 保存为.html
                '--convert-links',    # 转换链接
                '--adjust-extension', # 调整扩展名
                '--no-parent',        # 不下载父目录
                '--recursive',        # 递归下载
                '--level=1',          # 只下载1层
                '--timeout=30',
                '--tries=3',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                '-P', self.download_dir,
                url
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✓ 页面保存成功")
                return True
            else:
                print(f"wget失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("页面保存超时")
            return False
        except Exception as e:
            print(f"页面保存失败: {e}")
            return False
    
    def get_page_content_with_curl(self, url):
        """使用curl获取页面内容"""
        try:
            result = subprocess.run([
                'curl', '-s', '-L',
                '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                '-H', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
                url
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"curl失败: {result.stderr}")
                return ""
        except Exception as e:
            print(f"curl错误: {e}")
            return ""
    
    def analyze_website_structure(self):
        """分析网站结构"""
        print("分析网站结构...")
        
        # 1. 获取robots.txt
        robots_url = urljoin(self.base_url, '/robots.txt')
        robots_content = self.get_page_content_with_curl(robots_url)
        if robots_content:
            print("✓ 获取robots.txt成功")
            # 保存robots.txt
            with open(os.path.join(self.download_dir, 'robots.txt'), 'w') as f:
                f.write(robots_content)
        
        # 2. 获取sitemap.xml
        sitemap_url = urljoin(self.base_url, '/sitemap.xml')
        sitemap_content = self.get_page_content_with_curl(sitemap_url)
        if sitemap_content and 'xml' in sitemap_content:
            print("✓ 获取sitemap.xml成功")
            # 保存sitemap.xml
            with open(os.path.join(self.download_dir, 'sitemap.xml'), 'w') as f:
                f.write(sitemap_content)
        
        # 3. 检查常见API端点
        common_endpoints = [
            '/api/level',
            '/api/notice', 
            '/api/pdf',
            '/data/level',
            '/json/level',
            '/level/api',
            '/notice/api'
        ]
        
        api_results = []
        for endpoint in common_endpoints:
            api_url = urljoin(self.base_url, endpoint)
            content = self.get_page_content_with_curl(api_url)
            if content and len(content) > 100:  # 有实际内容
                api_results.append((endpoint, len(content)))
        
        if api_results:
            print("发现API端点:")
            for endpoint, size in api_results:
                print(f"  {endpoint}: {size} 字节")
    
    def extract_pdf_links_from_content(self, content, base_url):
        """从内容中提取PDF链接"""
        pdf_links = []
        
        # 各种PDF链接模式
        pdf_patterns = [
            r'href="([^"]*\.pdf)"',
            r"href='([^']*\.pdf)'",
            r'"url"\s*:\s*"([^"]*\.pdf)"',
            r"'url'\s*:\s*'([^']*\.pdf)'",
            r'"file"\s*:\s*"([^"]*\.pdf)"',
            r'"pdf"\s*:\s*"([^"]*\.pdf)"',
            r'download="([^"]*\.pdf)"',
        ]
        
        for pattern in pdf_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match.startswith('/'):
                    full_url = urljoin(base_url, match)
                elif not match.startswith('http'):
                    full_url = urljoin(base_url, '/' + match.lstrip('/'))
                else:
                    full_url = match
                
                pdf_links.append(full_url)
        
        return list(set(pdf_links))  # 去重
    
    def download_pdf_file(self, pdf_url):
        """下载PDF文件"""
        try:
            # 从URL提取文件名
            parsed_url = urlparse(pdf_url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename or not filename.endswith('.pdf'):
                filename = f"pdf_{int(time.time())}.pdf"
            
            # 清理文件名
            filename = self.sanitize_filename(filename)
            filepath = os.path.join(self.download_dir, filename)
            
            # 检查文件是否已存在
            if os.path.exists(filepath):
                print(f"文件已存在: {filename}")
                return True
            
            # 使用curl下载
            result = subprocess.run([
                'curl', '-s', '-L', '-o', filepath,
                '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                pdf_url
            ], capture_output=True, timeout=60)
            
            if result.returncode == 0:
                # 检查文件大小
                if os.path.getsize(filepath) > 100:  # 至少100字节
                    file_size = os.path.getsize(filepath)
                    print(f"✓ 下载成功: {filename} ({file_size} 字节)")
                    self.downloaded_files.append({
                        'filename': filename,
                        'url': pdf_url,
                        'size': file_size
                    })
                    return True
                else:
                    os.remove(filepath)  # 删除无效文件
                    print(f"✗ 文件太小或无效: {filename}")
                    return False
            else:
                print(f"✗ 下载失败: {filename}")
                return False
                
        except Exception as e:
            print(f"下载错误: {e}")
            return False
    
    def crawl_website(self):
        """爬取网站"""
        print("=" * 60)
        print("系统浏览器爬虫开始运行")
        print("目标网站:", self.base_url)
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # 1. 分析网站结构
            print("\n1. 分析网站结构...")
            self.analyze_website_structure()
            
            # 2. 获取主页面内容
            print("\n2. 获取主页面内容...")
            main_content = self.get_page_content_with_curl(self.base_url)
            
            if not main_content:
                print("无法获取页面内容")
                return
            
            # 保存主页面
            with open(os.path.join(self.download_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(main_content)
            
            print("✓ 主页面获取成功")
            
            # 3. 提取PDF链接
            print("\n3. 提取PDF链接...")
            pdf_links = self.extract_pdf_links_from_content(main_content, self.base_url)
            
            if pdf_links:
                print(f"发现 {len(pdf_links)} 个PDF链接")
                
                # 4. 下载PDF文件
                print("\n4. 下载PDF文件...")
                for i, pdf_url in enumerate(pdf_links, 1):
                    print(f"[{i}/{len(pdf_links)}] 下载: {pdf_url}")
                    self.download_pdf_file(pdf_url)
                    time.sleep(1)  # 短暂暂停
            else:
                print("未发现PDF链接")
            
            # 5. 尝试使用wget递归下载
            print("\n5. 尝试递归下载...")
            if self.save_page_with_browser(self.base_url, 'website_content.html'):
                print("✓ 递归下载完成")
            
            # 输出结果
            print("\n" + "=" * 60)
            print("爬虫运行完成!")
            print(f"运行时间: {time.time() - start_time:.2f} 秒")
            print(f"下载文件数: {len(self.downloaded_files)}")
            
            if self.downloaded_files:
                print("\n下载的文件列表:")
                for i, file_info in enumerate(self.downloaded_files, 1):
                    print(f"{i}. {file_info['filename']} ({file_info['size']} 字节)")
            
            print(f"\n文件保存在: {os.path.abspath(self.download_dir)}")
            
            if len(self.downloaded_files) == 0:
                print("\n建议:")
                print("1. 网站可能是动态加载的SPA应用")
                print("2. 需要JavaScript执行才能看到内容")
                print("3. 考虑安装浏览器自动化工具如Selenium")
            
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
        
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext
        
        return filename

def main():
    """主函数"""
    crawler = SystemBrowserCrawler()
    
    try:
        crawler.crawl_website()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()