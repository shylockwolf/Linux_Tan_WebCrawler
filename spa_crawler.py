#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门针对SPA（单页应用）网站的爬虫程序
目标网站：https://ydydj.univsport.com/level/Levelnotice
"""

import os
import time
import requests
import json
import re
from urllib.parse import urljoin, urlparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spa_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SPACrawler:
    def __init__(self):
        self.base_url = "https://ydydj.univsport.com"
        self.target_url = "https://ydydj.univsport.com/level/Levelnotice"
        self.download_dir = "downloads"
        self.setup_download_dir()
        
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def setup_download_dir(self):
        """创建下载目录"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            logger.info(f"创建下载目录: {self.download_dir}")
    
    def analyze_spa_structure(self):
        """分析SPA网站结构"""
        logger.info("=== 分析SPA网站结构 ===")
        
        try:
            # 获取主页面
            response = self.session.get(self.target_url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"网站访问失败，状态码: {response.status_code}")
                return False
            
            # 保存页面内容
            with open('spa_index.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info("主页面已保存: spa_index.html")
            
            # 分析HTML结构
            html_content = response.text
            
            # 提取JavaScript和CSS文件
            js_files = re.findall(r'<script[^>]*src="([^"]+)"[^>]*>', html_content)
            css_files = re.findall(r'<link[^>]*href="([^"]+)"[^>]*rel="stylesheet"[^>]*>', html_content)
            
            logger.info(f"找到 {len(js_files)} 个JavaScript文件")
            logger.info(f"找到 {len(css_files)} 个CSS文件")
            
            # 下载并分析JavaScript文件
            for js_file in js_files:
                full_url = urljoin(self.base_url, js_file)
                self.analyze_js_file(full_url)
            
            return True
            
        except Exception as e:
            logger.error(f"SPA结构分析失败: {e}")
            return False
    
    def analyze_js_file(self, js_url):
        """分析JavaScript文件"""
        try:
            response = self.session.get(js_url, timeout=10)
            if response.status_code == 200:
                js_content = response.text
                
                # 保存JavaScript文件
                filename = os.path.basename(urlparse(js_url).path)
                if not filename:
                    filename = "unknown.js"
                
                js_path = os.path.join(self.download_dir, "js_analysis", filename)
                os.makedirs(os.path.dirname(js_path), exist_ok=True)
                
                with open(js_path, 'w', encoding='utf-8') as f:
                    f.write(js_content)
                
                # 分析JavaScript内容
                self.extract_api_endpoints(js_content, filename)
                self.extract_data_patterns(js_content, filename)
                
        except Exception as e:
            logger.warning(f"分析JavaScript文件失败 {js_url}: {e}")
    
    def extract_api_endpoints(self, js_content, filename):
        """从JavaScript中提取API端点"""
        # 查找API URL模式
        api_patterns = [
            r'["\'](/api/[^"\']+)["\']',
            r'["\'](/data/[^"\']+)["\']',
            r'["\'](/json/[^"\']+)["\']',
            r'["\'](/ajax/[^"\']+)["\']',
            r'["\'](/v[12]/[^"\']+)["\']',
            r'["\'](/rest/[^"\']+)["\']',
            r'["\'](/notice/[^"\']+)["\']',
            r'["\'](/level/[^"\']+)["\']',
            r'["\'](/download/[^"\']+)["\']',
            r'["\'](/file/[^"\']+)["\']',
        ]
        
        endpoints_found = []
        for pattern in api_patterns:
            matches = re.findall(pattern, js_content)
            for match in matches:
                full_url = urljoin(self.base_url, match)
                if full_url not in endpoints_found:
                    endpoints_found.append(full_url)
        
        if endpoints_found:
            logger.info(f"在 {filename} 中找到 {len(endpoints_found)} 个API端点")
            for endpoint in endpoints_found[:5]:  # 只显示前5个
                logger.info(f"  API端点: {endpoint}")
    
    def extract_data_patterns(self, js_content, filename):
        """从JavaScript中提取数据模式"""
        # 查找可能的数据结构
        data_patterns = [
            r'level[^=]*=[^\{]*\{([^\}]+)\}',
            r'notice[^=]*=[^\{]*\{([^\}]+)\}',
            r'data[^=]*=[^\{]*\{([^\}]+)\}',
            r'list[^=]*=[^\[]*\[([^\]]+)\]',
        ]
        
        for pattern in data_patterns:
            matches = re.findall(pattern, js_content)
            if matches:
                logger.info(f"在 {filename} 中找到数据模式")
    
    def discover_api_endpoints(self):
        """发现API端点"""
        logger.info("=== 发现API端点 ===")
        
        # 常见的API端点路径
        common_endpoints = [
            "/api/notices",
            "/api/levels", 
            "/api/documents",
            "/data/notices",
            "/json/level",
            "/ajax/getNotices",
            "/v1/notices",
            "/v2/level",
            "/rest/notice",
            "/level/api",
            "/notice/list",
            "/download/list",
            "/file/list",
        ]
        
        discovered_endpoints = []
        
        for endpoint in common_endpoints:
            full_url = urljoin(self.base_url, endpoint)
            try:
                response = self.session.get(full_url, timeout=5)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    # 检查是否是JSON数据
                    if 'application/json' in content_type or response.text.strip().startswith('{'):
                        discovered_endpoints.append({
                            'url': full_url,
                            'type': 'JSON API',
                            'size': len(response.text)
                        })
                        logger.info(f"✓ 发现JSON API: {full_url}")
                        
                        # 保存API响应
                        api_filename = endpoint.replace('/', '_') + '.json'
                        api_path = os.path.join(self.download_dir, "api_responses", api_filename)
                        os.makedirs(os.path.dirname(api_path), exist_ok=True)
                        
                        try:
                            # 尝试解析JSON
                            json_data = response.json()
                            with open(api_path, 'w', encoding='utf-8') as f:
                                json.dump(json_data, f, ensure_ascii=False, indent=2)
                            logger.info(f"  API数据已保存: {api_path}")
                            
                            # 分析API数据结构
                            self.analyze_api_data(json_data, endpoint)
                            
                        except:
                            # 如果不是标准JSON，保存原始文本
                            with open(api_path, 'w', encoding='utf-8') as f:
                                f.write(response.text)
                    
                    elif 'text/html' not in content_type:
                        discovered_endpoints.append({
                            'url': full_url,
                            'type': '其他类型',
                            'content_type': content_type
                        })
                        logger.info(f"✓ 发现端点: {full_url} ({content_type})")
                        
            except Exception as e:
                # 忽略连接错误
                pass
        
        return discovered_endpoints
    
    def analyze_api_data(self, json_data, endpoint):
        """分析API返回的数据结构"""
        if isinstance(json_data, dict):
            # 分析字典结构
            keys = list(json_data.keys())
            logger.info(f"  API数据结构 - 键: {keys}")
            
            # 检查是否有列表数据（可能是通知列表）
            for key, value in json_data.items():
                if isinstance(value, list) and value:
                    logger.info(f"  列表 '{key}' 包含 {len(value)} 个元素")
                    if len(value) > 0:
                        # 显示第一个元素的结构
                        first_item = value[0]
                        if isinstance(first_item, dict):
                            item_keys = list(first_item.keys())
                            logger.info(f"    列表项结构: {item_keys}")
        
        elif isinstance(json_data, list) and json_data:
            logger.info(f"  API返回数组，包含 {len(json_data)} 个元素")
            if len(json_data) > 0:
                first_item = json_data[0]
                if isinstance(first_item, dict):
                    item_keys = list(first_item.keys())
                    logger.info(f"    数组项结构: {item_keys}")
    
    def crawl_spa_website(self):
        """爬取SPA网站"""
        logger.info("开始爬取SPA网站...")
        
        # 1. 分析SPA结构
        if not self.analyze_spa_structure():
            logger.error("SPA结构分析失败")
            return
        
        # 2. 发现API端点
        endpoints = self.discover_api_endpoints()
        
        if not endpoints:
            logger.warning("未发现有效的API端点")
            # 尝试其他方法
            self.try_alternative_approaches()
        else:
            logger.info(f"共发现 {len(endpoints)} 个API端点")
            
            # 3. 从API端点获取数据
            self.process_api_endpoints(endpoints)
        
        logger.info("SPA网站爬取完成")
    
    def process_api_endpoints(self, endpoints):
        """处理API端点数据"""
        logger.info("=== 处理API端点数据 ===")
        
        for endpoint in endpoints:
            url = endpoint['url']
            logger.info(f"处理端点: {url}")
            
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    
                    # 尝试解析为JSON
                    try:
                        data = response.json()
                        
                        # 查找可下载的文件链接
                        download_links = self.extract_download_links_from_data(data)
                        
                        if download_links:
                            logger.info(f"找到 {len(download_links)} 个下载链接")
                            self.download_files(download_links)
                        else:
                            logger.info("未找到下载链接")
                            
                    except:
                        # 如果不是JSON，检查是否是文件
                        content_type = response.headers.get('content-type', '')
                        if any(ext in content_type for ext in ['pdf', 'word', 'excel', 'zip']):
                            self.download_file(url, "api_file")
                        
            except Exception as e:
                logger.error(f"处理端点失败 {url}: {e}")
    
    def extract_download_links_from_data(self, data):
        """从数据中提取下载链接"""
        download_links = []
        
        def search_links(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if isinstance(value, str) and any(ext in value.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar']):
                        # 可能是文件链接
                        if value.startswith('http') or value.startswith('/'):
                            full_url = value if value.startswith('http') else urljoin(self.base_url, value)
                            download_links.append({
                                'url': full_url,
                                'source': new_path,
                                'filename': os.path.basename(value)
                            })
                    elif isinstance(value, (dict, list)):
                        search_links(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_links(item, f"{path}[{i}]")
        
        search_links(data)
        return download_links
    
    def download_files(self, download_links):
        """下载文件"""
        for link_info in download_links:
            self.download_file(link_info['url'], link_info['filename'] or "downloaded_file")
    
    def download_file(self, url, filename):
        """下载单个文件"""
        try:
            response = self.session.get(url, timeout=30, stream=True)
            
            if response.status_code == 200:
                # 清理文件名
                safe_name = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                if not safe_name:
                    safe_name = "downloaded_file"
                
                # 从URL获取文件扩展名
                file_ext = os.path.splitext(urlparse(url).path)[1]
                if not file_ext:
                    # 从Content-Type推断文件类型
                    content_type = response.headers.get('content-type', '')
                    if 'pdf' in content_type:
                        file_ext = '.pdf'
                    elif 'word' in content_type:
                        file_ext = '.docx'
                    elif 'excel' in content_type:
                        file_ext = '.xlsx'
                    elif 'zip' in content_type:
                        file_ext = '.zip'
                    else:
                        file_ext = '.bin'
                
                file_path = os.path.join(self.download_dir, f"{safe_name}{file_ext}")
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info(f"✓ 文件下载成功: {file_path}")
                return True
            else:
                logger.warning(f"文件下载失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"文件下载失败 {url}: {e}")
            return False
    
    def try_alternative_approaches(self):
        """尝试替代方法"""
        logger.info("=== 尝试替代方法 ===")
        
        # 方法1: 检查robots.txt
        robots_url = urljoin(self.base_url, "/robots.txt")
        try:
            response = self.session.get(robots_url, timeout=5)
            if response.status_code == 200:
                logger.info("找到robots.txt文件")
                # 分析robots.txt内容
                robots_content = response.text
                with open(os.path.join(self.download_dir, "robots.txt"), 'w') as f:
                    f.write(robots_content)
        except:
            pass
        
        # 方法2: 检查sitemap.xml
        sitemap_url = urljoin(self.base_url, "/sitemap.xml")
        try:
            response = self.session.get(sitemap_url, timeout=5)
            if response.status_code == 200:
                logger.info("找到sitemap.xml文件")
                # 分析sitemap内容
                sitemap_content = response.text
                with open(os.path.join(self.download_dir, "sitemap.xml"), 'w') as f:
                    f.write(sitemap_content)
        except:
            pass

def main():
    """主函数"""
    crawler = SPACrawler()
    crawler.crawl_spa_website()

if __name__ == "__main__":
    main()