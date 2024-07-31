import json
from flask import Blueprint, request, jsonify, render_template_string, redirect, render_template, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from . import db
from .models import Users, Profile, FeaturedArticle, DailyImage, DailyEvent
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

# トップ -----------------------------------------------------------------------
@routes.route('/')
def home():
    histories = Profile.query.filter_by(delete_flag=False).all()
    return render_template('home.html', histories=histories)
    # return render_template('home.html')

# ログイン -----------------------------------------------------------------------
@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user_obj = Users.query.filter_by(email=email, password=password).first()
        
        if user_obj:
            login_user(user_obj)
            return redirect('/createProfile')
        else:
            error = "Invalid email or password"
            return render_template('login.html', error=error)
    
    return render_template('login.html')

# ログアウト -----------------------------------------------------------------------
@routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

# サインアップ -----------------------------------------------------------------------
@routes.route('/signup', methods=['GET', 'POST'])
def signup():
    user_count = Users.query.count()
    page_count = Profile.query.count()
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
                flash('新規登録に成功しました！', 'success')
                user_obj = Users.query.filter_by(email=email, password=password).first()
                if user_obj:
                    login_user(user_obj)
                return redirect(url_for('routes.home'))
            except psycopg2.IntegrityError:
                conn.rollback()
                cursor.close()
                conn.close()
                flash('このメールアドレスは既に登録されています', 'error')
                return redirect(url_for('routes.signup'))
            except Exception as e:
                print(f"Error during signup: {e}")
                flash('新規登録中にエラーが発生しました', 'error')
                return redirect(url_for('routes.signup'))
        else:
            flash('データベース接続に失敗しました', 'error')
            return redirect(url_for('routes.signup'))
    return render_template('signup.html', user_count=user_count, page_count=page_count)

# 検索 -----------------------------------------------------------------------
@routes.route('/search', methods=['GET'])
def search():
    name = request.args.get('name')
    if name:
        profiles = db.session.query(Profile).filter(Profile.name.ilike(f'%{name}%')).all()
        if profiles:
            if len(profiles) == 1:
                return redirect(url_for('routes.viewProfile', id=profiles[0].id))
            else:
                return render_template('searchResults.html', profiles=profiles)
        else:
            flash('人物が見つかりませんでした。')
            return redirect(url_for('routes.home'))
    return redirect(url_for('routes.home'))

# 歴史生成 -----------------------------------------------------------------------
@routes.route('/createProfile', methods=['GET', 'POST'])
@login_required
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
        user_id = current_user.id
        
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
            profile_data = response.choices[0].message.content
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
        return render_template('createProfile.html',categories=categories)

# 生成した歴史確認 -----------------------------------------------------------------------
@routes.route('/profile/<int:id>', methods=['GET'])
def viewProfile(id):
    profile = Profile.query.get(id)
    if not profile:
        return "Profile not found", 404
    return render_template('profile.html', profile=profile)

# 生成した歴史確認（リスト） -----------------------------------------------------------------------
@routes.route('/searchResults', methods=['GET'])
def searchResults():
    name = request.args.get('name')
    profiles = db.session.query(Profile).filter(Profile.name.ilike(f'%{name}%')).all()
    return render_template('searchResults.html', profiles=profiles)

# 記事生成一覧 -------------------------------------------------------------
@routes.route('/articleSelection', methods=['GET', 'POST'])
@login_required
def articleSelection():
    return render_template('articleSelection.html')

# 記事生成一覧 > 選り抜き記事-------------------------------------------------------------
@routes.route('/featuredArticles', methods=['GET', 'POST'])
@login_required
def featuredArticles():
    if request.method == 'POST':
        data = request.form
        title = data.get('title')
        summary = data.get('summary')
        genre = data.get('genre')

        if not all([title, summary, genre]):
            flash('すべてのフィールドを埋めてください。', 'error')
            return redirect(url_for('routes.featuredArticles'))

        user_content = {
            "title": title,
            "summary": summary,
            "genre": genre
        }
        
        print("DEBUG: User content:", user_content)

        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "あなたは選り抜き記事を生成するAIです。以下の情報を基に、Wikipediaのような形式で選り抜き記事を1500文字以上3000文字以内で作成してください。"
                        "出力はjson形式とし、各フィールドには以下の情報を含めてください。"
                        "- title: タイトル\n"
                        "- content: 記事内容\n"
                    )
                },
                {"role": "user", "content": json.dumps(user_content)}
            ]

            print("OpenAI API request messages:", json.dumps(messages, ensure_ascii=False, indent=2))
       
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=2048
            )
            
            print("DEBUG: OpenAI API response:", response)

        except Exception as e:
            flash(f'OpenAI API Call Failed: {str(e)}', 'error')
            return redirect(url_for('routes.featuredArticles'))

        try:
            article_data = response.choices[0].message.content
            print("DEBUG: Article data received:", article_data) # デバッグログ追加
            article_json = json.loads(article_data)
            print("DEBUG: Article data received:", article_data) 

            # 欠けているキーにデフォルト値を設定
            required_keys = ["title", "content"]
            for key in required_keys:
                if key not in article_json:
                    article_json[key] = "不明"
            print("DEBUG: Article JSON after processing:", article_json)

        except Exception as e:
            flash(f'Response Processing Failed: {str(e)}', 'error')
            return redirect(url_for('routes.featuredArticles'))
        
        try:
            # 画像生成のためのプロンプトを作成
            image_prompt = f"{article_json['title']}: {article_json['content'][:200]}"
            print("DEBUG: Image prompt:", image_prompt) 
            
            # 画像生成リクエスト
            image_response = client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            print("DEBUG: Image response:", image_response)
            # image_url = image_response.data[0].url
            image_url = upload_image_to_gcs(image_response['data'][0]['url'])
            
        except Exception as e:
            flash(f'Image Generation Failed: {str(e)}', 'error')
            return redirect(url_for('routes.featuredArticles'))

        try:
            article = FeaturedArticle(
                title=article_json["title"],
                content=article_json["content"],
                image_url=image_url,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                user_id=current_user.id
            )

            db.session.add(article)
            db.session.commit()

            flash('記事が正常に作成されました。', 'success')
            return redirect(f'/viewFeaturedArticles/{article.id}')
        except Exception as e:
            flash(f'Database Operation Failed: {str(e)}', 'error')
            return redirect(url_for('routes.featuredArticles'))
    else:
        articles = FeaturedArticle.query.all()
        return render_template('viewFeaturedArticles.html', featuredArticles=articles)

# 記事生成一覧 > 選り抜き記事確認-------------------------------------------------------------
@routes.route('/article/<int:id>', methods=['GET'])
def viewFeaturedArticles(id):
    article = FeaturedArticle.query.get(id)
    if not article:
        return "FeaturedArticle not found", 404
    return render_template('viewFeaturedArticles.html', article=article)


# 記事生成一覧 > 今日の１枚-------------------------------------------------------------
@routes.route('/dailyImages', methods=['GET', 'POST'])
@login_required
def dailyImages():
    return "dailyImages"

# 記事生成一覧 > 今日は何の日？-------------------------------------------------------------
@routes.route('/dailyEvents', methods=['GET', 'POST'])
@login_required
def dailyEvents():
    return "dailyEvents"
