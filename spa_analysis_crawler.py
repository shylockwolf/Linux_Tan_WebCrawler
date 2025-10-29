#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPA网站分析爬虫 - 专门处理需要JavaScript渲染的单页面应用
目标网站：https://ydydj.univsport.com/level/Levelnotice
"""

import os
import re
import time
import subprocess
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

class SPAAnalysisCrawler:
    def __init__(self, base_url="https://ydydj.univsport.com/level/Levelnotice"):
        self.base_url = base_url
        self.download_dir = "spa_analysis"
        self.setup_directories()
        
    def setup_directories(self):
        """创建下载目录"""
        Path(self.download_dir).mkdir(exist_ok=True)
    
    def analyze_spa_structure(self):
        """分析SPA网站结构"""
        print("分析SPA网站结构...")
        
        # 1. 获取基础HTML
        html_content = self.get_page_with_curl(self.base_url)
        if html_content:
            self.save_file('index.html', html_content)
            print("✓ 基础HTML获取成功")
            
            # 分析HTML中的关键信息
            self.analyze_html_structure(html_content)
        
        # 2. 分析JavaScript资源
        self.analyze_javascript_resources(html_content)
        
        # 3. 分析网络请求模式
        self.analyze_network_patterns()
        
        # 4. 生成分析报告
        self.generate_analysis_report()
    
    def get_page_with_curl(self, url):
        """使用curl获取页面内容"""
        try:
            result = subprocess.run([
                'curl', '-s', '-L',
                '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                url
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            return ""
        except:
            return ""
    
    def analyze_html_structure(self, html_content):
        """分析HTML结构"""
        print("分析HTML结构...")
        
        # 提取脚本标签
        script_pattern = r'<script[^>]*src="([^"]*)"[^>]*>'
        scripts = re.findall(script_pattern, html_content)
        
        if scripts:
            print(f"发现 {len(scripts)} 个脚本文件")
            for script in scripts:
                print(f"  - {script}")
        
        # 提取链接标签
        link_pattern = r'<link[^>]*href="([^"]*)"[^>]*>'
        links = re.findall(link_pattern, html_content)
        
        if links:
            print(f"发现 {len(links)} 个链接文件")
            for link in links:
                print(f"  - {link}")
        
        # 提取标题
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            print(f"页面标题: {title}")
        
        # 检查Vue/React/Angular特征
        framework_indicators = {
            'Vue.js': ['vue', 'v-app', 'v-model', 'v-for'],
            'React': ['react', 'react-dom', 'jsx'],
            'Angular': ['ng-', 'angular'],
            'jQuery': ['jquery', '$('],
        }
        
        for framework, indicators in framework_indicators.items():
            for indicator in indicators:
                if indicator.lower() in html_content.lower():
                    print(f"可能使用: {framework}")
                    break
    
    def analyze_javascript_resources(self, html_content):
        """分析JavaScript资源"""
        print("分析JavaScript资源...")
        
        # 提取JavaScript文件URL
        js_pattern = r'src="([^"]*\.js)"'
        js_files = re.findall(js_pattern, html_content)
        
        downloaded_js = 0
        for js_url in js_files:
            if not js_url.startswith('http'):
                js_url = urljoin(self.base_url, js_url)
            
            js_content = self.get_page_with_curl(js_url)
            if js_content:
                filename = f"js_{downloaded_js}.js"
                self.save_file(filename, js_content)
                downloaded_js += 1
                
                # 分析JS中的关键词
                self.analyze_js_keywords(js_content, filename)
        
        print(f"下载了 {downloaded_js} 个JavaScript文件")
    
    def analyze_js_keywords(self, js_content, filename):
        """分析JavaScript中的关键词"""
        keywords = [
            'pdf', 'download', 'level', 'notice', 'api', 'data',
            'list', 'query', 'search', 'file', 'document'
        ]
        
        found_keywords = []
        for keyword in keywords:
            if keyword.lower() in js_content.lower():
                found_keywords.append(keyword)
        
        if found_keywords:
            print(f"  {filename}: 发现关键词 - {', '.join(found_keywords)}")
    
    def analyze_network_patterns(self):
        """分析网络请求模式"""
        print("分析网络请求模式...")
        
        # 常见的API端点模式
        api_patterns = [
            '/api/', '/data/', '/json/', '/rest/', '/graphql',
            '/level/', '/notice/', '/pdf/', '/download/', '/file/'
        ]
        
        for pattern in api_patterns:
            api_url = urljoin(self.base_url, pattern)
            
            # 尝试HEAD请求
            try:
                result = subprocess.run([
                    'curl', '-s', '-I', '-L',
                    '-H', 'User-Agent: Mozilla/5.0',
                    api_url
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    # 检查响应状态
                    if '200 OK' in result.stdout or '301' in result.stdout or '302' in result.stdout:
                        print(f"  {pattern}: 可访问")
                    elif '404' in result.stdout:
                        print(f"  {pattern}: 不存在")
                    else:
                        print(f"  {pattern}: 其他状态")
                        
            except:
                pass
    
    def generate_analysis_report(self):
        """生成分析报告"""
        report = """
# SPA网站分析报告

## 目标网站
- URL: https://ydydj.univsport.com/level/Levelnotice

## 分析结果

### 网站类型
- 单页面应用 (SPA)
- 需要JavaScript渲染才能显示完整内容
- 静态爬虫无法获取实际数据

### 技术栈特征
- 使用现代前端框架 (Vue.js/React/Angular)
- 动态加载内容
- API驱动数据获取

### 爬取建议

#### 方法1: 使用浏览器自动化工具
```python
# 需要安装Selenium + ChromeDriver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

driver.get("https://ydydj.univsport.com/level/Levelnotice")
time.sleep(5)  # 等待JavaScript执行
content = driver.page_source
```

#### 方法2: 分析网络请求
- 使用浏览器开发者工具监控网络请求
- 查找API接口
- 直接调用API获取数据

#### 方法3: 使用无头浏览器
```bash
# 使用puppeteer或playwright
npm install puppeteer
```

### 下一步行动
1. 安装浏览器自动化工具
2. 分析网站的实际API接口
3. 模拟真实用户行为获取数据
"""
        
        self.save_file('analysis_report.md', report)
        print("✓ 分析报告已生成")
    
    def save_file(self, filename, content):
        """保存文件"""
        filepath = os.path.join(self.download_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def crawl(self):
        """执行爬虫分析"""
        print("=" * 60)
        print("SPA网站分析爬虫开始运行")
        print("目标网站:", self.base_url)
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            self.analyze_spa_structure()
            
            print("\n" + "=" * 60)
            print("分析完成!")
            print(f"运行时间: {time.time() - start_time:.2f} 秒")
            print(f"分析结果保存在: {os.path.abspath(self.download_dir)}")
            print("=" * 60)
            
        except Exception as e:
            print(f"分析失败: {e}")

def main():
    """主函数"""
    crawler = SPAAnalysisCrawler()
    
    try:
        crawler.crawl()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()