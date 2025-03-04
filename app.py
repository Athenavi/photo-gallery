import hashlib
import json
from datetime import datetime
from flask import Flask, render_template, send_from_directory, make_response, request
from flask_caching import Cache
from pathlib import Path
import config
from photo_utils import get_photo_structure, get_day_photos

app = Flask(__name__, template_folder='templates', static_folder="static")
app.config['CACHE_TYPE'] = 'simple'
cache = Cache(app)
app.config.from_object(config)


@app.template_filter('month_name')
def month_name_filter(month_str):
    try:
        return datetime.strptime(month_str, "%m").strftime("%B")
    except ValueError:
        return month_str


@cache.cached(timeout=600)
@app.route('/')
def index():
    structure = get_photo_structure(app.config['PHOTO_ROOT'])
    return render_template('index.html', structure=structure)


@cache.cached(timeout=180)
@app.route('/etag')
def get_etag():
    structure = get_photo_structure(app.config['PHOTO_ROOT'])
    # 将字典转换为 JSON 格式的字符串
    structure_str = json.dumps(structure)
    return hashlib.md5(structure_str.encode('utf-8')).hexdigest()


@cache.cached(timeout=180)
@app.route('/day/<year>/<month>/<day>')
def day_view(year, month, day):
    photo_root = Path(app.config['PHOTO_ROOT']).resolve()
    day_path = photo_root / year / month / day
    photos = get_day_photos(day_path, photo_root)
    html_content = render_template('day.html',
                                   photos=photos,
                                   year=year,
                                   month=month,
                                   day=day)
    response = make_response(html_content)
    response.set_etag(get_etag())
    response.headers['Cache-Control'] = 'public, max-age=180'
    return response.make_conditional(request.environ)


@app.route('/<path:filename>')
def serve_photo(filename):
    return send_from_directory(app.config['PHOTO_ROOT'], filename)


if __name__ == '__main__':
    app.run(debug=True)
