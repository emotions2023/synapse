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

# Google Cloud Storageの設定
storage_client = storage.Client.from_service_account_json(os.getenv('GOOGLE_CLOUD_KEYFILE'))
bucket_name = os.getenv('GOOGLE_CLOUD_BUCKET')

# OpenAIの設定
openai.api_key = os.getenv('OPENAI_API_KEY')

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
        
        api_key = os.getenv("OPENAI_API_KEY")

        # OpenAI APIクライアントを初期化
        client = openai.OpenAI(api_key=api_key)
        
        user_content = f"""
        {{
            "name": "{name}",
            "category": "{category}",
            "birth": "{year_of_birth}"
        }}
        """
        
        try:
            image_data = base64.b64encode(image.read()).decode('utf-8')
            image_url = upload_image_to_gcs(image_data)
            if image_url is None:
                return jsonify({'error': 'Failed to upload image to GCS'}), 500
        except Exception as e:
            return jsonify({'error': f'Image Upload Failed: {str(e)}'}), 500
        
        try:
            response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    response_format={"type": "json_object"},
                    messages=[
                    {
                        "role": "system",
                        "content": """あなたは人物の歴史を網羅している百科事典です。この百科事典には史実とは違う、架空の歴史的人物のみ登場します。紀元前2000年～現代までの中で、何かを成し遂げ、死没していった人ばかりです。そんな架空の人物の、歴史をWikipediaのように網羅的に人物紹介をしてください。ただし、「名前」「カテゴリー」「生誕年」はユーザーが決めた内容に従ってください。名前、生年月日、ジャンルはユーザーが入力した内容を記載してください。それ以外はあなたが創作してください。生い立ちには、人物の詳細な生い立ちを300～500文字で表示してください。死去詳細には、人物の死因や死亡場所など詳細に300～500文字で表示してください。その他には、人物の生涯を詳細に300文字～500文字でjson形式で表示してください。下記はjson形式の出力方法です。
                        "name": "名前",
                        "birth": "生年月日",
                        "death": "死亡日",
                        "cemetery": "墓地",
                        "business": "職業",
                        "language": "言語",
                        "nationality": "国籍",
                        "education": "教育",
                        "lastEducation": "最終学歴",
                        "periodOfActivity": "活動期間",
                        "genre": "ジャンル",
                        "upbringing": "生い立ち",
                        "deathDetails": "死去詳細",
                        "others": "その他の情報"名前: ${name}、カテゴリー: ${category}、生誕: ${yearOfBirth}年`
                    """},
                    {"role": "user", "content": user_content}
                ]
            )
        except Exception as e:
            return jsonify({'error': f'OpenAI API Call Failed: {str(e)}'}), 500
        
        try:
            # レスポンスの内容をログに出力
            print("OpenAI API response:", response)
            
            profile_data = response.choices[0].message.content
            print("profile_data = " ,profile_data)
            profile_json = json.loads(profile_data)
            
        
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
