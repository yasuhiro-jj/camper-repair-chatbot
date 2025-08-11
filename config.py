import os
from dotenv import load_dotenv

# .envファイルを読み込み（存在する場合）
if os.path.exists('.env'):
    try:
        load_dotenv()
    except UnicodeDecodeError:
        # .envファイルのエンコーディングエラーの場合、無視して続行
        print("Warning: .envファイルのエンコーディングエラーを無視して続行します")
    except Exception as e:
        # その他のエラーの場合も無視して続行
        print(f"Warning: .envファイルの読み込みエラーを無視して続行します: {e}")
else:
    print("Info: .envファイルが見つかりません。環境変数を設定してください。")

# APIキーの設定（環境変数から取得）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

# APIキーが設定されていない場合の警告
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEYが設定されていません。環境変数を設定してください。")
if not SERP_API_KEY:
    print("Warning: SERP_API_KEYが設定されていません。環境変数を設定してください。")