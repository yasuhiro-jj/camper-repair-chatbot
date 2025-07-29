import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

# 環境変数からAPIキーを取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

# APIキーが設定されていない場合のエラーハンドリング
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEYが設定されていません。.envファイルを確認してください。")

if not SERP_API_KEY:
    raise ValueError("SERP_API_KEYが設定されていません。.envファイルを確認してください。") 