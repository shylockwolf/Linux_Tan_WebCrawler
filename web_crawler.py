#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运动员技术等级查询网站爬虫程序
目标网站：https://ydydj.univsport.com/level/Levelnotice
功能：爬取第一层链接，进入第二层网页，下载可下载文件
"""

import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin, urlparse
import re
from pathlib import Path

class LevelNoticeCrawler:
    def __init__(self, base_url="https://ydydj.univsport.com/level/Levelnotice"):
        self.base_url = base_url
        self.download_dir = "downloads"
        self.setup_directories()
        self.driver = None
        self.setup_driver()
        
    def setup_directories(self):
        """创建下载目录"""
        Path(self.download_dir).mkdir(exist_ok=True)
        
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # 使用新的无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置下载路径
        prefs = {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"使用webdriver_manager失败: {e}")
            # 如果webdriver_manager不可用，尝试使用Chromium
            try:
                # 尝试使用Chromium
                chrome_options.binary_location = '/snap/bin/chromium'
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception as e2:
                print(f"使用Chromium也失败: {e2}")
                # 最后尝试直接使用Chrome
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                except Exception as e3:
                    print(f"所有浏览器驱动尝试都失败: {e3}")
                    raise
        
        self.driver.implicitly_wait(10)
        
    def wait_for_page_load(self, timeout=10):
        """等待页面加载完成"""
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
    def get_first_level_links(self):
        """获取第一层链接"""
        print("正在访问目标网站...")
        self.driver.get(self.base_url)
        self.wait_for_page_load()
        
        # 等待页面内容加载（针对SPA应用）
        time.sleep(5)
        
        print("正在查找第一层链接...")
        
        # 查找所有可能的链接元素
        link_selectors = [
            "a[href]",  # 所有链接
            "button",    # 按钮
            ".link",     # 链接类
            ".btn",      # 按钮类
            "[onclick]", # 点击事件
        ]
        
        first_level_links = []
        
        for selector in link_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    link_info = self.extract_link_info(element, selector)
                    if link_info and self.is_valid_link(link_info):
                        first_level_links.append(link_info)
            except Exception as e:
                print(f"查找选择器 {selector} 时出错: {e}")
        
        # 去重
        unique_links = []
        seen_urls = set()
        
        for link in first_level_links:
            if link['url'] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        print(f"找到 {len(unique_links)} 个第一层链接")
        return unique_links
    
    def extract_link_info(self, element, selector):
        """提取链接信息"""
        try:
            # 获取链接URL
            url = None
            if selector == "a[href]":
                url = element.get_attribute("href")
            elif selector == "[onclick]":
                onclick = element.get_attribute("onclick")
                url = self.parse_onclick_url(onclick)
            
            if not url:
                return None
            
            # 获取链接文本
            text = element.text.strip()
            if not text:
                text = element.get_attribute("title") or element.get_attribute("aria-label") or "无标题"
            
            return {
                'url': url,
                'text': text,
                'element': element
            }
        except Exception as e:
            print(f"提取链接信息时出错: {e}")
            return None
    
    def parse_onclick_url(self, onclick_text):
        """解析onclick事件中的URL"""
        if not onclick_text:
            return None
        
        # 常见的onclick模式
        patterns = [
            r"window\.location\.href=['\"]([^'\"]+)['\"]",
            r"window\.open\(['\"]([^'\"]+)['\"]",
            r"location\.href=['\"]([^'\"]+)['\"]",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, onclick_text)
            if match:
                url = match.group(1)
                if not url.startswith(('http://', 'https://')):
                    url = urljoin(self.base_url, url)
                return url
        
        return None
    
    def is_valid_link(self, link_info):
        """判断是否为有效链接"""
        url = link_info['url']
        
        # 排除无效链接
        if not url or url.startswith(('javascript:', 'mailto:', 'tel:')):
            return False
        
        # 确保是相对或绝对URL
        if not url.startswith(('http://', 'https://')):
            url = urljoin(self.base_url, url)
            link_info['url'] = url
        
        return True
    
    def crawl_second_level(self, first_level_link):
        """爬取第二层页面"""
        print(f"\n正在访问第二层页面: {first_level_link['text']}")
        print(f"URL: {first_level_link['url']}")
        
        try:
            # 点击链接进入第二层页面
            if first_level_link.get('element'):
                first_level_link['element'].click()
            else:
                self.driver.get(first_level_link['url'])
            
            self.wait_for_page_load()
            time.sleep(3)  # 等待页面加载
            
            # 查找可下载文件
            download_links = self.find_download_links()
            
            # 下载文件
            downloaded_files = []
            for download_link in download_links:
                downloaded_file = self.download_file(download_link, first_level_link['text'])
                if downloaded_file:
                    downloaded_files.append(downloaded_file)
            
            return downloaded_files
            
        except Exception as e:
            print(f"爬取第二层页面时出错: {e}")
            return []
        finally:
            # 返回第一层页面
            self.driver.back()
            self.wait_for_page_load()
    
    def find_download_links(self):
        """在第二层页面中查找下载链接"""
        download_selectors = [
            "a[href*='.pdf']",
            "a[href*='.doc']", 
            "a[href*='.xls']",
            "a[href*='.zip']",
            "a[href*='.rar']",
            "a[download]",
            "[class*='download']",
            "[class*='file']",
        ]
        
        download_links = []
        
        for selector in download_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    url = element.get_attribute("href")
                    if url and self.is_downloadable(url):
                        text = element.text.strip() or element.get_attribute("title") or "下载文件"
                        download_links.append({
                            'url': url,
                            'text': text,
                            'element': element
                        })
            except Exception as e:
                print(f"查找下载链接 {selector} 时出错: {e}")
        
        # 去重
        unique_downloads = []
        seen_urls = set()
        
        for link in download_links:
            if link['url'] not in seen_urls:
                unique_downloads.append(link)
                seen_urls.add(link['url'])
        
        print(f"找到 {len(unique_downloads)} 个可下载文件")
        return unique_downloads
    
    def is_downloadable(self, url):
        """判断URL是否可下载"""
        downloadable_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar', '.7z']
        return any(ext in url.lower() for ext in downloadable_extensions)
    
    def download_file(self, download_link, category_name):
        """下载文件"""
        try:
            url = download_link['url']
            filename = self.get_filename_from_url(url, download_link['text'])
            
            # 创建分类目录
            category_dir = os.path.join(self.download_dir, self.sanitize_filename(category_name))
            Path(category_dir).mkdir(exist_ok=True)
            
            filepath = os.path.join(category_dir, filename)
            
            print(f"正在下载: {filename}")
            
            # 使用requests下载文件
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"✓ 下载完成: {filepath}")
            return {
                'filename': filename,
                'filepath': filepath,
                'size': os.path.getsize(filepath)
            }
            
        except Exception as e:
            print(f"下载文件时出错: {e}")
            return None
    
    def get_filename_from_url(self, url, link_text):
        """从URL或链接文本中提取文件名"""
        # 从URL中提取文件名
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        if '/' in path:
            filename = path.split('/')[-1]
            if filename and '.' in filename:
                return self.sanitize_filename(filename)
        
        # 从链接文本创建文件名
        filename = link_text + ".pdf"  # 默认PDF格式
        return self.sanitize_filename(filename)
    
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
    
    def run(self):
        """运行爬虫"""
        try:
            print("=" * 60)
            print("运动员技术等级查询网站爬虫开始运行")
            print("=" * 60)
            
            # 获取第一层链接
            first_level_links = self.get_first_level_links()
            
            if not first_level_links:
                print("未找到任何第一层链接，程序结束")
                return
            
            # 显示找到的链接
            print("\n找到的第一层链接:")
            for i, link in enumerate(first_level_links, 1):
                print(f"{i}. {link['text']} - {link['url']}")
            
            # 爬取第二层页面并下载文件
            total_downloaded = 0
            
            for i, link in enumerate(first_level_links, 1):
                print(f"\n[{i}/{len(first_level_links)}] 处理链接: {link['text']}")
                
                downloaded_files = self.crawl_second_level(link)
                total_downloaded += len(downloaded_files)
                
                # 显示下载结果
                if downloaded_files:
                    print(f"  下载了 {len(downloaded_files)} 个文件:")
                    for file_info in downloaded_files:
                        print(f"    ✓ {file_info['filename']} ({file_info['size']} bytes)")
                else:
                    print("  未找到可下载文件")
                
                # 短暂暂停，避免请求过快
                time.sleep(2)
            
            print(f"\n" + "=" * 60)
            print(f"爬虫运行完成!")
            print(f"总共处理了 {len(first_level_links)} 个第一层链接")
            print(f"总共下载了 {total_downloaded} 个文件")
            print(f"文件保存在: {os.path.abspath(self.download_dir)}")
            print("=" * 60)
            
        except Exception as e:
            print(f"爬虫运行过程中出错: {e}")
        finally:
            self.close()
    
    def close(self):
        """关闭浏览器驱动"""
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")

def main():
    """主函数"""
    crawler = LevelNoticeCrawler()
    
    try:
        crawler.run()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        crawler.close()

if __name__ == "__main__":
    main()