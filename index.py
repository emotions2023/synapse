from flask import Flask, request, render_template_string
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# データベース接続
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD']
        )
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

@app.route('/')
def home():
    return render_template_string('''
        <h1>トップ画面</h1>
        <a href="/login">ログイン</a>
        <a href="/signup">新規登録</a>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                return render_template_string('<h1>ログインに成功しました！</h1>')
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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
