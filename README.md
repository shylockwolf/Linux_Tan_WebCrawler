# 运动员技术等级查询网站爬虫

这是一个用于爬取运动员技术等级查询网站（https://ydydj.univsport.com/level/Levelnotice）的Python爬虫程序。

## 功能特点

- ✅ 自动识别和点击第一层链接
- ✅ 进入第二层页面查找可下载文件
- ✅ 支持多种文件格式下载（PDF、Word、Excel、压缩包等）
- ✅ 智能文件命名和分类存储
- ✅ 处理JavaScript动态渲染的单页应用
- ✅ 错误处理和重试机制

## 文件结构

```
Linux_Tan_WebCrawler/
├── web_crawler.py          # 主爬虫程序
├── test_crawler.py         # 网站结构测试工具
├── config.py               # 配置文件
├── requirements.txt        # Python依赖包
└── downloads/              # 下载文件目录（自动创建）
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 测试网站结构（推荐先运行）

```bash
python test_crawler.py
```

这个工具会打开浏览器显示网站，分析页面结构，并生成截图。

### 2. 运行主爬虫程序

```bash
python web_crawler.py
```

爬虫会自动：
- 访问目标网站
- 查找所有第一层链接
- 依次点击每个链接进入第二层页面
- 在第二层页面中查找可下载文件
- 下载文件到本地 `downloads/` 目录

### 3. 查看下载结果

下载的文件会按第一层链接的名称分类存储：
```
downloads/
├── 公告通知/
│   ├── 2024年运动员等级评定通知.pdf
│   └── 技术等级标准.docx
├── 政策法规/
│   └── 运动员技术等级管理办法.pdf
└── ...
```

## 配置选项

在 `config.py` 中可以修改以下配置：

- `HEADLESS`: 是否使用无头模式（True/False）
- `DOWNLOADABLE_EXTENSIONS`: 可下载的文件类型
- `PAGE_LOAD_TIMEOUT`: 页面加载超时时间
- 其他浏览器和请求参数

## 技术说明

- 使用 **Selenium** 处理JavaScript动态渲染
- 使用 **requests** 进行文件下载
- 支持多种链接识别方式（a标签、按钮、onclick事件等）
- 自动处理相对URL和绝对URL
- 文件名清理和非法字符过滤

## 注意事项

1. **首次运行**需要下载Chrome驱动，请确保网络连接正常
2. 如果网站结构复杂，建议先运行测试工具了解页面布局
3. 下载速度受网络和服务器响应影响
4. 请遵守网站的robots.txt和使用条款

## 故障排除

### 常见问题

1. **Chrome驱动下载失败**
   - 检查网络连接
   - 手动安装Chrome浏览器

2. **找不到链接**
   - 运行测试工具检查网站结构
   - 调整config.py中的选择器配置

3. **下载失败**
   - 检查网络连接
   - 确认文件链接有效
   - 查看错误日志

## 许可证

本项目仅供学习和研究使用。