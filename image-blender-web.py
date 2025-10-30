import os
import uuid
from io import BytesIO

import numpy as np
import requests
from PIL import Image, UnidentifiedImageError
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def download_image(url):
    """从URL下载图片并进行验证"""
    try:
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()

        # 检查内容类型
        content_type = response.headers.get('content-type', '').lower()
        if not content_type.startswith('image/'):
            raise ValueError(f"URL返回的不是图片，内容类型: {content_type}")

        # 验证图片数据
        image_data = BytesIO(response.content)

        # 尝试打开图片
        try:
            img = Image.open(image_data)
            # 验证图片可以正常读取
            img.verify()
        except UnidentifiedImageError:
            raise ValueError("无法识别图片格式，可能不是有效的图片文件")
        except Exception as e:
            raise ValueError(f"图片格式错误: {str(e)}")

        # 重新打开图片（因为verify()会关闭图片）
        image_data.seek(0)
        return Image.open(image_data)

    except requests.exceptions.RequestException as e:
        raise ValueError(f"下载图片失败: {str(e)}")
    except Exception as e:
        raise ValueError(f"处理图片时出错: {str(e)}")


def process_uploaded_file(file):
    """处理上传的文件"""
    if not file or not file.filename:
        raise ValueError("没有选择文件")

    # 检查文件扩展名
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        raise ValueError(f"不支持的图片格式。支持: {', '.join(allowed_extensions)}")

    try:
        # 读取文件数据
        file_data = BytesIO(file.read())
        file.seek(0)  # 重置文件指针，以便后续使用

        # 验证图片
        img = Image.open(file_data)
        img.verify()

        # 重新打开图片
        file_data.seek(0)
        return Image.open(file_data)
    except UnidentifiedImageError:
        raise ValueError("无法识别图片格式，请确保是有效的图片文件")
    except Exception as e:
        raise ValueError(f"图片文件损坏或格式不支持: {str(e)}")


def blend_images(base_img, overlay_img, blend_mode, center_percentage=0.3):
    """融合两张图片"""
    # 确保两张图片尺寸相同
    if base_img.size != overlay_img.size:
        overlay_img = overlay_img.resize(base_img.size, Image.Resampling.LANCZOS)

    # 转换为RGBA模式以支持透明度
    if base_img.mode != 'RGBA':
        base_img = base_img.convert('RGBA')
    if overlay_img.mode != 'RGBA':
        overlay_img = overlay_img.convert('RGBA')

    # 转换为numpy数组
    base_array = np.array(base_img)
    overlay_array = np.array(overlay_img)

    # 创建结果数组
    result_array = base_array.copy()
    width, height = base_img.size

    if blend_mode == 1:  # 上半部分融合
        blend_height = height // 2
        for y in range(blend_height):
            alpha = smoothstep(y / blend_height)
            for x in range(width):
                result_array[y, x] = blend_pixels_np(base_array[y, x], overlay_array[y, x], alpha)

    elif blend_mode == 2:  # 下半部分融合
        blend_height = height // 2
        blend_start = height - blend_height
        for y in range(blend_start, height):
            alpha = smoothstep((y - blend_start) / blend_height)
            for x in range(width):
                result_array[y, x] = blend_pixels_np(base_array[y, x], overlay_array[y, x], alpha)

    elif blend_mode == 3:  # 左半部分融合
        blend_width = width // 2
        for x in range(blend_width):
            alpha = smoothstep(x / blend_width)
            for y in range(height):
                result_array[y, x] = blend_pixels_np(base_array[y, x], overlay_array[y, x], alpha)

    elif blend_mode == 4:  # 右半部分融合
        blend_width = width // 2
        blend_start = width - blend_width
        for x in range(blend_start, width):
            alpha = smoothstep((x - blend_start) / blend_width)
            for y in range(height):
                result_array[y, x] = blend_pixels_np(base_array[y, x], overlay_array[y, x], alpha)

    elif blend_mode == 5:  # 左右融合，保留中间
        center_width = int(width * center_percentage)
        left_blend_width = (width - center_width) // 2
        right_blend_start = left_blend_width + center_width

        # 创建融合遮罩
        blend_mask = np.ones((height, width), dtype=np.float32)

        # 左侧渐变区域
        if left_blend_width > 0:
            for x in range(left_blend_width):
                alpha = smoothstep(x / left_blend_width)
                blend_mask[:, x] = alpha

        # 中间区域完全显示表层图
        blend_mask[:, left_blend_width:right_blend_start] = 1.0

        # 右侧渐变区域
        if right_blend_start < width:
            right_blend_width = width - right_blend_start
            for x in range(right_blend_start, width):
                alpha = smoothstep(1 - (x - right_blend_start) / right_blend_width)
                blend_mask[:, x] = alpha

        # 应用融合
        for y in range(height):
            for x in range(width):
                result_array[y, x] = blend_pixels_np(base_array[y, x], overlay_array[y, x], blend_mask[y, x])

    return Image.fromarray(result_array.astype(np.uint8), 'RGBA')


