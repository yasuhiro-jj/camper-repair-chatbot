import os
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# APIキーの設定（環境変数から取得）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")