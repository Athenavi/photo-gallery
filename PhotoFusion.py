import argparse

import numpy as np
from PIL import Image


def blend_images(base_img_path, overlay_img_path, blend_mode, center_percentage=0.3):
    """
    融合两张图片

    参数:
    base_img_path: 底图路径
    overlay_img_path: 表层图路径
    blend_mode: 融合模式 (1-上半部分, 2-下半部分, 3-左半部分, 4-右半部分, 5-左右融合保留中间)
    center_percentage: 模式5中保留中间区域的百分比 (0-1)
    """

    # 打开图片并转换为RGBA模式（支持透明度）
    base_img = Image.open(base_img_path).convert('RGBA')
    overlay_img = Image.open(overlay_img_path).convert('RGBA')

    # 确保两张图片尺寸相同
    if base_img.size != overlay_img.size:
        overlay_img = overlay_img.resize(base_img.size, Image.Resampling.LANCZOS)

    # 转换为numpy数组以提高性能
    base_array = np.array(base_img)
    overlay_array = np.array(overlay_img)

    # 创建结果数组
    result_array = base_array.copy()
    width, height = base_img.size

    if blend_mode == 1:  # 上半部分融合
        blend_height = height // 2
        for y in range(blend_height):
            # 使用平滑的渐变函数
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
                # 使用平滑的渐变，从0到1
                alpha = smoothstep(x / left_blend_width)
                blend_mask[:, x] = alpha

        # 中间区域完全显示表层图
        blend_mask[:, left_blend_width:right_blend_start] = 1.0

        # 右侧渐变区域
        if right_blend_start < width:
            right_blend_width = width - right_blend_start
            for x in range(right_blend_start, width):
                # 使用平滑的渐变，从1到0
                alpha = smoothstep(1 - (x - right_blend_start) / right_blend_width)
                blend_mask[:, x] = alpha

        # 应用融合
        for y in range(height):
            for x in range(width):
                result_array[y, x] = blend_pixels_np(base_array[y, x], overlay_array[y, x], blend_mask[y, x])

    # 转换回PIL图像
    result_img = Image.fromarray(result_array.astype(np.uint8), 'RGBA')
    return result_img


def smoothstep(x):
    """平滑过渡函数，消除硬边界"""
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def blend_pixels_np(base_pixel, overlay_pixel, alpha):
    """使用numpy数组混合两个像素，alpha控制混合程度 (0-1)"""
    # 使用alpha混合公式
    result = (1 - alpha) * base_pixel + alpha * overlay_pixel
    return result.astype(np.uint8)


def blend_pixels(base_pixel, overlay_pixel, alpha):
    """混合两个像素，alpha控制混合程度 (0-1)"""
    r1, g1, b1, a1 = base_pixel
    r2, g2, b2, a2 = overlay_pixel

    # 使用alpha混合公式
    r = int(r1 * (1 - alpha) + r2 * alpha)
    g = int(g1 * (1 - alpha) + g2 * alpha)
    b = int(b1 * (1 - alpha) + b2 * alpha)
    a = int(a1 * (1 - alpha) + a2 * alpha)

    return (r, g, b, a)


def main():
    parser = argparse.ArgumentParser(description='图片融合工具')
    parser.add_argument('base_image', help='底图路径')
    parser.add_argument('overlay_image', help='表层图路径')
    parser.add_argument('--mode', type=int, choices=[1, 2, 3, 4, 5], required=True,
                        help='融合模式: 1-上半部分, 2-下半部分, 3-左半部分, 4-右半部分, 5-左右融合保留中间')
    parser.add_argument('--output', default='blended_result.png', help='输出图片路径')
    parser.add_argument('--percentage', type=float, default=0.3,
                        help='模式5中保留中间区域的百分比 (0-1)，默认0.3')

    args = parser.parse_args()

    try:
        result = blend_images(args.base_image, args.overlay_image,
                              args.mode, args.percentage)
        result.save(args.output)
        print(f"图片融合完成！结果已保存到: {args.output}")
    except Exception as e:
        print(f"处理图片时出错: {e}")


if __name__ == "__main__":
    main()
