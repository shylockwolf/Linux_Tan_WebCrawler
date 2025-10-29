#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版网站测试工具
"""

import requests
import re
from urllib.parse import urljoin, urlparse

def test_website_structure():
    """测试网站结构"""
    url = "https://ydydj.univsport.com/level/Levelnotice"
    
    print("正在测试网站结构...")
    print("目标URL:", url)
    print("=" * 60)
    
    try:
        # 发送请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print("✓ 网站访问成功")
        print(f"状态码: {response.status_code}")
        print(f"内容类型: {response.headers.get('content-type', '未知')}")
        print(f"内容长度: {len(response.text)} 字符")
        
        # 分析页面内容
        html_content = response.text
        
        # 检查页面类型
        if '<div id="app"></div>' in html_content:
            print("\n⚠️ 检测到单页应用(SPA)结构")
            print("页面内容通过JavaScript动态加载")
        
        # 查找标题
        title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
        if title_match:
            print(f"页面标题: {title_match.group(1)}")
        
        # 查找链接
        print("\n正在分析页面链接...")
        
        # 各种链接模式
        link_patterns = [
            (r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', "a标签链接"),
            (r'href="([^"]*\.html?)"[^>]*>', "HTML页面链接"),
            (r'href="([^"]*\.php)"[^>]*>', "PHP页面链接"),
            (r'src="([^"]*\.js)"[^>]*>', "JavaScript文件"),
            (r'src="([^"]*\.css)"[^>]*>', "CSS文件"),
        ]
        
        all_links = []
        
        for pattern, description in link_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                print(f"\n{description} ({len(matches)} 个):")
                for match in matches[:5]:  # 只显示前5个
                    if isinstance(match, tuple):
                        href = match[0]
                        text = match[1] if len(match) > 1 else ""
                    else:
                        href = match
                        text = ""
                    
                    # 清理文本
                    text = re.sub(r'<[^>]*>', '', text).strip()
                    
                    if href and not href.startswith(('javascript:', 'mailto:', 'tel:')):
                        full_url = urljoin(url, href)
                        print(f"  - {text[:50]}... -> {full_url}")
                        all_links.append((description, text, full_url))
        
        # 查找可能的下载链接
        print("\n查找可下载文件...")
        download_patterns = [
            r'href="([^"]*\.pdf)"[^>]*>',
            r'href="([^"]*\.doc)"[^>]*>',
            r'href="([^"]*\.docx)"[^>]*>',
            r'href="([^"]*\.xls)"[^>]*>',
            r'href="([^"]*\.zip)"[^>]*>',
        ]
        
        download_links = []
        for pattern in download_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for href in matches:
                full_url = urljoin(url, href)
                download_links.append(full_url)
                print(f"  ✓ 可下载文件: {full_url}")
        
        print(f"\n总共找到 {len(download_links)} 个可下载文件链接")
        
        # 分析页面结构
        print("\n页面结构分析:")
        
        # 检查常见框架特征
        framework_indicators = {
            'Vue.js': ['__VUE__', 'v-', 'vue-'],
            'React': ['__react', 'react-root', 'data-react'],
            'Angular': ['ng-', 'data-ng', 'angular'],
        }
        
        for framework, indicators in framework_indicators.items():
            for indicator in indicators:
                if indicator in html_content:
                    print(f"  - 可能使用 {framework}")
                    break
        
        # 检查API端点
        api_patterns = [
            r'"api[^"]*"',
            r'"endpoint[^"]*"',
            r'"url[^"]*"',
        ]
        
        api_endpoints = []
        for pattern in api_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if 'http' in match:
                    api_endpoints.append(match)
        
        if api_endpoints:
            print(f"\n发现 {len(api_endpoints)} 个API端点:")
            for endpoint in api_endpoints[:3]:
                print(f"  - {endpoint}")
        
        print("\n" + "=" * 60)
        print("测试完成!")
        
        # 建议
        if '<div id="app"></div>' in html_content:
            print("\n建议:")
            print("1. 这是一个单页应用(SPA)，需要使用Selenium等工具模拟浏览器")
            print("2. 或者分析网络请求，直接调用API接口")
        
        return True
        
    except requests.RequestException as e:
        print(f"✗ 网站访问失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试过程中出错: {e}")
        return False

def main():
    """主函数"""
    print("运动员技术等级查询网站结构测试")
    print("=" * 60)
    
    success = test_website_structure()
    
    if success:
        print("\n接下来可以运行简化版爬虫:")
        print("python3 simple_crawler.py")
    else:
        print("\n网站测试失败，请检查网络连接或网站状态")

if __name__ == "__main__":
    main()