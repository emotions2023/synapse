import json
from flask import Blueprint, request, jsonify, render_template_string, redirect, render_template, url_for
from . import db
from .models import Profile
from google.cloud import storage
import openai
import os
import base64
from datetime import datetime
import psycopg2

# Blueprintの設定
routes = Blueprint('routes', __name__)

# GOOGLE_CLOUD_KEYFILE 環境変数からJSONファイルパスを取得
google_cloud_keyfile = os.getenv('GOOGLE_CLOUD_KEYFILE', 'synapse001-45cd33ace705.json')
bucket_name = os.getenv('GOOGLE_CLOUD_BUCKET')

# Google Cloud Storageクライアントを初期化
storage_client = storage.Client.from_service_account_json(google_cloud_keyfile)

# OpenAI APIキーを取得
api_key = os.getenv('OPENAI_API_KEY')
# OpenAI APIクライアントを初期化
client = openai.OpenAI(api_key=api_key)

def upload_image_to_gcs(base64_image):
    try:
        buffer = base64.b64decode(base64_image)
        bucket = storage_client.bucket(bucket_name)
        file_name = f'profile-images/{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        blob = bucket.blob(file_name)
        blob.upload_from_string(buffer, content_type='image/png')
        return f'https://storage.googleapis.com/{bucket_name}/{file_name}'
    except Exception as e:
        print(f"Failed to upload image to GCS: {e}")
        return None

@routes.route('/')
def home():
    return render_template_string('''
        <h1>トップ画面</h1>
        <a href="/login">ログイン</a>
        <a href="/signup">新規登録</a>
    ''')

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = db.engine.raw_connection()
        if conn is not None:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                return redirect('/createProfile')
            else:
                return render_template_string('<h1>無効なメールアドレスまたはパスワード</h1>'), 401
        else:
            return render_template_string('<h1>データベース接続に失敗しました</h1>'), 500
    return render_template_string('''
        <h1>ログイン</h1>
        <form method="POST">
            <label>メールアドレス</label><br>
            <input type="text" name="email"><br>
            <label>パスワード</label><br>
            <input type="password" name="password"><br>
            <input type="submit" value="ログイン">
        </form>
    ''')

@routes.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        conn = db.engine.raw_connection()
        if conn is not None:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)', (name, email, password))
                conn.commit()
                cursor.close()
                conn.close()
                return render_template_string('<h1>新規登録に成功しました！</h1>')
            except psycopg2.IntegrityError:
                conn.rollback()
                cursor.close()
                conn.close()
                return render_template_string('<h1>このメールアドレスは既に登録されています</h1>'), 400
            except Exception as e:
                print(f"Error during signup: {e}")
                return render_template_string('<h1>新規登録中にエラーが発生しました</h1>'), 500
        else:
            return render_template_string('<h1>データベース接続に失敗しました</h1>'), 500
    return render_template_string('''
        <h1>新規登録</h1>
        <form method="POST">
            <label>名前</label><br>
            <input type="text" name="name"><br>
            <label>メールアドレス</label><br>
            <input type="text" name="email"><br>
            <label>パスワード</label><br>
            <input type="password" name="password"><br>
            <input type="submit" value="登録">
        </form>
    ''')

