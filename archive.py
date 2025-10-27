import os
import shutil
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 启用CORS以便本地访问
CORS(app)

# 存储用户会话数据
user_sessions = {}


class ImageClassifier:
    def __init__(self):
        self.current_session = None

    def create_session(self):
        session_id = str(uuid.uuid4())
        user_sessions[session_id] = {
            'step': 1,
            'folder_path': '',
            'level': '',
            'selected_categories': [],
            'images': [],
            'classifications': {},
            'current_image_index': 0
        }
        return session_id

    def get_session(self, session_id):
        return user_sessions.get(session_id)

    def update_session(self, session_id, updates):
        if session_id in user_sessions:
            user_sessions[session_id].update(updates)
            return True
        return False


classifier = ImageClassifier()


@app.route('/')
def index():
    session_id = classifier.create_session()
    return render_template('archive-index.html', session_id=session_id)


@app.route('/api/select-folder', methods=['POST'])
def select_folder():
    session_id = request.json.get('session_id')
    folder_path = request.json.get('folder_path')
    level = request.json.get('level')

    print(f"选择文件夹: {folder_path}, 等级: {level}")

    if not folder_path or not level:
        return jsonify({'error': '缺少必要参数'}), 400

    # 验证文件夹是否存在
    if not os.path.exists(folder_path):
        return jsonify({'error': '文件夹不存在'}), 400

    # 扫描图片文件
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
    images = []

    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_ext = os.path.splitext(file.lower())[1]
                if file_ext in image_extensions:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        images.append({
                            'id': str(uuid.uuid4()),
                            'name': file,
                            'path': file_path,
                            'relative_path': os.path.relpath(file_path, folder_path),
                            'size': stat.st_size,
                            'last_modified': stat.st_mtime
                        })
                    except Exception as e:
                        print(f"无法访问文件 {file_path}: {e}")
                        continue
    except Exception as e:
        return jsonify({'error': f'扫描文件夹时出错: {str(e)}'}), 400

    if not images:
        return jsonify({'error': '文件夹中没有找到图片文件'}), 400

    # 根据等级提取可能的分类
    categories = set()
    for image in images:
        try:
            mod_time = datetime.fromtimestamp(image['last_modified'])

            if level == 'year':
                categories.add(str(mod_time.year))
            elif level == 'month':
                categories.add(f"{mod_time.year}-{mod_time.month:02d}")
            elif level == 'date':
                categories.add(f"{mod_time.year}-{mod_time.month:02d}-{mod_time.day:02d}")
            elif level == 'only_month':
                categories.add(f"{mod_time.month:02d}")
            elif level == 'only_date':
                categories.add(f"{mod_time.day:02d}")
        except Exception as e:
            print(f"处理文件 {image['name']} 的时间信息时出错: {e}")

    # 更新会话
    classifier.update_session(session_id, {
        'step': 2,
        'folder_path': folder_path,
        'level': level,
        'images': images,
        'available_categories': sorted(list(categories))
    })

    return jsonify({
        'success': True,
        'image_count': len(images),
        'available_categories': sorted(list(categories))
    })


@app.route('/api/validate-folder', methods=['POST'])
def validate_folder():
    data = request.get_json()
    folder_path = data.get('folder_path')
    session_id = data.get('session_id')

    if not folder_path:
        return jsonify({'success': False, 'error': '文件夹路径不能为空'})

    try:
        # 检查路径是否存在
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': '文件夹路径不存在'})

        if not os.path.isdir(folder_path):
            return jsonify({'success': False, 'error': '路径不是文件夹'})

        # 扫描图片文件
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
        image_files = []

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    relative_path = os.path.relpath(os.path.join(root, file), folder_path)
                    image_files.append(relative_path)

        if not image_files:
            return jsonify({'success': False, 'error': '文件夹中没有找到图片文件'})

        # 返回预览文件列表（前10个）
        preview_files = image_files[:10]

        return jsonify({
            'success': True,
            'image_count': len(image_files),
            'preview_files': preview_files
        })

    except PermissionError:
        return jsonify({'success': False, 'error': '没有权限访问该文件夹'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'访问文件夹时出错: {str(e)}'})


