#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试爬虫 - 用于验证网站结构和链接
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class WebsiteTester:
    def __init__(self, url="https://ydydj.univsport.com/level/Levelnotice"):
        self.url = url
        self.driver = self.setup_driver()
        
    def setup_driver(self):
        """设置浏览器驱动（非无头模式，便于调试）"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            driver = webdriver.Chrome(options=chrome_options)
        
        driver.implicitly_wait(10)
        return driver
    
    def wait_for_page_load(self, timeout=30):
        """等待页面加载完成"""
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
    
    def test_website_structure(self):
        """测试网站结构"""
        print("正在访问目标网站...")
        self.driver.get(self.url)
        self.wait_for_page_load()
        
        # 等待JavaScript加载
        print("等待JavaScript加载...")
        time.sleep(5)
        
        # 获取页面基本信息
        print("\n=== 页面基本信息 ===")
        print(f"页面标题: {self.driver.title}")
        print(f"当前URL: {self.driver.current_url}")
        
        # 获取页面源代码
        page_source = self.driver.page_source
        print(f"页面源代码长度: {len(page_source)} 字符")
        
        # 分析页面结构
        self.analyze_page_structure()
        
        # 查找所有可能的链接
        self.find_all_links()
        
        # 查找特定元素
        self.find_specific_elements()
        
    def analyze_page_structure(self):
        """分析页面结构"""
        print("\n=== 页面结构分析 ===")
        
        # 查找主要容器
        containers = [
            ("header", "header, [class*='header']"),
            ("导航", "nav, [class*='nav'], [class*='menu']"),
            ("主要内容", "main, [class*='main'], [class*='content']"),
            ("侧边栏", "aside, [class*='sidebar']"),
            ("页脚", "footer, [class*='footer']"),
        ]
        
        for name, selector in containers:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"{name}: 找到 {len(elements)} 个元素")
            
            for i, element in enumerate(elements[:3]):  # 只显示前3个
                try:
                    text = element.text.strip()[:50] + "..." if len(element.text) > 50 else element.text
                    print(f"  {i+1}. {text}")
                except:
                    print(f"  {i+1}. [无法获取文本]")
    
    def find_all_links(self):
        """查找所有链接"""
        print("\n=== 链接分析 ===")
        
        # 查找所有链接
        links = self.driver.find_elements(By.TAG_NAME, "a")
        print(f"总共找到 {len(links)} 个 <a> 标签")
        
        # 分类显示链接
        valid_links = []
        invalid_links = []
        
        for link in links:
            try:
                href = link.get_attribute("href")
                text = link.text.strip()
                
                if href and not href.startswith(('javascript:', 'mailto:', 'tel:')):
                    valid_links.append((text, href))
                else:
                    invalid_links.append((text, href))
            except:
                pass
        
        print(f"有效链接: {len(valid_links)} 个")
        print(f"无效链接: {len(invalid_links)} 个")
        
        # 显示有效链接
        print("\n前10个有效链接:")
        for i, (text, href) in enumerate(valid_links[:10]):
            print(f"{i+1}. {text} -> {href}")
        
        # 显示按钮和点击事件
        self.find_buttons_and_clicks()
    
    def find_buttons_and_clicks(self):
        """查找按钮和点击事件"""
        print("\n=== 按钮和点击事件 ===")
        
        # 查找按钮
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        print(f"找到 {len(buttons)} 个按钮")
        
        for i, button in enumerate(buttons[:5]):
            try:
                text = button.text.strip()
                onclick = button.get_attribute("onclick")
                print(f"按钮 {i+1}: {text}")
                if onclick:
                    print(f"  onclick: {onclick[:100]}...")
            except:
                pass
        
        # 查找有onclick事件的元素
        click_elements = self.driver.find_elements(By.CSS_SELECTOR, "[onclick]")
        print(f"\n找到 {len(click_elements)} 个有onclick事件的元素")
        
        for i, element in enumerate(click_elements[:5]):
            try:
                text = element.text.strip()[:30]
                onclick = element.get_attribute("onclick")
                tag = element.tag_name
                print(f"{i+1}. <{tag}> {text}")
                print(f"   onclick: {onclick[:100]}...")
            except:
                pass
    
    def find_specific_elements(self):
        """查找特定元素"""
        print("\n=== 特定元素查找 ===")
        
        # 查找可能的下载链接
        download_selectors = [
            "[href*='.pdf']",
            "[href*='.doc']",
            "[href*='.xls']",
            "[href*='.zip']",
            "[download]",
        ]
        
        for selector in download_selectors:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"找到 {len(elements)} 个 {selector} 元素")
                for element in elements[:3]:
                    try:
                        href = element.get_attribute("href")
                        text = element.text.strip()
                        print(f"  - {text} -> {href}")
                    except:
                        pass
    
    def take_screenshot(self, filename="website_screenshot.png"):
        """截取屏幕截图"""
        self.driver.save_screenshot(filename)
        print(f"\n截图已保存为: {filename}")
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")

def main():
    """主函数"""
    tester = WebsiteTester()
    
    try:
        tester.test_website_structure()
        tester.take_screenshot()
        
        print("\n" + "="*60)
        print("测试完成!")
        print("请查看上面的输出信息来了解网站结构")
        print("截图已保存为 website_screenshot.png")
        print("="*60)
        
        # 等待用户查看结果
        input("按回车键关闭浏览器...")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
    finally:
        tester.close()

if __name__ == "__main__":
    main()