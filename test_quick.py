#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试爬虫功能
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_crawler import LevelNoticeCrawler

def quick_test():
    """快速测试爬虫基本功能"""
    print("开始快速测试爬虫功能...")
    
    try:
        # 创建爬虫实例
        crawler = LevelNoticeCrawler()
        
        # 测试驱动设置
        print("✓ 浏览器驱动设置成功")
        
        # 测试访问网站
        print("正在访问目标网站...")
        crawler.driver.get(crawler.base_url)
        crawler.wait_for_page_load()
        
        # 检查页面标题
        title = crawler.driver.title
        print(f"✓ 网站访问成功，标题: {title}")
        
        # 测试查找链接
        print("正在查找第一层链接...")
        links = crawler.get_first_level_links()
        
        if links:
            print(f"✓ 找到 {len(links)} 个第一层链接")
            
            # 只测试前2个链接
            test_links = links[:2]
            
            for i, link in enumerate(test_links, 1):
                print(f"\n测试链接 {i}: {link['text']}")
                
                try:
                    # 测试第二层页面访问
                    downloaded_files = crawler.crawl_second_level(link)
                    
                    if downloaded_files:
                        print(f"✓ 成功下载 {len(downloaded_files)} 个文件")
                    else:
                        print("⚠ 未找到可下载文件")
                        
                except Exception as e:
                    print(f"✗ 处理链接时出错: {e}")
        else:
            print("✗ 未找到任何链接")
        
        print("\n" + "="*50)
        print("快速测试完成!")
        print("="*50)
        
    except Exception as e:
        print(f"✗ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'crawler' in locals() and crawler.driver:
            crawler.close()

if __name__ == "__main__":
    quick_test()