@routes.route('/createProfile', methods=['GET', 'POST'])
def create_profile():
    categories = [
        "王族", "皇族", "政治家", "軍人", "革命家", "探検家", "科学者", "発明家", "哲学者", "作家", "詩人", "画家", "彫刻家", "音楽家", "舞踏家", "俳優", "宗教家", "商人", "工匠", "教育者", "医者", "船乗り", "改革者", "経済学者", "法学者", "民族学者", "建築家", "演出家", "ジャーナリスト", "政治活動家", "環境保護活動家", "農学者"
    ]

    if request.method == 'POST':
        data = request.form
        name = data.get('name')
        category = data.get('category')
        century = int(data.get('century'))
        year_of_century = int(data.get('yearOfCentury'))
        image = request.files.get('image')  # request.filesを使ってファイルを取得

        if not all([name, category, century, year_of_century, image]):
            return jsonify({'error': 'Missing required fields'}), 400

        year_of_birth = century + year_of_century
        user_id = 1  # ここではテスト用にハードコーディング
        
        user_content = {
            "name": name,
            "category": category,
            "birth": year_of_birth
        }
        
        try:
            image_data = base64.b64encode(image.read()).decode('utf-8')
            image_url = upload_image_to_gcs(image_data)
            if image_url is None:
                return jsonify({'error': 'Failed to upload image to GCS'}), 500
        except Exception as e:
            return jsonify({'error': f'Image Upload Failed: {str(e)}'}), 500
        
        try:
            messages=[
            {
                "role": "system",
                "content": (
                    "あなたは架空の歴史的人物のみを扱う百科事典です。以下の人物紹介を、"
                    "Wikipediaのような形式で詳細に作成してください。ユーザーが提供する"
                    "「名前」「カテゴリー」「生誕年」に従い、その他の詳細を創作してください。"
                    "出力はjson形式とし、各フィールドには以下の情報を含めてください。"
                    "- name: 名前\n"
                    "- birth: 生年月日\n"
                    "- death: 死亡日\n"
                    "- cemetery: 墓地\n"
                    "- business: 職業\n"
                    "- language: 言語\n"
                    "- nationality: 国籍\n"
                    "- education: 教育\n"
                    "- lastEducation: 最終学歴\n"
                    "- periodOfActivity: 活動期間\n"
                    "- genre: ジャンル\n"
                    "- upbringing: 生い立ち（1000〜2000文字）\n"
                    "- deathDetails: 死去詳細（1000〜2000文字）\n"
                    "- others: その他の情報（1000〜2000文字）\n"
                )
            },
            {"role": "user", "content": json.dumps(user_content)}
        ]
            # デバッグ: リクエストの内容を出力
            print("OpenAI API request messages:", json.dumps(messages, ensure_ascii=False, indent=2))
        
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=2048
            )
            
        except Exception as e:
            return jsonify({'error': f'OpenAI API Call Failed: {str(e)}'}), 500
        
        try:
            # レスポンスの内容をログに出力
            print("OpenAI API response:", response)
            
            profile_data = response.choices[0].message.content
            print("profile_data = " ,profile_data)
            profile_json = json.loads(profile_data)
            
            # 欠けているキーにデフォルト値を設定
            required_keys = ["name", "birth", "death", "cemetery", "business", "language", "nationality", "education", "lastEducation", "periodOfActivity", "genre", "upbringing", "deathDetails", "others"]
            for key in required_keys:
                if key not in profile_json:
                    profile_json[key] = "不明"
            
        except Exception as e:
            return jsonify({'error': f'Response Processing Failed: {str(e)}'}), 500
        
        try:
            profile = Profile(
                name=profile_json["name"],
                birth=profile_json["birth"],
                death=profile_json["death"],
                cemetery=profile_json["cemetery"],
                business=profile_json["business"],
                language=profile_json["language"],
                nationality=profile_json["nationality"],
                education=profile_json["education"],
                last_education=profile_json["lastEducation"],
                period_of_activity=profile_json["periodOfActivity"],
                genre=profile_json["genre"],
                upbringing=profile_json["upbringing"],
                death_details=profile_json["deathDetails"],
                others=profile_json["others"],
                created_at=datetime.now(),
                user_id=user_id,
                delete_flag=False,
                image_url=image_url
            )

            db.session.add(profile)
            db.session.commit()
            
             # プロファイル詳細ページにリダイレクト
            return redirect(f'/profile/{profile.id}')

            # return jsonify(profile_json), 201

        except Exception as e:
            return jsonify({'error': f'Database Operation Failed: {str(e)}'}), 500
    else:
        return render_template_string('''
            <h1>架空の歴史を作成</h1>
            <form method="POST" enctype="multipart/form-data">
                <label>名前</label><br>
                <input type="text" name="name"><br>
                <label>カテゴリー</label><br>
                <select name="category">
                    {% for category in categories %}
                        <option value="{{ category }}">{{ category }}</option>
                    {% endfor %}
                </select><br>
                <label>世紀</label><br>
                <select name="century" id="century" onchange="updateYearOfCentury()">
                    <option value="" selected disabled>選択してください</option>
                    {% for century in range(-2000, 2100, 100) %}
                        <option value="{{ century }}">{{ century }}</option>
                    {% endfor %}
                </select><br>
                <label>年</label><br>
                <select name="yearOfCentury" id="yearOfCentury">
                    <!-- JavaScriptで動的に追加 -->
                </select><br>
                <label>画像</label><br>
                <input type="file" name="image"><br>
                <input type="submit" value="作成">
            </form>
            <script>
                function updateYearOfCentury() {
                    var centurySelect = document.getElementById('century');
                    var yearOfCenturySelect = document.getElementById('yearOfCentury');
                    var selectedCentury = parseInt(centurySelect.value);
                    
                    yearOfCenturySelect.innerHTML = '';
                    
                    for (var i = 0; i < 100; i++) {
                        var year = selectedCentury + i;
                        var option = document.createElement('option');
                        option.value = i;
                        option.text = year;
                        yearOfCenturySelect.appendChild(option);
                    }
                }
            </script>
        ''', categories=categories)
        
@routes.route('/profile/<int:id>', methods=['GET'])
def view_profile(id):
    profile = Profile.query.get(id)
    if not profile:
        return "Profile not found", 404
    return render_template('profile.html', profile=profile)