def smoothstep(x):
    """平滑过渡函数"""
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def blend_pixels_np(base_pixel, overlay_pixel, alpha):
    """混合两个像素"""
    result = (1 - alpha) * base_pixel + alpha * overlay_pixel
    return result.astype(np.uint8)


@app.route('/')
def index():
    return render_template('image-blender/index.html')


@app.route('/blend', methods=['POST'])
def blend():
    try:
        # 获取表单数据
        blend_mode = int(request.form.get('blend_mode', 1))
        center_percentage = float(request.form.get('center_percentage', 0.3))

        # 处理底图
        base_input_type = request.form.get('base_input_type', 'upload')
        if base_input_type == 'upload':
            if 'base_image' not in request.files:
                return jsonify({'error': '请选择底图文件'}), 400
            base_file = request.files['base_image']
            base_img = process_uploaded_file(base_file)
        else:  # URL
            base_url = request.form.get('base_url', '').strip()
            if not base_url:
                return jsonify({'error': '请输入底图URL'}), 400
            base_img = download_image(base_url)

        # 处理表层图
        overlay_input_type = request.form.get('overlay_input_type', 'upload')
        if overlay_input_type == 'upload':
            if 'overlay_image' not in request.files:
                return jsonify({'error': '请选择表层图文件'}), 400
            overlay_file = request.files['overlay_image']
            overlay_img = process_uploaded_file(overlay_file)
        else:  # URL
            overlay_url = request.form.get('overlay_url', '').strip()
            if not overlay_url:
                return jsonify({'error': '请输入表层图URL'}), 400
            overlay_img = download_image(overlay_url)

        # 执行图片融合
        result_img = blend_images(base_img, overlay_img, blend_mode, center_percentage)

        # 保存结果图片
        output_filename = f"{uuid.uuid4().hex}.png"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        result_img.save(output_path, 'PNG')

        return jsonify({
            'success': True,
            'result_url': f"/static/uploads/{output_filename}"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cleanup', methods=['POST'])
def cleanup():
    """清理上传的临时文件"""
    try:
        count = 0
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
                count += 1
        return jsonify({'success': True, 'message': f'已清理 {count} 个文件'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/validate_url', methods=['POST'])
def validate_url():
    """验证URL是否有效"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()

        if not url:
            return jsonify({'valid': False, 'message': 'URL不能为空'})

        # 简单URL格式验证
        if not url.startswith(('http://', 'https://')):
            return jsonify({'valid': False, 'message': 'URL必须以 http:// 或 https:// 开头'})

        # 尝试下载图片但不保存
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.head(url, timeout=5, headers=headers, allow_redirects=True)
        content_type = response.headers.get('content-type', '').lower()

        if not content_type.startswith('image/'):
            return jsonify({'valid': False, 'message': f'URL指向的不是图片文件 (Content-Type: {content_type})'})

        return jsonify({'valid': True, 'message': 'URL有效'})

    except requests.exceptions.RequestException as e:
        return jsonify({'valid': False, 'message': f'无法访问URL: {str(e)}'})
    except Exception as e:
        return jsonify({'valid': False, 'message': f'验证失败: {str(e)}'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
