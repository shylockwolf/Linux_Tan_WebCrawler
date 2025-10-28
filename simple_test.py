#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试爬虫功能
"""

import os
import sys
import time

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """测试基本功能"""
    print("开始测试爬虫基本功能...")
    
    try:
        # 导入爬虫类
        from web_crawler import LevelNoticeCrawler
        
        # 创建爬虫实例
        print("正在初始化爬虫...")
        crawler = LevelNoticeCrawler()
        print("✓ 爬虫初始化成功")
        
        # 测试访问网站
        print("正在访问目标网站...")
        crawler.driver.get(crawler.base_url)
        time.sleep(5)  # 等待页面加载
        
        # 检查页面状态
        title = crawler.driver.title
        current_url = crawler.driver.current_url
        print(f"✓ 网站访问成功")
        print(f"  页面标题: {title}")
        print(f"  当前URL: {current_url}")
        
        # 测试查找链接
        print("\n正在查找第一层链接...")
        links = crawler.get_first_level_links()
        
        if links:
            print(f"✓ 找到 {len(links)} 个第一层链接")
            
            # 显示前3个链接
            print("\n前3个链接:")
            for i, link in enumerate(links[:3], 1):
                print(f"  {i}. {link['text']}")
                print(f"     URL: {link['url']}")
            
            # 测试第一个链接
            if len(links) > 0:
                print(f"\n测试第一个链接: {links[0]['text']}")
                try:
                    downloaded_files = crawler.crawl_second_level(links[0])
                    if downloaded_files:
                        print(f"✓ 成功下载 {len(downloaded_files)} 个文件")
                    else:
                        print("⚠ 未找到可下载文件")
                except Exception as e:
                    print(f"✗ 处理链接时出错: {e}")
        else:
            print("✗ 未找到任何链接")
        
        print("\n" + "="*60)
        print("测试完成!")
        print("="*60)
        
    except Exception as e:
        print(f"✗ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保关闭浏览器
        if 'crawler' in locals():
            try:
                crawler.close()
                print("✓ 浏览器已关闭")
            except:
                pass

if __name__ == "__main__":
    test_basic_functionality()