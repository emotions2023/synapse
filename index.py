from flask import Flask, request, render_template_string
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# データベース接続
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )
    return conn

# usersテーブルの作成（存在しない場合）
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(50) NOT NULL
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

create_table()

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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            return render_template_string('<h1>ログインに成功しました！</h1>')
        else:
            return render_template_string('<h1>無効なメールアドレスまたはパスワード</h1>'), 401
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
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, password))
            conn.commit()
            cursor.close()
            conn.close()
            return render_template_string('<h1>新規登録に成功しました！</h1>')
        except psycopg2.IntegrityError:
            conn.rollback()
            cursor.close()
            conn.close()
            return render_template_string('<h1>このメールアドレスは既に登録されています</h1>'), 400
    return render_template_string('''
        <h1>新規登録</h1>
        <form method="POST">
            <label>ユーザー名</label><br>
            <input type="text" name="username"><br>
            <label>メールアドレス</label><br>
            <input type="text" name="email"><br>
            <label>パスワード</label><br>
            <input type="password" name="password"><br>
            <input type="submit" value="登録">
        </form>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
