#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单PDF爬虫 - 针对 https://ydydj.univsport.com/level/Levelnotice
使用直接请求和API分析
"""

import os
import re
import time
import json
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse

class SimplePDFCrawler:
    def __init__(self, base_url="https://ydydj.univsport.com/level/Levelnotice"):
        self.base_url = base_url
        self.download_dir = "simple_pdf_downloads"
        self.session = requests.Session()
        self.setup_session()
        self.setup_directories()
        
    def setup_session(self):
        """设置会话头信息"""
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
            print(f"获取页面失败 {url}: {e}")
            return ""
    
    def analyze_static_assets(self, content):
        """分析静态资源中的链接"""
        links = []
        
        # 分析JavaScript文件中的链接
        js_patterns = [
            r'"(https?://[^"]+\.pdf)"',  # PDF链接
            r"'(https?://[^']+\.pdf)'",    # PDF链接
            r'"(\/[^"]+\.pdf)"',          # 相对PDF链接
            r"'(\/[^']+\.pdf)'",          # 相对PDF链接
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match.startswith('/'):
                    full_url = urljoin(self.base_url, match)
                else:
                    full_url = match
                
                links.append({
                    'url': full_url,
                    'type': 'pdf',
                    'source': 'javascript'
                })
        
        return links
    
    def analyze_api_patterns(self, content):
        """分析可能的API模式"""
        api_patterns = [
            r'"api[^"]*"',
            r'"data[^"]*"',
            r'"list[^"]*"',
            r'"query[^"]*"',
            r'"search[^"]*"',
            r'"level[^"]*"',
            r'"notice[^"]*"',
        ]
        
        potential_apis = []
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # 清理引号
                api_path = match.strip('"')
                if api_path and len(api_path) > 2:
                    potential_apis.append(api_path)
        
        return potential_apis
    
    def try_api_endpoints(self, api_paths):
        """尝试API端点"""
        pdf_links = []
        
        # 常见的API端点模式
        api_endpoints = [
            f"/api/{path}" for path in api_paths
        ] + [
            f"/api/level/{path}" for path in api_paths
        ] + [
            f"/api/notice/{path}" for path in api_paths
        ] + [
            f"/data/{path}" for path in api_paths
        ]
        
        for endpoint in api_endpoints:
            api_url = urljoin(self.base_url, endpoint)
            
            # 尝试GET请求
            try:
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    # 检查是否是JSON响应
                    if 'application/json' in content_type:
                        try:
                            data = response.json()
                            pdf_links.extend(self.extract_pdf_from_json(data, api_url))
                        except:
                            pass
                    
                    # 检查响应内容中是否包含PDF链接
                    text_content = response.text
                    pdf_matches = re.findall(r'https?://[^\s"\']+\.pdf', text_content)
                    pdf_links.extend([{'url': url, 'type': 'pdf', 'source': 'api'}] for url in pdf_matches)
                    
            except requests.RequestException:
                continue
        
        return pdf_links
    
    def extract_pdf_from_json(self, data, api_url):
        """从JSON数据中提取PDF链接"""
        pdf_links = []
        
        def search_dict(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # 检查值是否是PDF链接
                    if isinstance(value, str) and value.endswith('.pdf'):
                        pdf_links.append({
                            'url': value if value.startswith('http') else urljoin(api_url, value),
                            'type': 'pdf',
                            'source': f'json.{current_path}'
                        })
                    
                    # 递归搜索
                    search_dict(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_dict(item, f"{path}[{i}]")
        
        search_dict(data)
        return pdf_links
    
    def download_pdf(self, pdf_info):
        """下载PDF文件"""
        url = pdf_info['url']
        source = pdf_info['source']
        
        try:
            # 从URL提取文件名
            parsed_url = urlparse(url)
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
            
            # 下载文件
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and 'application' not in content_type.lower():
                print(f"警告: {url} 可能不是PDF文件 (Content-Type: {content_type})")
            
            # 保存文件
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(filepath)
            print(f"✓ 下载成功: {filename} ({file_size} 字节) - 来源: {source}")
            return True
            
        except requests.RequestException as e:
            print(f"✗ 下载失败 {url}: {e}")
            return False
    
    def crawl(self):
        """执行爬虫"""
        print("=" * 60)
        print("简单PDF爬虫开始运行")
        print("目标网站:", self.base_url)
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # 1. 获取主页面内容
            print("\n1. 获取主页面内容...")
            main_content = self.get_page_content(self.base_url)
            
            if not main_content:
                print("无法获取页面内容，程序结束")
                return
            
            print("✓ 页面内容获取成功")
            
            # 2. 分析静态资源
            print("\n2. 分析静态资源中的PDF链接...")
            static_pdfs = self.analyze_static_assets(main_content)
            print(f"发现 {len(static_pdfs)} 个静态PDF链接")
            
            # 3. 分析API模式
            print("\n3. 分析API模式...")
            api_paths = self.analyze_api_patterns(main_content)
            print(f"发现 {len(api_paths)} 个潜在API路径")
            
            # 4. 尝试API端点
            print("\n4. 尝试API端点...")
            api_pdfs = self.try_api_endpoints(api_paths)
            print(f"从API发现 {len(api_pdfs)} 个PDF链接")
            
            # 合并所有PDF链接
            all_pdfs = static_pdfs + api_pdfs
            
            if not all_pdfs:
                print("\n未找到任何PDF链接，尝试其他方法...")
                
                # 5. 尝试常见PDF路径
                common_pdf_paths = [
                    "/pdf/",
                    "/download/",
                    "/files/",
                    "/documents/",
                    "/level/pdf/",
                    "/notice/pdf/",
                    "/api/pdf/",
                ]
                
                for path in common_pdf_paths:
                    pdf_url = urljoin(self.base_url, path)
                    all_pdfs.append({
                        'url': pdf_url,
                        'type': 'pdf',
                        'source': 'common_path'
                    })
            
            # 6. 下载PDF文件
            print(f"\n5. 开始下载PDF文件 (共 {len(all_pdfs)} 个)...")
            
            successful_downloads = 0
            for i, pdf_info in enumerate(all_pdfs, 1):
                print(f"[{i}/{len(all_pdfs)}] 处理: {pdf_info['url']}")
                
                if self.download_pdf(pdf_info):
                    successful_downloads += 1
                
                # 短暂暂停
                time.sleep(1)
            
            # 输出结果
            print("\n" + "=" * 60)
            print("爬虫运行完成!")
            print(f"运行时间: {time.time() - start_time:.2f} 秒")
            print(f"尝试下载: {len(all_pdfs)} 个文件")
            print(f"成功下载: {successful_downloads} 个文件")
            print(f"文件保存在: {os.path.abspath(self.download_dir)}")
            
            if successful_downloads == 0:
                print("\n建议:")
                print("1. 网站可能是动态加载内容的SPA应用")
                print("2. 需要JavaScript渲染才能看到完整内容")
                print("3. 考虑使用Selenium等浏览器自动化工具")
            
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
    crawler = SimplePDFCrawler()
    
    try:
        crawler.crawl()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()