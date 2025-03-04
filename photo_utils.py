from pathlib import Path
from PIL import Image
import config

THUMB_SIZE = (400, 400)


def get_photo_structure(root_path):
    root = Path(root_path)
    structure = {}
    for year_dir in sorted(root.iterdir(), reverse=True):
        if year_dir.is_dir() and year_dir.name.isdigit():
            year = year_dir.name
            structure[year] = {}
            for month_dir in sorted(year_dir.iterdir()):
                if month_dir.is_dir() and month_dir.name.isdigit():
                    month = month_dir.name
                    structure[year][month] = [
                        day.name for day in month_dir.iterdir()
                        if day.is_dir() and day.name.isdigit()
                    ]
    return structure


def get_day_photos(day_path, photo_root):
    photos = []
    for file in day_path.iterdir():
        if file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            thumb_path = generate_thumbnail(file, photo_root)
            original_rel = file.relative_to(photo_root)  # 相对于PHOTO_ROOT的路径
            photos.append({
                'original': original_rel.as_posix(),  # 转换为字符串路径
                'thumbnail': thumb_path
            })
    return photos


def generate_thumbnail(image_path, photo_root):
    if not image_path.exists():
        raise FileNotFoundError(f"原始图片不存在: {image_path}")

    # 构建相对于当前工作目录的缩略图目录路径
    thumb_dir = Path.cwd() / 'static' / 'thumbnails' / image_path.parent.relative_to(photo_root)

    # 验证路径是否在项目目录内
    try:
        thumb_dir.resolve().relative_to(Path.cwd())
    except ValueError:
        raise RuntimeError(f"非法路径访问: {thumb_dir}")

    thumb_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = thumb_dir / image_path.name

    if not thumb_path.exists():
        img = Image.open(image_path)
        img.thumbnail(THUMB_SIZE)
        img.save(thumb_path)

    static_dir = Path.cwd() / 'static'
    thumb_rel = thumb_path.relative_to(static_dir)
    return thumb_rel.as_posix()

