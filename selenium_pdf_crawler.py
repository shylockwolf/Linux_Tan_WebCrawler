#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Selenium模拟浏览器行为的PDF爬虫程序
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
from urllib.parse import urljoin, urlparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('selenium_pdf_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SeleniumPDFCrawler:
    def __init__(self):
        self.base_url = "https://ydydj.univsport.com"
        self.target_url = "https://ydydj.univsport.com/level/Levelnotice"
        self.download_dir = "selenium_pdf_downloads"
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
            # 先不使用无头模式，以便观察浏览器行为
            # chrome_options.add_argument('--headless')
            
            # 设置下载行为
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
    
    def explore_page_structure(self):
        """探索页面结构"""
        logger.info("=== 探索页面结构 ===")
        
        # 保存页面截图
        self.driver.save_screenshot(os.path.join(self.download_dir, 'page_screenshot.png'))
        logger.info("页面截图已保存")
        
        # 获取页面标题
        page_title = self.driver.title
        logger.info(f"页面标题: {page_title}")
        
        # 获取当前URL
        current_url = self.driver.current_url
        logger.info(f"当前URL: {current_url}")
        
        # 获取页面源码
        page_source = self.driver.page_source
        with open(os.path.join(self.download_dir, 'dynamic_page_source.html'), 'w', encoding='utf-8') as f:
            f.write(page_source)
        logger.info("动态页面源码已保存")
        
        # 分析页面中的各种元素
        self.analyze_page_elements()
    
    def analyze_page_elements(self):
        """分析页面中的各种元素"""
        logger.info("=== 分析页面元素 ===")
        
        # 查找所有可见的元素类型
        element_types = [
            ('链接', 'a'),
            ('按钮', 'button'),
            ('输入框', 'input'),
            ('下拉框', 'select'),
            ('表格', 'table'),
            ('列表', 'ul, ol'),
            ('图片', 'img'),
            ('div容器', 'div'),
            ('span元素', 'span'),
        ]
        
        for element_name, selector in element_types:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                visible_elements = [e for e in elements if e.is_displayed()]
                logger.info(f"{element_name}: 总数 {len(elements)}, 可见 {len(visible_elements)}")
                
                # 显示前几个可见元素的信息
                for i, element in enumerate(visible_elements[:3]):
                    try:
                        if element_name == '链接':
                            text = element.text[:50] if element.text else "无文本"
                            href = element.get_attribute('href') or "无链接"
                            logger.info(f"  链接{i+1}: 文本='{text}', href='{href}'")
                        elif element_name == '按钮':
                            text = element.text[:50] if element.text else "无文本"
                            logger.info(f"  按钮{i+1}: 文本='{text}'")
                    except:
                        pass
                        
            except Exception as e:
                logger.warning(f"分析{element_name}失败: {e}")
    
    def find_and_click_links(self):
        """查找并点击可能的链接"""
        logger.info("=== 查找并点击链接 ===")
        
        # 尝试多种选择器来查找链接
        link_selectors = [
            "a[href]:visible",
            "button:visible",
            "[class*='link']:visible",
            "[class*='btn']:visible", 
            "[class*='tab']:visible",
            "[class*='nav']:visible",
            "[class*='menu']:visible",
            "[class*='item']:visible",
            "[class*='list']:visible",
            "[onclick]:visible",
        ]
        
        clicked_links = []
        
        for selector in link_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                visible_elements = [e for e in elements if e.is_displayed()]
                
                for element in visible_elements:
                    try:
                        # 获取元素信息
                        text = element.text.strip()
                        element_type = element.tag_name
                        
                        # 跳过已经点击过的元素
                        element_id = f"{element_type}:{text}"
                        if element_id in clicked_links:
                            continue
                        
                        logger.info(f"尝试点击: {element_type} - 文本: '{text}'")
                        
                        # 点击元素
                        element.click()
                        time.sleep(3)  # 等待页面响应
                        
                        # 检查页面是否发生了变化
                        new_url = self.driver.current_url
                        if new_url != self.target_url:
                            logger.info(f"✓ 页面跳转到: {new_url}")
                            
                            # 在新页面中查找PDF
                            pdf_count = self.search_pdfs_in_current_page(text)
                            
                            # 返回原页面
                            self.driver.back()
                            time.sleep(2)
                        
                        clicked_links.append(element_id)
                        
                    except Exception as e:
                        logger.warning(f"点击元素失败: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"使用选择器 {selector} 失败: {e}")
                continue
    
    def search_pdfs_in_current_page(self, page_name):
        """在当前页面中搜索PDF文件"""
        logger.info(f"在页面 '{page_name}' 中搜索PDF文件...")
        
        pdf_count = 0
        
        # 查找PDF链接
        pdf_selectors = [
            "a[href$='.pdf']",
            "a[href*='pdf']",
            "[href*='.pdf']",
            "[download]",
        ]
        
        for selector in pdf_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        href = element.get_attribute('href')
                        text = element.text.strip() or "未命名"
                        
                        if href and '.pdf' in href.lower():
                            logger.info(f"找到PDF链接: {text} -> {href}")
                            
                            # 下载PDF
                            if self.download_pdf(href, page_name, text):
                                pdf_count += 1
                                
                    except Exception as e:
                        logger.warning(f"处理PDF链接失败: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"使用选择器 {selector} 失败: {e}")
                continue
        
        return pdf_count
    
    def download_pdf(self, pdf_url, page_name, link_text):
        """下载PDF文件"""
        try:
            logger.info(f"正在下载PDF: {link_text}")
            
            # 使用requests下载（避免浏览器下载对话框）
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': self.driver.current_url
            }
            
            response = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
            
            if response.status_code == 200:
                # 生成文件名
                safe_page_name = "".join(c for c in page_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_link_text = "".join(c for c in link_text if c.isalnum() or c in (' ', '-', '_')).rstrip()
                
                if not safe_link_text or safe_link_text == '未命名':
                    filename = f"{safe_page_name}.pdf"
                else:
                    filename = f"{safe_page_name}_{safe_link_text}.pdf"
                
                file_path = os.path.join(self.download_dir, filename)
                
                # 下载文件
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # 检查文件大小
                file_size = os.path.getsize(file_path)
                if file_size > 100:  # 确保不是空文件
                    logger.info(f"✓ PDF下载成功: {filename} ({file_size} 字节)")
                    return True
                else:
                    logger.warning(f"PDF文件太小，可能无效: {filename}")
                    os.remove(file_path)
                    return False
            else:
                logger.warning(f"PDF下载失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"PDF下载失败 {pdf_url}: {e}")
            return False
    
    def crawl(self):
        """执行爬虫任务"""
        logger.info("开始Selenium PDF爬虫任务...")
        
        try:
            # 1. 访问目标网站
            self.driver.get(self.target_url)
            logger.info(f"成功访问目标网站: {self.target_url}")
            
            # 2. 等待页面加载
            time.sleep(5)
            
            # 3. 探索页面结构
            self.explore_page_structure()
            
            # 4. 查找并点击链接
            self.find_and_click_links()
            
            # 5. 统计结果
            self.show_results()
            
        except Exception as e:
            logger.error(f"爬虫任务失败: {e}")
        finally:
            self.cleanup()
    
    def show_results(self):
        """显示爬取结果"""
        logger.info("=" * 50)
        logger.info("爬虫任务完成!")
        
        # 显示下载的文件
        if os.path.exists(self.download_dir):
            files = os.listdir(self.download_dir)
            pdf_files = [f for f in files if f.lower().endswith('.pdf')]
            
            if pdf_files:
                logger.info(f"成功下载 {len(pdf_files)} 个PDF文件:")
                for pdf_file in pdf_files:
                    file_path = os.path.join(self.download_dir, pdf_file)
                    file_size = os.path.getsize(file_path)
                    logger.info(f"  - {pdf_file} ({file_size} 字节)")
            else:
                logger.info("未下载到PDF文件")
        
        logger.info(f"文件保存在: {self.download_dir}")
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")

def main():
    """主函数"""
    try:
        crawler = SeleniumPDFCrawler()
        crawler.crawl()
    except Exception as e:
        logger.error(f"程序执行失败: {e}")

if __name__ == "__main__":
    main()