#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度调试脚本 - 详细分析目标网站结构
"""

import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebsiteDebugger:
    def __init__(self):
        self.base_url = "https://ydydj.univsport.com/level/Levelnotice"
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """设置浏览器驱动"""
        try:
            # 尝试使用系统自带的Chromium
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 尝试使用系统Chromium
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome浏览器初始化成功")
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            # 尝试使用requests进行基础分析
            self.driver = None
    
    def basic_analysis(self):
        """基础网站分析"""
        logger.info("=== 基础网站分析 ===")
        
        try:
            # 检查网站可访问性
            response = requests.get(self.base_url, timeout=10)
            logger.info(f"网站状态码: {response.status_code}")
            logger.info(f"内容类型: {response.headers.get('content-type', '未知')}")
            
            # 检查页面大小
            content_length = len(response.content)
            logger.info(f"页面大小: {content_length} 字节")
            
            # 保存页面内容
            with open('website_content.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info("页面内容已保存到 website_content.html")
            
            # 分析HTML结构
            self.analyze_html_structure(response.text)
            
        except Exception as e:
            logger.error(f"基础分析失败: {e}")
    
    def analyze_html_structure(self, html_content):
        """分析HTML结构"""
        logger.info("=== HTML结构分析 ===")
        
        # 检查关键标签
        tags_to_check = ['title', 'meta', 'script', 'link', 'a', 'div', 'span', 'table', 'form', 'input', 'button']
        
        for tag in tags_to_check:
            count = html_content.count(f'<{tag}')
            logger.info(f"<{tag}> 标签数量: {count}")
        
        # 检查JavaScript框架特征
        framework_indicators = {
            'React': ['react', 'React', '__react', 'data-react'],
            'Vue': ['vue', 'Vue', '__vue', 'data-vue'],
            'Angular': ['ng-', 'angular', 'Angular'],
            'jQuery': ['jquery', '$('],
            'SPA': ['router', 'vue-router', 'react-router'],
        }
        
        for framework, indicators in framework_indicators.items():
            found = any(indicator in html_content for indicator in indicators)
            logger.info(f"{framework} 框架特征: {'✓ 存在' if found else '✗ 不存在'}")
    
    def selenium_analysis(self):
        """使用Selenium进行深度分析"""
        if not self.driver:
            logger.warning("Selenium不可用，跳过深度分析")
            return
        
        logger.info("=== Selenium深度分析 ===")
        
        try:
            # 访问网站
            self.driver.get(self.base_url)
            time.sleep(5)
            
            # 获取页面信息
            page_title = self.driver.title
            current_url = self.driver.current_url
            logger.info(f"页面标题: {page_title}")
            logger.info(f"当前URL: {current_url}")
            
            # 保存页面截图
            self.driver.save_screenshot('page_screenshot.png')
            logger.info("页面截图已保存: page_screenshot.png")
            
            # 保存完整页面源码
            page_source = self.driver.page_source
            with open('selenium_page_source.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            logger.info("Selenium页面源码已保存: selenium_page_source.html")
            
            # 分析DOM结构
            self.analyze_dom_structure()
            
            # 分析JavaScript执行后的内容
            self.analyze_dynamic_content()
            
        except Exception as e:
            logger.error(f"Selenium分析失败: {e}")
    
    def analyze_dom_structure(self):
        """分析DOM结构"""
        logger.info("=== DOM结构分析 ===")
        
        # 查找所有链接
        links = self.driver.find_elements(By.TAG_NAME, 'a')
        logger.info(f"找到 {len(links)} 个链接")
        
        link_info = []
        for i, link in enumerate(links[:10]):  # 只显示前10个
            try:
                href = link.get_attribute('href')
                text = link.text.strip()
                if href:
                    link_info.append({
                        'index': i,
                        'text': text,
                        'href': href,
                        'visible': link.is_displayed()
                    })
            except:
                pass
        
        logger.info("前10个链接信息:")
        for info in link_info:
            logger.info(f"  [{info['index']}] {info['text']} -> {info['href']} (可见: {info['visible']})")
        
        # 查找按钮和表单元素
        buttons = self.driver.find_elements(By.TAG_NAME, 'button')
        inputs = self.driver.find_elements(By.TAG_NAME, 'input')
        forms = self.driver.find_elements(By.TAG_NAME, 'form')
        
        logger.info(f"按钮数量: {len(buttons)}")
        logger.info(f"输入框数量: {len(inputs)}")
        logger.info(f"表单数量: {len(forms)}")
    
    def analyze_dynamic_content(self):
        """分析动态内容"""
        logger.info("=== 动态内容分析 ===")
        
        # 执行JavaScript获取页面信息
        try:
            # 获取所有全局变量
            js_script = """
            return {
                'windowKeys': Object.keys(window),
                'documentTitle': document.title,
                'bodyHTML': document.body.innerHTML.length,
                'scripts': Array.from(document.scripts).map(s => s.src || 'inline'),
                'images': Array.from(document.images).map(img => img.src),
                'links': Array.from(document.links).map(link => link.href)
            };
            """
            
            result = self.driver.execute_script(js_script)
            
            logger.info(f"页面标题: {result.get('documentTitle', '未知')}")
            logger.info(f"body内容长度: {result.get('bodyHTML', 0)} 字符")
            logger.info(f"脚本数量: {len(result.get('scripts', []))}")
            logger.info(f"图片数量: {len(result.get('images', []))}")
            logger.info(f"链接数量: {len(result.get('links', []))}")
            
            # 保存详细分析结果
            with open('dynamic_analysis.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info("动态分析结果已保存: dynamic_analysis.json")
            
        except Exception as e:
            logger.error(f"动态内容分析失败: {e}")
    
    def network_analysis(self):
        """网络请求分析"""
        logger.info("=== 网络请求分析 ===")
        
        # 检查常见的API端点
        api_endpoints = [
            '/api/', '/data/', '/json/', '/ajax/', '/v1/', '/v2/', '/rest/',
            '/notice/', '/download/', '/file/', '/document/', '/list/', '/page/'
        ]
        
        base_domain = "https://ydydj.univsport.com"
        
        for endpoint in api_endpoints:
            url = base_domain + endpoint
            try:
                response = requests.get(url, timeout=5)
                status = response.status_code
                if status != 404:
                    logger.info(f"{url} - 状态码: {status}")
            except:
                pass
    
    def run_complete_analysis(self):
        """运行完整分析"""
        logger.info("开始深度分析目标网站...")
        
        # 基础分析
        self.basic_analysis()
        
        # 网络分析
        self.network_analysis()
        
        # Selenium深度分析
        self.selenium_analysis()
        
        logger.info("深度分析完成！")
        logger.info("生成的文件:")
        logger.info("  - website_content.html: 基础页面内容")
        logger.info("  - page_screenshot.png: 页面截图")
        logger.info("  - selenium_page_source.html: Selenium获取的页面源码")
        logger.info("  - dynamic_analysis.json: 动态内容分析结果")
        logger.info("  - debug.log: 详细日志")
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()

def main():
    """主函数"""
    debugger = WebsiteDebugger()
    try:
        debugger.run_complete_analysis()
    except Exception as e:
        logger.error(f"分析失败: {e}")
    finally:
        debugger.cleanup()

if __name__ == "__main__":
    main()