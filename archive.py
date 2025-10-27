import os
import shutil
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
            'current_image_index': 0,
            'uploaded_files': {}  # 存储上传的文件信息
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


@app.route('/api/upload-files', methods=['POST'])
def upload_files():
    session_id = request.form.get('session_id')
    level = request.form.get('level')

    if not session_id or not level:
        return jsonify({'error': '缺少必要参数'}), 400

    session = classifier.get_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 400

    # 处理上传的文件
    uploaded_files = []
    if 'files' in request.files:
        files = request.files.getlist('files')

        for file in files:
            if file.filename:
                # 安全地保存文件名
                filename = secure_filename(file.filename)
                file_id = str(uuid.uuid4())

                # 创建临时文件
                temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
                os.makedirs(temp_dir, exist_ok=True)

                file_path = os.path.join(temp_dir, file_id + '_' + filename)
                file.save(file_path)

                uploaded_files.append({
                    'id': file_id,
                    'name': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'last_modified': os.path.getmtime(file_path)
                })

    if not uploaded_files:
        return jsonify({'error': '没有上传任何文件'}), 400

    # 根据等级提取可能的分类
    categories = set()
    for file_info in uploaded_files:
        try:
            mod_time = datetime.fromtimestamp(file_info['last_modified'])

            if level == 'year':
                categories.add(str(mod_time.year))
            elif level == 'month':
                categories.add(f"{mod_time.year}-{mod_time.month:02d}")
            elif level == 'date':
                categories.add(f"{mod_time.year}-{mod_time.month:02d}-{mod_time.day:02d}")
        except Exception as e:
            print(f"Error processing file {file_info['name']}: {e}")

    # 更新会话
    session['uploaded_files'] = {file['id']: file for file in uploaded_files}
    session['images'] = uploaded_files
    session['step'] = 2
    session['level'] = level
    session['available_categories'] = sorted(list(categories))

    return jsonify({
        'success': True,
        'image_count': len(uploaded_files),
        'available_categories': sorted(list(categories))
    })


@app.route('/api/select-categories', methods=['POST'])
def select_categories():
    session_id = request.json.get('session_id')
    selected_categories = request.json.get('selected_categories', [])

    session = classifier.get_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 400

    # 创建分类文件夹（在临时目录中）
    temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    for category in selected_categories:
        category_path = os.path.join(temp_dir, category)
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

    uploaded_files = session.get('uploaded_files', {})
    if image_id not in uploaded_files:
        return jsonify({'error': '图片不存在'}), 404

    file_info = uploaded_files[image_id]

    # 返回图片文件
    return send_file(file_info['path'], as_attachment=False)


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
            'category': session['classifications'].get(image['id'], '未分类')
        })

    return jsonify({
        'classifications': classifications,
        'total_count': len(classifications)
    })


@app.route('/api/execute-move', methods=['POST'])
def execute_move():
    session_id = request.json.get('session_id')
    target_folder = request.json.get('target_folder', '')

    session = classifier.get_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 400

    # 如果没有指定目标文件夹，使用原始位置
    if not target_folder:
        # 获取第一个文件的原始目录
        first_file = session['images'][0]['path']
        target_folder = os.path.dirname(first_file)

    base_path = target_folder
    classifications = session['classifications']
    moved_files = []

    for image in session['images']:
        image_id = image['id']
        if image_id in classifications and classifications[image_id]:
            category = classifications[image_id]
            src_path = image['path']
            dest_dir = os.path.join(base_path, category)
            dest_path = os.path.join(dest_dir, image['name'])

            # 确保目标目录存在
            os.makedirs(dest_dir, exist_ok=True)

            # 移动文件
            shutil.move(src_path, dest_path)
            moved_files.append({
                'name': image['name'],
                'from': src_path,
                'to': dest_path
            })

    classifier.update_session(session_id, {'step': 5})

    return jsonify({
        'success': True,
        'moved_count': len(moved_files),
        'moved_files': moved_files
    })


@app.route('/api/cleanup-session', methods=['POST'])
def cleanup_session():
    session_id = request.json.get('session_id')
    session = classifier.get_session(session_id)

    if session:
        # 清理临时文件
        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        # 从会话存储中移除
        if session_id in user_sessions:
            del user_sessions[session_id]

    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
