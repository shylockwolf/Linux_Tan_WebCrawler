#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫配置文件
"""

# 目标网站配置
TARGET_URL = "https://ydydj.univsport.com/level/Levelnotice"

# 下载配置
DOWNLOAD_DIR = "downloads"
MAX_RETRIES = 3
RETRY_DELAY = 2

# 浏览器配置
HEADLESS = True  # 是否使用无头模式
WINDOW_SIZE = "1920,1080"
PAGE_LOAD_TIMEOUT = 30
IMPLICIT_WAIT = 10

# 文件类型配置
DOWNLOADABLE_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.ppt', '.pptx', '.zip', '.rar', '.7z',
    '.txt', '.csv', '.jpg', '.jpeg', '.png', '.gif'
]

# 链接选择器配置
LINK_SELECTORS = [
    "a[href]",           # 所有链接
    "button",             # 按钮
    ".link",              # 链接类
    ".btn",               # 按钮类
    "[onclick]",         # 点击事件
    "[class*='menu']",   # 菜单类
    "[class*='nav']",    # 导航类
    "[class*='tab']",    # 标签类
]

# 下载链接选择器配置
DOWNLOAD_SELECTORS = [
    "a[href*='.pdf']",
    "a[href*='.doc']", 
    "a[href*='.xls']",
    "a[href*='.zip']",
    "a[href*='.rar']",
    "a[download]",
    "[class*='download']",
    "[class*='file']",
]

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}