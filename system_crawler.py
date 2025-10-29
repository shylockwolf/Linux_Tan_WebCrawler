#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统版爬虫程序 - 使用系统工具和requests
目标网站：https://ydydj.univsport.com/level/Levelnotice
"""

import os
import re
import requests
import json
import time
import subprocess
from urllib.parse import urljoin, urlparse
from pathlib import Path

class SystemLevelCrawler:
    def __init__(self, base_url="https://ydydj.univsport.com/level/Levelnotice"):
        self.base_url = base_url
        self.download_dir = "downloads"
        self.session = requests.Session()
        self.setup_session()
        self.setup_directories()
        
    def setup_session(self):
        """设置请求会话"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
    def setup_directories(self):
        """创建下载目录"""
        Path(self.download_dir).mkdir(exist_ok=True)
        
    def get_page_with_curl(self, url):
        """使用curl获取页面内容"""
        try:
            result = subprocess.run([
                'curl', '-s', '-L', '-H', 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                url
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"curl命令失败: {result.stderr}")
                return None
        except Exception as e:
            print(f"使用curl获取页面失败: {e}")
            return None
    
    def get_page_content(self, url):
        """获取页面内容（优先使用curl）"""
        # 先尝试使用curl
        content = self.get_page_with_curl(url)
        if content:
            return content
        
        # 如果curl失败，使用requests
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"获取页面失败: {url}, 错误: {e}")
            return None
    
    def analyze_javascript_file(self, js_url):
        """分析JavaScript文件，查找API端点"""
        print(f"正在分析JavaScript文件: {js_url}")
        
        js_content = self.get_page_content(js_url)
        if not js_content:
            return []
        
        # 查找API端点模式
        api_patterns = [
            r'"(/api/[^"]+)"',
            r'"(/level/[^"]+)"',
            r'url:\s*["\']([^"\']+)["\']',
            r'fetch\(["\']([^"\']+)["\']',
            r'axios\.get\(["\']([^"\']+)["\']',
        ]
        
        endpoints = []
        for pattern in api_patterns:
            matches = re.findall(pattern, js_content)
            for match in matches:
                if match.startswith('/'):
                    full_url = urljoin(self.base_url, match)
                    endpoints.append(full_url)
                elif 'http' in match:
                    endpoints.append(match)
        
        # 去重
        unique_endpoints = list(set(endpoints))
        
        print(f"找到 {len(unique_endpoints)} 个可能的API端点")
        for endpoint in unique_endpoints[:10]:  # 只显示前10个
            print(f"  - {endpoint}")
        
        return unique_endpoints
    
    def try_api_endpoints(self, endpoints):
        """尝试调用API端点"""
        results = []
        
        for endpoint in endpoints:
            print(f"尝试API端点: {endpoint}")
            
            try:
                # 尝试GET请求
                response = self.session.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    # 检查返回内容类型
                    if 'application/json' in content_type:
                        data = response.json()
                        print(f"  ✓ JSON响应: {len(str(data))} 字符")
                        results.append({
                            'endpoint': endpoint,
                            'type': 'json',
                            'data': data
                        })
                    elif 'text/html' in content_type:
                        print(f"  ✓ HTML响应: {len(response.text)} 字符")
                        results.append({
                            'endpoint': endpoint,
                            'type': 'html',
                            'data': response.text
                        })
                    else:
                        print(f"  ? 未知内容类型: {content_type}")
                else:
                    print(f"  ✗ 状态码: {response.status_code}")
                    
            except Exception as e:
                print(f"  ✗ 调用失败: {e}")
            
            time.sleep(0.5)  # 短暂暂停
        
        return results
    
    def extract_links_from_api_data(self, api_results):
        """从API数据中提取链接"""
        links = []
        
        for result in api_results:
            if result['type'] == 'json':
                # 从JSON数据中提取链接
                data_str = json.dumps(result['data'])
                links.extend(self.extract_links_from_text(data_str, result['endpoint']))
            elif result['type'] == 'html':
                # 从HTML中提取链接
                links.extend(self.extract_links_from_text(result['data'], result['endpoint']))
        
        return links
    
    def extract_links_from_text(self, text, base_url):
        """从文本中提取链接"""
        links = []
        
        # 各种链接模式
        link_patterns = [
            r'"(https?://[^"]+)"',
            r'"(/[^"]+)"',
            r'href="([^"]+)"',
            r'url":"([^"]+)"',
        ]
        
        for pattern in link_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match.startswith('/'):
                    full_url = urljoin(base_url, match)
                else:
                    full_url = match
                
                if full_url.startswith('http') and full_url not in [l['url'] for l in links]:
                    links.append({
                        'url': full_url,
                        'text': self.get_link_text_from_url(full_url),
                        'source': base_url
                    })
        
        return links
    
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
    
    def download_file(self, url, filename, category):
        """下载文件"""
        try:
            # 创建分类目录
            category_dir = os.path.join(self.download_dir, self.sanitize_filename(category))
            Path(category_dir).mkdir(exist_ok=True)
            
            filepath = os.path.join(category_dir, filename)
            
            print(f"正在下载: {filename}")
            
            # 使用curl下载（更稳定）
            result = subprocess.run([
                'curl', '-s', '-L', '-o', filepath, url
            ], capture_output=True, timeout=60)
            
            if result.returncode == 0:
                file_size = os.path.getsize(filepath)
                print(f"✓ 下载完成: {filepath} ({file_size} 字节)")
                
                return {
                    'filename': filename,
                    'filepath': filepath,
                    'size': file_size,
                    'url': url
                }
            else:
                print(f"✗ 下载失败: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"下载文件失败: {url}, 错误: {e}")
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
    
    def crawl(self):
        """执行爬虫"""
        print("=" * 60)
        print("系统版爬虫开始运行")
        print("目标网站:", self.base_url)
        print("=" * 60)
        
        # 获取第一层页面
        print("\n正在访问目标网站...")
        first_level_html = self.get_page_content(self.base_url)
        
        if not first_level_html:
            print("无法访问目标网站，程序结束")
            return
        
        print("页面获取成功")
        
        # 分析JavaScript文件
        js_pattern = r'src="([^"]*\.js)"'
        js_matches = re.findall(js_pattern, first_level_html, re.IGNORECASE)
        
        if js_matches:
            js_url = urljoin(self.base_url, js_matches[0])
            endpoints = self.analyze_javascript_file(js_url)
            
            if endpoints:
                print("\n尝试调用API端点...")
                api_results = self.try_api_endpoints(endpoints)
                
                if api_results:
                    print("\n从API数据中提取链接...")
                    links = self.extract_links_from_api_data(api_results)
                    
                    if links:
                        print(f"找到 {len(links)} 个链接")
                        self.process_links(links)
                        return
        
        # 如果API方法失败，尝试直接分析页面
        print("\nAPI方法失败，尝试直接分析页面...")
        links = self.extract_links_from_text(first_level_html, self.base_url)
        
        if links:
            print(f"找到 {len(links)} 个链接")
            self.process_links(links)
        else:
            print("未找到任何链接")
    
    def process_links(self, links):
        """处理链接"""
        print("\n链接列表:")
        for i, link in enumerate(links, 1):
            print(f"{i}. {link['text']}")
            print(f"   URL: {link['url']}")
        
        # 筛选可下载文件
        download_links = [l for l in links if self.is_downloadable_file(l['url'])]
        
        if download_links:
            print(f"\n找到 {len(download_links)} 个可下载文件")
            
            total_downloaded = 0
            for i, link in enumerate(download_links, 1):
                print(f"\n[{i}/{len(download_links)}] 下载: {link['text']}")
                
                filename = self.sanitize_filename(link['text'] + ".pdf")
                result = self.download_file(link['url'], filename, "直接下载")
                
                if result:
                    total_downloaded += 1
            
            print(f"\n下载完成! 总共下载了 {total_downloaded} 个文件")
        else:
            print("\n未找到可下载文件")
        
        print(f"\n文件保存在: {os.path.abspath(self.download_dir)}")

def main():
    """主函数"""
    crawler = SystemLevelCrawler()
    
    try:
        crawler.crawl()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()