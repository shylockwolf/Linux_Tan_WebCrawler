#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网站调试工具 - 深入了解网站结构
"""

import subprocess
import tempfile
import re
import os
from urllib.parse import urljoin, urlparse

def debug_website():
    """调试网站结构"""
    url = "https://ydydj.univsport.com/level/Levelnotice"
    
    print("=" * 60)
    print("网站调试工具")
    print("目标URL:", url)
    print("=" * 60)
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
        temp_html = temp_file.name
    
    try:
        # 方法1: 使用curl获取原始响应
        print("\n1. 使用curl获取原始响应...")
        result = subprocess.run([
            'curl', '-s', '-I', url
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("响应头信息:")
            print(result.stdout)
        
        # 方法2: 使用浏览器获取完整页面
        print("\n2. 使用浏览器获取完整页面...")
        result = subprocess.run([
            'chromium-browser',
            '--headless',
            '--disable-gpu',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--window-size=1920,1080',
            '--dump-dom',
            url
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # 保存页面内容
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            content = result.stdout
            print(f"页面内容长度: {len(content)} 字符")
            
            # 分析页面内容
            print("\n3. 页面内容分析:")
            
            # 检查关键元素
            checks = [
                ("<div id=\"app\">", "Vue.js应用容器"),
                ("<div id=\"root\">", "React应用容器"),
                ("<script>", "内联脚本"),
                ("<iframe", "iframe框架"),
                ("<form", "表单元素"),
                ("<table", "表格元素"),
                ("<nav", "导航元素"),
                ("<menu", "菜单元素"),
            ]
            
            for pattern, description in checks:
                count = content.count(pattern)
                print(f"  {description}: {count} 个")
            
            # 检查JavaScript文件
            print("\n4. JavaScript文件分析:")
            js_patterns = [
                r'src="([^"]*\.js)"',
                r'script src="([^"]+)"',
            ]
            
            js_files = []
            for pattern in js_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    full_url = urljoin(url, match)
                    js_files.append(full_url)
            
            print(f"找到 {len(js_files)} 个JavaScript文件:")
            for js_file in js_files:
                print(f"  - {js_file}")
            
            # 检查CSS文件
            print("\n5. CSS文件分析:")
            css_patterns = [
                r'href="([^"]*\.css)"',
                r'link[^>]*href="([^"]+)"[^>]*rel="stylesheet"',
            ]
            
            css_files = []
            for pattern in css_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    full_url = urljoin(url, match)
                    css_files.append(full_url)
            
            print(f"找到 {len(css_files)} 个CSS文件:")
            for css_file in css_files:
                print(f"  - {css_file}")
            
            # 检查网络请求
            print("\n6. 可能的API端点:")
            api_patterns = [
                r'"(/api/[^"]+)"',
                r'"(/level/[^"]+)"',
                r'url:\s*["\']([^"\']+)["\']',
                r'fetch\(["\']([^"\']+)["\']',
                r'axios\.get\(["\']([^"\']+)["\']',
            ]
            
            api_endpoints = []
            for pattern in api_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if match.startswith('/'):
                        full_url = urljoin(url, match)
                        api_endpoints.append(full_url)
                    elif 'http' in match:
                        api_endpoints.append(match)
            
            print(f"找到 {len(api_endpoints)} 个可能的API端点:")
            for endpoint in api_endpoints[:10]:  # 只显示前10个
                print(f"  - {endpoint}")
            
            # 检查页面文本内容
            print("\n7. 页面文本内容摘要:")
            # 提取所有文本（去除HTML标签）
            text_content = re.sub(r'<[^>]*>', ' ', content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            if len(text_content) > 500:
                print(f"  前500字符: {text_content[:500]}...")
            else:
                print(f"  完整文本: {text_content}")
            
            # 检查特定关键词
            keywords = ['公告', '通知', '下载', '文件', '等级', '运动员', '技术']
            print("\n8. 关键词检查:")
            for keyword in keywords:
                if keyword in content:
                    print(f"  ✓ 找到关键词: {keyword}")
                else:
                    print(f"  ✗ 未找到关键词: {keyword}")
            
            # 保存详细内容到文件
            debug_file = "website_debug.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("网站调试报告\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"目标URL: {url}\n")
                f.write(f"页面长度: {len(content)} 字符\n\n")
                
                f.write("JavaScript文件:\n")
                for js in js_files:
                    f.write(f"  {js}\n")
                f.write("\n")
                
                f.write("CSS文件:\n")
                for css in css_files:
                    f.write(f"  {css}\n")
                f.write("\n")
                
                f.write("API端点:\n")
                for api in api_endpoints:
                    f.write(f"  {api}\n")
                f.write("\n")
                
                f.write("页面内容前1000字符:\n")
                f.write(content[:1000])
                f.write("\n...\n")
            
            print(f"\n详细调试信息已保存到: {debug_file}")
            
            # 建议
            print("\n" + "=" * 60)
            print("调试完成!")
            print("\n建议:")
            
            if "<div id=\"app\">" in content:
                print("1. 这是一个Vue.js单页应用，需要模拟用户交互")
                print("2. 可能需要分析网络请求来找到数据接口")
            elif len(api_endpoints) > 0:
                print("1. 发现了API端点，可以尝试直接调用")
                print("2. 使用浏览器开发者工具分析网络请求")
            else:
                print("1. 网站结构复杂，建议使用Selenium进行完整浏览器模拟")
                print("2. 或者联系网站管理员获取数据接口")
            
            return True
        else:
            print("无法获取页面内容")
            return False
            
    except Exception as e:
        print(f"调试过程中出错: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_html):
            os.unlink(temp_html)

def main():
    """主函数"""
    print("运动员技术等级查询网站调试工具")
    debug_website()

if __name__ == "__main__":
    main()