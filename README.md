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

# PhotoFusion

PhotoFusion是一个基于Python的图片融合脚本，可以实现两张图片的不同融合方式：

1. **安装依赖**：

```bash
pip install Pillow numpy
```

2. **命令行使用**：

```bash
# 上半部分融合
python PhotoFusion.py base.jpg overlay.jpg --mode 1 --output result1.png

# 下半部分融合  
python PhotoFusion.py base.jpg overlay.jpg --mode 2 --output result2.png

# 左半部分融合
python PhotoFusion.py base.jpg overlay.jpg --mode 3 --output result3.png

# 右半部分融合
python PhotoFusion.py base.jpg overlay.jpg --mode 4 --output result4.png

# 左右融合保留中间（保留30%中间区域）
python PhotoFusion.py base.jpg overlay.jpg --mode 5 --percentage 0.3 --output result5.png
```

功能特点：

- 支持5种不同的融合模式
- 模式5可以自定义中间保留区域的百分比
- 自动调整图片尺寸匹配（建议使用相同分辨率）
- 使用平滑的透明度渐变，效果自然
- 支持PNG透明背景图片

注意事项：

- 确保两张图片路径正确
- 百分比参数只在模式5中有效
- 输出格式支持常见图片格式（PNG、JPG等）

# archive.py

## 图片归档分类系统 (Image Archive Classifier)

这是一个基于 Flask 的图片归档分类 Web 应用，用于帮助用户按照时间维度（年份、月份、日期）自动扫描和手动分类本地文件夹中的图片文件，并将图片移动到相应的分类文件夹中。

## 主要功能

### 1. 图片扫描

- 支持扫描指定文件夹及其子文件夹中的所有图片文件
- 支持的图片格式：JPG, JPEG, PNG, GIF, BMP, WEBP, TIFF, TIF
- 自动获取图片的文件大小和最后修改时间 photo-gallery

### 2. 多种分类级别

系统支持以下五种时间分类级别：

- **year（年份）**：按年份分类（如：2023）
- **month（年-月）**：按年月分类（如：2023-01）
- **date（完整日期）**：按完整日期分类（如：2023-01-15）
- **only_month（仅月份）**：仅按月份分类（如：01）
- **only_date（仅日期）**：仅按日期分类（如：15） photo-gallery

### 3. 图片分类流程

1. 选择文件夹并设定分类级别
2. 系统自动扫描图片并生成可用分类
3. 用户选择需要的分类目录
4. 逐个查看图片并进行分类标记
5. 确认后批量移动图片到对应分类文件夹

## 安装要求

```bash
pip install flask flask-cors
```

## 启动方式

```bash
python archive.py
```