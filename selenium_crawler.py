#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Selenium模拟真实浏览器行为的爬虫程序
目标网站：https://ydydj.univsport.com/level/Levelnotice
"""

import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse
from urllib.parse import urljoin
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SeleniumWebCrawler:
    def __init__(self):
        self.base_url = "https://ydydj.univsport.com/level/Levelnotice"
        self.download_dir = "downloads"
        self.setup_download_dir()
        self.driver = None
        self.setup_driver()
    
    def setup_download_dir(self):
        """创建下载目录"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            logger.info(f"创建下载目录: {self.download_dir}")
    
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        try:
            # 配置Chrome选项
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--headless')  # 无头模式
            
            # 设置下载目录
            prefs = {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # 使用webdriver-manager自动管理驱动
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 设置页面加载超时
            self.driver.set_page_load_timeout(30)
            
            logger.info("Chrome浏览器驱动初始化成功")
            
        except Exception as e:
            logger.error(f"浏览器驱动初始化失败: {e}")
            raise
    
    def wait_for_element(self, by, value, timeout=10):
        """等待元素出现"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            logger.warning(f"等待元素超时: {by}={value}, {e}")
            return None
    
    def get_first_level_links(self):
        """获取第一层链接"""
        logger.info("正在获取第一层链接...")
        
        # 等待页面加载完成
        time.sleep(5)
        
        # 尝试多种选择器来查找链接
        link_selectors = [
            "a[href]",  # 所有链接
            ".list-group a",  # 列表组链接
            ".panel a",  # 面板链接
            ".card a",  # 卡片链接
            "table a",  # 表格中的链接
            "li a",  # 列表中的链接
            "[class*='link']",  # 包含link的类
            "[class*='item']",  # 包含item的类
            "[class*='list']",  # 包含list的类
        ]
        
        first_level_links = []
        
        for selector in link_selectors:
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for link in links:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    
                    if href and href != "#" and href != "javascript:void(0)":
                        # 确保URL是完整的
                        if not href.startswith("http"):
                            href = urljoin(self.base_url, href)
                        
                        # 过滤掉非目标网站的链接
                        if "ydydj.univsport.com" in href:
                            link_info = {
                                "url": href,
                                "text": text,
                                "element": link
                            }
                            if link_info not in first_level_links:
                                first_level_links.append(link_info)
                                logger.info(f"找到链接: {text} -> {href}")
                
                if first_level_links:
                    break
                    
            except Exception as e:
                logger.warning(f"使用选择器 {selector} 查找链接失败: {e}")
                continue
        
        # 如果没有找到链接，尝试点击可能的导航元素
        if not first_level_links:
            logger.info("未找到明显链接，尝试查找导航元素...")
            self.explore_navigation_elements()
            
            # 重新尝试查找链接
            return self.get_first_level_links()
        
        logger.info(f"共找到 {len(first_level_links)} 个第一层链接")
        return first_level_links
    
    def explore_navigation_elements(self):
        """探索可能的导航元素"""
        navigation_selectors = [
            "button",
            "[onclick]",
            "[class*='btn']",
            "[class*='tab']",
            "[class*='nav']",
            "[class*='menu']",
            "[class*='pagination']",
        ]
        
        for selector in navigation_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        # 尝试点击元素
                        self.driver.execute_script("arguments[0].click();", element)
                        logger.info(f"点击导航元素: {selector}")
                        time.sleep(2)
                        break
                    except:
                        continue
            except:
                continue
    
    def process_second_level_page(self, link_info):
        """处理第二层页面"""
        url = link_info["url"]
        text = link_info["text"]
        
        logger.info(f"正在处理第二层页面: {text}")
        
        try:
            # 打开新标签页
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # 访问第二层页面
            self.driver.get(url)
            time.sleep(3)
            
            # 查找可下载的文件
            downloaded_files = self.find_and_download_files(text)
            
            # 关闭当前标签页，返回主页面
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return downloaded_files
            
        except Exception as e:
            logger.error(f"处理第二层页面失败 {url}: {e}")
            # 确保返回主页面
            try:
                self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return []
    
    def find_and_download_files(self, page_title):
        """在页面中查找并下载文件"""
        downloaded_files = []
        
        # 文件链接选择器
        file_selectors = [
            "a[href$='.pdf']",  # PDF文件
            "a[href$='.doc']",  # Word文档
            "a[href$='.docx']",  # Word文档
            "a[href$='.xls']",  # Excel文件
            "a[href$='.xlsx']",  # Excel文件
            "a[href$='.zip']",  # 压缩文件
            "a[href$='.rar']",  # 压缩文件
            "a[href$='.txt']",  # 文本文件
            "a[download]",  # 有download属性的链接
            "[class*='download'] a",  # 下载类中的链接
            "[class*='file'] a",  # 文件类中的链接
        ]
        
        for selector in file_selectors:
            try:
                file_links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for file_link in file_links:
                    file_url = file_link.get_attribute("href")
                    file_text = file_link.text.strip() or "未命名文件"
                    
                    if file_url:
                        # 下载文件
                        if self.download_file(file_url, file_text, page_title):
                            downloaded_files.append({
                                "url": file_url,
                                "name": file_text,
                                "page": page_title
                            })
                            
            except Exception as e:
                logger.warning(f"查找文件失败 {selector}: {e}")
        
        return downloaded_files
    
    def download_file(self, file_url, file_name, page_title):
        """下载文件"""
        try:
            # 使用requests下载文件
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(file_url, headers=headers, stream=True, timeout=30)
            
            if response.status_code == 200:
                # 清理文件名
                safe_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                if not safe_name:
                    safe_name = "downloaded_file"
                
                # 从URL获取文件扩展名
                file_ext = os.path.splitext(urllib.parse.urlparse(file_url).path)[1]
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
                
                # 创建页面专属目录
                page_dir = os.path.join(self.download_dir, page_title.replace('/', '_'))
                if not os.path.exists(page_dir):
                    os.makedirs(page_dir)
                
                # 保存文件
                file_path = os.path.join(page_dir, f"{safe_name}{file_ext}")
                
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
            logger.error(f"文件下载失败 {file_url}: {e}")
            return False
    
    def crawl(self):
        """执行爬虫任务"""
        logger.info("开始爬虫任务...")
        
        try:
            # 访问目标网站
            self.driver.get(self.base_url)
            logger.info(f"成功访问目标网站: {self.base_url}")
            
            # 等待页面加载
            time.sleep(5)
            
            # 获取页面标题和基本信息
            page_title = self.driver.title
            logger.info(f"页面标题: {page_title}")
            
            # 保存当前页面截图
            screenshot_path = os.path.join(self.download_dir, "page_screenshot.png")
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"页面截图已保存: {screenshot_path}")
            
            # 获取第一层链接
            first_level_links = self.get_first_level_links()
            
            if not first_level_links:
                logger.warning("未找到任何链接，尝试分析页面结构...")
                self.analyze_page_structure()
                return
            
            # 处理每个第一层链接
            total_downloaded = 0
            for i, link_info in enumerate(first_level_links, 1):
                logger.info(f"处理第 {i}/{len(first_level_links)} 个链接: {link_info['text']}")
                
                downloaded_files = self.process_second_level_page(link_info)
                total_downloaded += len(downloaded_files)
                
                # 添加延迟，避免请求过快
                time.sleep(2)
            
            logger.info(f"爬虫任务完成！共处理 {len(first_level_links)} 个链接，下载 {total_downloaded} 个文件")
            
        except Exception as e:
            logger.error(f"爬虫任务失败: {e}")
        finally:
            self.cleanup()
    
    def analyze_page_structure(self):
        """分析页面结构"""
        logger.info("分析页面结构...")
        
        # 获取页面HTML
        page_source = self.driver.page_source
        
        # 保存页面源码
        source_path = os.path.join(self.download_dir, "page_source.html")
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(page_source)
        logger.info(f"页面源码已保存: {source_path}")
        
        # 分析页面中的关键元素
        elements_to_check = [
            ("标题", "h1, h2, h3, h4, h5, h6"),
            ("链接", "a"),
            ("按钮", "button"),
            ("输入框", "input"),
            ("表格", "table"),
            ("列表", "ul, ol"),
            ("图片", "img"),
            ("脚本", "script"),
        ]
        
        for element_type, selector in elements_to_check:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"找到 {len(elements)} 个{element_type}元素")
                
                # 显示前几个元素的内容
                for i, element in enumerate(elements[:3]):
                    try:
                        if element_type == "链接":
                            content = f"文本: {element.text}, URL: {element.get_attribute('href')}"
                        elif element_type == "图片":
                            content = f"ALT: {element.get_attribute('alt')}, SRC: {element.get_attribute('src')}"
                        else:
                            content = element.text[:100] if element.text else "无文本内容"
                        logger.info(f"  {element_type}{i+1}: {content}")
                    except:
                        pass
                        
            except Exception as e:
                logger.warning(f"分析{element_type}失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")

def main():
    """主函数"""
    try:
        crawler = SeleniumWebCrawler()
        crawler.crawl()
    except Exception as e:
        logger.error(f"程序执行失败: {e}")

if __name__ == "__main__":
    main()