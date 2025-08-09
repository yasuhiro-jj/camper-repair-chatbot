# キャンピングカー修理専門AIチャット

## 🚀 Streamlit Cloud デプロイ

このアプリはStreamlit Cloudで簡単にデプロイできます。

### デプロイ手順

1. **GitHubにリポジトリをプッシュ**
   ```bash
   git add .
   git commit -m "Initial commit for Streamlit Cloud"
   git push origin main
   ```

2. **Streamlit Cloudでデプロイ**
   - [Streamlit Cloud](https://share.streamlit.io/)にアクセス
   - GitHubアカウントでログイン
   - 「New app」をクリック
   - リポジトリを選択
   - メインファイル: `streamlit_app.py`
   - デプロイ！

### 🔑 環境変数の設定

Streamlit Cloudの管理画面で以下の環境変数を設定してください：

- `OPENAI_API_KEY`: OpenAI APIキー

### 📁 ファイル構成

- `streamlit_app.py`: メインアプリケーション
- `requirements.txt`: 依存関係
- `.streamlit/config.toml`: Streamlit設定
- `config.py`: 設定ファイル

### 🛠️ ローカル実行

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### 📱 機能

- キャンピングカー修理の専門AIチャット
- PDF・テキストファイルからの情報検索
- リアルタイムチャット
- モバイル対応UI 