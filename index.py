import os
from app import create_app

# デバッグ用に環境変数を出力
print("DATABASE_URL:", os.getenv('DATABASE_URL'))
print("GOOGLE_CLOUD_KEYFILE:", os.getenv('GOOGLE_CLOUD_KEYFILE'))

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
