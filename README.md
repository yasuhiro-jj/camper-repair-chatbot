# キャンピングカー修理専門AIチャットボット

## 📋 概要
キャンピングカーの修理に関する質問に答えるAIチャットボットです。

## 🚀 デプロイ手順

### 1. GitHubにリポジトリを作成
1. GitHubにログイン
2. 新しいリポジトリを作成（例：`camping-repair-chatbot`）
3. リポジトリをクローン

### 2. ファイルをアップロード
以下のファイルをGitHubリポジトリにアップロード：

```
camping-repair-chatbot/
├── streamlit_app.py          # メインアプリケーション
├── requirements.txt          # 依存関係
├── config.py                # API設定
├── .streamlit/
│   └── config.toml         # Streamlit設定
├── キャンピングカー修理マニュアル.pdf
├── シナリオ1.txt
├── シナリオ2.txt
├── シナリオ3.txt
├── シナリオ4.txt
├── シナリオ5.txt
├── シナリオ6.txt
├── シナリオ7.txt
├── シナリオ8.txt
├── シナリオ9.txt
└── シナリオ10.txt
```

### 3. Streamlit Cloudでデプロイ
1. [Streamlit Cloud](https://streamlit.io/cloud)にアクセス
2. GitHubアカウントでログイン
3. 「New app」をクリック
4. リポジトリを選択
5. メインファイルパスを `streamlit_app.py` に設定
6. 「Deploy!」をクリック

### 4. 環境変数の設定
Streamlit Cloudの管理画面で以下の環境変数を設定：

```
OPENAI_API_KEY = your-openai-api-key
SERP_API_KEY = your-serpapi-key
```

## 📁 ファイル構成

### 必須ファイル
- `streamlit_app.py` - メインアプリケーション
- `requirements.txt` - Python依存関係
- `config.py` - API設定
- `.streamlit/config.toml` - Streamlit設定

### データファイル
- `キャンピングカー修理マニュアル.pdf` - メインマニュアル
- `シナリオ1.txt` ～ `シナリオ10.txt` - 修理シナリオ

## 🔧 ローカル開発

### 環境構築
```bash
# 仮想環境を作成
conda create -n campingrepare python=3.11
conda activate campingrepare

# 依存関係をインストール
pip install -r requirements.txt

# アプリケーションを起動
streamlit run streamlit_app.py
```

### 設定
`config.py` にAPIキーを設定：
```python
OPENAI_API_KEY = "your-openai-api-key"
SERP_API_KEY = "your-serpapi-key"
```

## 📊 機能

### チャット機能
- 会話履歴の保持
- リアルタイム回答生成
- クイック質問ボタン

### データ管理
- 動的ファイル読み込み
- PDF・テキストファイル対応
- ベクトル化による高速検索

### UI/UX
- レスポンシブデザイン
- モダンなチャットインターフェース
- サイドバーでのクイックアクセス

## 🔄 データ更新

### 新しいデータを追加
1. 新しいPDFまたはテキストファイルをリポジトリに追加
2. GitHubにプッシュ
3. Streamlit Cloudが自動的に再デプロイ

### データベース再構築
アプリケーション起動時に自動的に新しいファイルを読み込み、ベクトル化します。

## 🛠️ トラブルシューティング

### よくある問題
1. **APIキーエラー**: 環境変数が正しく設定されているか確認
2. **ファイル読み込みエラー**: ファイルが正しい場所にあるか確認
3. **依存関係エラー**: `requirements.txt` のバージョンを確認

### ログ確認
Streamlit Cloudの管理画面でログを確認できます。

## 📞 サポート
問題が発生した場合は、GitHubのIssuesで報告してください。 