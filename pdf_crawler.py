#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF文件爬虫程序 - 专门针对第二层网页的PDF下载
目标网站：https://ydydj.univsport.com/level/Levelnotice
"""

import os
import time
import requests
import re
from urllib.parse import urljoin, urlparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PDFCrawler:
    def __init__(self):
        self.base_url = "https://ydydj.univsport.com"
        self.target_url = "https://ydydj.univsport.com/level/Levelnotice"
        self.download_dir = "pdf_downloads"
        self.setup_download_dir()
        
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def setup_download_dir(self):
        """创建下载目录"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            logger.info(f"创建PDF下载目录: {self.download_dir}")
    
    def get_first_level_links(self):
        """获取第一层页面的所有链接"""
        logger.info("正在获取第一层页面链接...")
        
        try:
            response = self.session.get(self.target_url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"第一层页面访问失败，状态码: {response.status_code}")
                return []
            
            html_content = response.text
            
            # 保存第一层页面内容
            with open(os.path.join(self.download_dir, 'first_level.html'), 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 提取所有链接
            links = re.findall(r'href="([^"]+)"', html_content)
            logger.info(f"找到 {len(links)} 个链接")
            
            # 过滤出第二层页面的链接
            second_level_links = []
            for link in links:
                # 过滤条件：排除空链接、JavaScript链接、外部链接
                if (link and 
                    not link.startswith('#') and 
                    not link.startswith('javascript:') and
                    not link.startswith('mailto:') and
                    'ydydj.univsport.com' in link or link.startswith('/')):
                    
                    # 构建完整URL
                    if link.startswith('/'):
                        full_url = urljoin(self.base_url, link)
                    else:
                        full_url = link
                    
                    # 排除当前页面
                    if full_url != self.target_url:
                        second_level_links.append(full_url)
            
            # 去重
            second_level_links = list(set(second_level_links))
            logger.info(f"过滤后得到 {len(second_level_links)} 个第二层页面链接")
            
            # 显示前几个链接
            for i, link in enumerate(second_level_links[:5]):
                logger.info(f"第二层链接 {i+1}: {link}")
            
            return second_level_links
            
        except Exception as e:
            logger.error(f"获取第一层链接失败: {e}")
            return []
    
    def crawl_second_level_pages(self, second_level_links):
        """爬取第二层页面并下载PDF文件"""
        logger.info("开始爬取第二层页面...")
        
        total_pdfs_downloaded = 0
        
        for i, page_url in enumerate(second_level_links):
            logger.info(f"处理第 {i+1}/{len(second_level_links)} 个第二层页面: {page_url}")
            
            try:
                # 访问第二层页面
                response = self.session.get(page_url, timeout=10)
                
                if response.status_code != 200:
                    logger.warning(f"页面访问失败: {page_url}, 状态码: {response.status_code}")
                    continue
                
                html_content = response.text
                
                # 保存第二层页面内容
                page_filename = f"second_level_{i+1}.html"
                with open(os.path.join(self.download_dir, page_filename), 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # 查找PDF文件链接
                pdf_links = self.find_pdf_links(html_content, page_url)
                
                if pdf_links:
                    logger.info(f"在页面 {page_url} 中找到 {len(pdf_links)} 个PDF文件")
                    
                    # 下载PDF文件
                    downloaded_count = self.download_pdfs(pdf_links, page_url, i+1)
                    total_pdfs_downloaded += downloaded_count
                else:
                    logger.info(f"页面 {page_url} 中没有找到PDF文件")
                
                # 添加延迟，避免请求过快
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"处理第二层页面失败 {page_url}: {e}")
                continue
        
        return total_pdfs_downloaded
    
    def find_pdf_links(self, html_content, page_url):
        """在HTML内容中查找PDF文件链接"""
        pdf_links = []
        
        # 方法1: 直接查找PDF链接
        pdf_patterns = [
            r'href="([^"]+\.pdf)"',
            r'src="([^"]+\.pdf)"',
            r'download="([^"]+\.pdf)"',
        ]
        
        for pattern in pdf_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # 构建完整URL
                if match.startswith('http'):
                    full_url = match
                else:
                    full_url = urljoin(page_url, match)
                
                if full_url not in pdf_links:
                    pdf_links.append(full_url)
        
        # 方法2: 查找包含"pdf"关键词的链接
        all_links = re.findall(r'href="([^"]+)"', html_content)
        for link in all_links:
            if '.pdf' in link.lower() or 'pdf' in link.lower():
                # 构建完整URL
                if link.startswith('http'):
                    full_url = link
                else:
                    full_url = urljoin(page_url, link)
                
                if full_url not in pdf_links:
                    pdf_links.append(full_url)
        
        # 方法3: 查找下载链接
        download_links = re.findall(r'href="([^"]+)"[^>]*download', html_content)
        for link in download_links:
            # 构建完整URL
            if link.startswith('http'):
                full_url = link
            else:
                full_url = urljoin(page_url, link)
            
            if full_url not in pdf_links:
                pdf_links.append(full_url)
        
        return pdf_links
    
    def download_pdfs(self, pdf_links, page_url, page_num):
        """下载PDF文件"""
        downloaded_count = 0
        
        for j, pdf_url in enumerate(pdf_links):
            try:
                logger.info(f"正在下载PDF: {pdf_url}")
                
                response = self.session.get(pdf_url, timeout=30, stream=True)
                
                if response.status_code == 200:
                    # 检查内容类型
                    content_type = response.headers.get('content-type', '')
                    
                    if 'pdf' in content_type.lower() or pdf_url.lower().endswith('.pdf'):
                        # 生成文件名
                        filename = self.generate_pdf_filename(pdf_url, page_num, j+1)
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
                            downloaded_count += 1
                        else:
                            logger.warning(f"PDF文件太小，可能无效: {filename}")
                            os.remove(file_path)
                    else:
                        logger.warning(f"链接不是PDF文件: {pdf_url}, 内容类型: {content_type}")
                else:
                    logger.warning(f"PDF下载失败: {pdf_url}, 状态码: {response.status_code}")
                
            except Exception as e:
                logger.error(f"PDF下载失败 {pdf_url}: {e}")
        
        return downloaded_count
    
    def generate_pdf_filename(self, pdf_url, page_num, pdf_num):
        """生成PDF文件名"""
        # 从URL提取文件名
        basename = os.path.basename(urlparse(pdf_url).path)
        
        if not basename or basename == 'pdf' or '.' not in basename:
            # 如果无法从URL获取有效文件名，使用编号
            basename = f"page_{page_num}_pdf_{pdf_num}.pdf"
        elif not basename.lower().endswith('.pdf'):
            # 确保文件扩展名正确
            basename += '.pdf'
        
        # 清理文件名
        safe_name = "".join(c for c in basename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        
        return safe_name
    
    def crawl(self):
        """执行爬虫任务"""
        logger.info("开始PDF爬虫任务...")
        
        # 1. 获取第一层页面链接
        second_level_links = self.get_first_level_links()
        
        if not second_level_links:
            logger.warning("未找到第二层页面链接")
            return
        
        # 2. 爬取第二层页面并下载PDF
        total_pdfs = self.crawl_second_level_pages(second_level_links)
        
        # 3. 统计结果
        logger.info("=" * 50)
        logger.info(f"爬虫任务完成!")
        logger.info(f"处理了 {len(second_level_links)} 个第二层页面")
        logger.info(f"成功下载 {total_pdfs} 个PDF文件")
        logger.info(f"文件保存在: {self.download_dir}")
        
        # 显示下载的文件列表
        if os.path.exists(self.download_dir):
            files = os.listdir(self.download_dir)
            pdf_files = [f for f in files if f.lower().endswith('.pdf')]
            if pdf_files:
                logger.info("下载的PDF文件:")
                for pdf_file in pdf_files:
                    file_path = os.path.join(self.download_dir, pdf_file)
                    file_size = os.path.getsize(file_path)
                    logger.info(f"  - {pdf_file} ({file_size} 字节)")

def main():
    """主函数"""
    crawler = PDFCrawler()
    crawler.crawl()

if __name__ == "__main__":
    main()