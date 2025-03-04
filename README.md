# 照片图库项目

基于Flask和Tailwind CSS构建的现代化照片展示系统，支持自动目录解析、瀑布流布局和懒加载功能。

## 功能特性

✅ 自动解析年/月/日目录结构  
✅ 响应式网格布局（支持移动端）  
✅ 智能缩略图生成系统  
✅ 图片懒加载优化  
✅ 点击查看大图模态框  
✅ EXIF信息保留  
✅ 安全文件传输  

## 快速开始

### 环境要求
- Python 3.12+
- Pillow 图像处理库

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/Athenavi/photo-gallery.git
cd photo-gallery

# 安装依赖
pip install -r requirements.txt

# 创建照片目录（按需修改config.py）
mkdir -p photos/2023/12/31  # 示例目录结构

```

### 配置参数 config.py
```
PHOTO_ROOT = "./photos"  # 指向您的照片根目录
```

### 目录机构规范
```
照片根目录/
├── 2023/
│   ├── 01/  # 月份(两位数)
│   │   ├── 01/  # 日期(两位数)
│   │   │   ├── IMG_001.jpg
│   │   │   └── IMG_002.jpg
│   │   └── 02/
├── 2024/
```



### 运行项目

```bash
# 启动项目
flask run --host=0.0.0.0 --port=5000
```

## 高级功能
- 自动生成400px缩略图（存放于static/thumbnails）
- 支持JPG/PNG格式文件
- 浏览器本地缓存优化

## 贡献指南
1. 提交Issue说明问题或建议
2. Fork仓库并创建特性分支
3. 提交Pull Request时关联相关Issue
