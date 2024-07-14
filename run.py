import os
from app import create_app

print("DATABASE_URL:", os.getenv('DATABASE_URL'))  # デバッグ用に接続文字列を出力

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