@app.route('/api/select-categories', methods=['POST'])
def select_categories():
    session_id = request.json.get('session_id')
    selected_categories = request.json.get('selected_categories', [])

    session = classifier.get_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 400

    # 创建分类文件夹
    base_path = session['folder_path']
    for category in selected_categories:
        category_path = os.path.join(base_path, category)
        os.makedirs(category_path, exist_ok=True)

    classifier.update_session(session_id, {
        'step': 3,
        'selected_categories': selected_categories,
        'current_image_index': 0
    })

    return jsonify({'success': True})


@app.route('/api/get-next-image', methods=['POST'])
def get_next_image():
    session_id = request.json.get('session_id')
    session = classifier.get_session(session_id)

    if not session:
        return jsonify({'error': '会话不存在'}), 400

    current_index = session.get('current_image_index', 0)
    images = session.get('images', [])

    if current_index >= len(images):
        return jsonify({'done': True})

    image = images[current_index]

    return jsonify({
        'image': {
            'id': image['id'],
            'name': image['name'],
            'path': image['path'],
            'size': image['size']
        },
        'current_index': current_index,
        'total_count': len(images),
        'done': False
    })


@app.route('/api/image/<session_id>/<image_id>')
def get_image(session_id, image_id):
    session = classifier.get_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 404

    # 在会话中查找图片
    image = None
    for img in session.get('images', []):
        if img['id'] == image_id:
            image = img
            break

    if not image or not os.path.exists(image['path']):
        return jsonify({'error': '图片不存在'}), 404

    # 返回图片文件
    return send_file(image['path'], as_attachment=False)


@app.route('/api/classify-image', methods=['POST'])
def classify_image():
    session_id = request.json.get('session_id')
    category = request.json.get('category')

    session = classifier.get_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 400

    current_index = session.get('current_image_index', 0)
    images = session.get('images', [])

    if current_index < len(images):
        image_id = images[current_index]['id']
        session['classifications'][image_id] = category

        # 更新索引
        classifier.update_session(session_id, {
            'current_image_index': current_index + 1
        })

    return jsonify({'success': True})


@app.route('/api/update-classification', methods=['POST'])
def update_classification():
    session_id = request.json.get('session_id')
    image_id = request.json.get('image_id')
    category = request.json.get('category')

    session = classifier.get_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 400

    session['classifications'][image_id] = category
    return jsonify({'success': True})


@app.route('/api/get-classifications', methods=['POST'])
def get_classifications():
    session_id = request.json.get('session_id')
    session = classifier.get_session(session_id)

    if not session:
        return jsonify({'error': '会话不存在'}), 400

    classifications = []
    for image in session.get('images', []):
        classifications.append({
            'id': image['id'],
            'name': image['name'],
            'path': image['path'],
            'category': session['classifications'].get(image['id'], '未分类')
        })

    return jsonify({
        'classifications': classifications,
        'total_count': len(classifications)
    })


@app.route('/api/execute-move', methods=['POST'])
def execute_move():
    session_id = request.json.get('session_id')
    session = classifier.get_session(session_id)

    if not session:
        return jsonify({'error': '会话不存在'}), 400

    base_path = session['folder_path']
    classifications = session['classifications']
    moved_files = []
    errors = []

    for image in session['images']:
        image_id = image['id']
        if image_id in classifications and classifications[image_id]:
            category = classifications[image_id]
            src_path = image['path']
            dest_dir = os.path.join(base_path, category)
            dest_path = os.path.join(dest_dir, image['name'])

            try:
                # 确保目标目录存在
                os.makedirs(dest_dir, exist_ok=True)

                # 移动文件
                shutil.move(src_path, dest_path)
                moved_files.append({
                    'name': image['name'],
                    'from': src_path,
                    'to': dest_path
                })
            except Exception as e:
                errors.append(f"移动文件 {image['name']} 时出错: {str(e)}")

    classifier.update_session(session_id, {'step': 5})

    result = {
        'success': True,
        'moved_count': len(moved_files),
        'moved_files': moved_files
    }

    if errors:
        result['errors'] = errors

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
