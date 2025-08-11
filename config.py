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
    print("Info: .envファイルが見つかりません。デフォルト設定を使用します。")

# APIキーの設定（直接設定または環境変数から取得）
OPENAI_API_KEY = "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"
SERP_API_KEY = "92c9c2dae2e41407a21cf68aa0a3dc5417fbcaf6ef0328b74ba6326d3ffd8f43"

# 環境変数が設定されている場合は環境変数を優先
if os.getenv("OPENAI_API_KEY"):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if os.getenv("SERP_API_KEY"):
    SERP_API_KEY = os.getenv("SERP_API_KEY")