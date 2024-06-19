from flask import Flask, request, jsonify, render_template_string
import os

app = Flask(__name__)

users = {}

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
        if email in users and users[email] == password:
            return jsonify({'message': 'ログインに成功しました！'})
        else:
            return jsonify({'message': '無効なメールアドレスまたはパスワード'}), 401
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
        if email not in users:
            users[email] = password
            return jsonify({'message': '新規登録に成功しました！'})
        else:
            return jsonify({'message': 'このメールアドレスは既に登録されています'}), 400
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
