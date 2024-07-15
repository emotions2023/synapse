import os
from app import create_app
from dotenv import load_dotenv, find_dotenv
import chardet

# .envファイルを読み込む
dotenv_path = find_dotenv()

# .envファイルのエンコーディングを検出して設定
def load_env_with_encoding(dotenv_path):
    with open(dotenv_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    with open(dotenv_path, 'r', encoding=encoding) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

load_env_with_encoding(dotenv_path)
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
