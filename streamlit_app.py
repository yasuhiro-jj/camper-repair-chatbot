import streamlit as st
import os
import uuid
import requests
from bs4 import BeautifulSoup
from typing import Literal
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.embeddings import OpenAIEmbeddings
import config
import glob

# === ページ設定 ===
st.set_page_config(
    page_title="キャンピングカー修理専門AIチャット",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# サイドバーを強制的に表示
st.markdown("""
<style>
/* サイドバーを常に表示 */
.stApp > div[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    position: relative !important;
}

/* スマホでのサイドバー表示を確保 */
@media (max-width: 768px) {
    .stApp > div[data-testid="stSidebar"] {
        display: block !important;
        width: 100% !important;
        visibility: visible !important;
        position: relative !important;
        z-index: 1000 !important;
    }
    
    /* サイドバーの背景を確保 */
    .stApp > div[data-testid="stSidebar"] > div {
        background-color: #f0f2f6 !important;
        padding: 1rem !important;
    }
}

/* サイドバーの表示を強制 */
section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
}
</style>
""", unsafe_allow_html=True)

# === セッション状態の初期化 ===
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

# === データベース初期化 ===
@st.cache_resource
def initialize_database():
    """データベースを初期化"""
    main_path = os.path.dirname(os.path.abspath(__file__))
    
    documents = []
    
    # PDFファイルを動的に検索
    pdf_pattern = os.path.join(main_path, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    
    for pdf_path in pdf_files:
        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            documents.extend(docs)
        except Exception as e:
            pass
    
    # テキストファイルを動的に検索
    txt_pattern = os.path.join(main_path, "*.txt")
    txt_files = glob.glob(txt_pattern)
    
    for txt_path in txt_files:
        try:
            loader = TextLoader(txt_path, encoding='utf-8')
            docs = loader.load()
            documents.extend(docs)
        except Exception as e:
            pass
    
    if not documents:
        pdf_path = os.path.join(main_path, "キャンピングカー修理マニュアル.pdf")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
    
    # OpenAIの埋め込みモデルを設定
    embeddings_model = OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)
    
    for doc in documents:
        if not isinstance(doc.page_content, str):
            doc.page_content = str(doc.page_content)
    
    # ドキュメントをメモリに保存
    return documents

# === モデルとツールの設定 ===
@st.cache_resource
def initialize_model():
    """モデルを初期化"""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        openai_api_key=config.OPENAI_API_KEY,
        max_tokens=500  # トークン数を制限
    )

@st.cache_resource
def initialize_tools():
    """ツールを初期化（外部検索機能は無効化）"""
    # 外部検索機能を無効化
    return []

# === ブログ記事検索機能 ===
@st.cache_data(ttl=3600)  # 1時間キャッシュ
def search_blog_articles(query: str):
    """ブログ記事を検索して関連記事を取得"""
    try:
        # ブログサイトのURL
        blog_url = "https://camper-repair.net/blog/"
        
        # サイトから記事一覧を取得
        response = requests.get(blog_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 記事リンクを取得
        articles = []
        
        # より確実に記事を取得するため、複数の方法を試す
        # 1. すべてのリンクを取得
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            title = link.get_text(strip=True)
            url = link.get('href')
            
            # タイトルが空でない、かつURLが有効な場合のみ処理
            if title and url and len(title) > 5:
                # 相対URLを絶対URLに変換
                if url.startswith('/'):
                    url = "https://camper-repair.net" + url
                elif not url.startswith('http'):
                    url = "https://camper-repair.net/" + url
                
                # タイトルに関連キーワードが含まれているかチェック
                query_words = query.lower().split()
                title_lower = title.lower()
                
                # 関連性スコアを計算（より柔軟なマッチング）
                score = 0
                for word in query_words:
                    if len(word) > 2 and word in title_lower:  # 2文字以上の単語のみ
                        score += 1
                
                # エアコン関連の質問の場合、エアコン関連記事を優先
                if any(word in query.lower() for word in ['エアコン', 'aircon', '冷房', '暖房']):
                    if any(word in title_lower for word in ['エアコン', 'aircon', '冷房', '暖房']):
                        score += 3
                
                # バッテリー関連の質問の場合
                if any(word in query.lower() for word in ['バッテリー', 'battery', '電池']):
                    if any(word in title_lower for word in ['バッテリー', 'battery', '電池', 'リチウム']):
                        score += 3
                
                # 冷蔵庫関連の質問の場合
                if any(word in query.lower() for word in ['冷蔵庫', 'refrigerator', '冷蔵']):
                    if any(word in title_lower for word in ['冷蔵庫', 'refrigerator', '冷蔵']):
                        score += 3
                
                if score > 0:
                    articles.append({
                        'title': title,
                        'url': url,
                        'score': score
                    })
        
        # スコアでソート
        articles.sort(key=lambda x: x['score'], reverse=True)
        
        # デバッグ用：記事が見つからない場合のフォールバック
        if not articles:
            # デフォルトの記事を返す
            default_articles = [
                {
                    'title': 'キャンピングカーのエアコンメンテナンスガイド',
                    'url': 'https://camper-repair.net/blog/aircon-maintenance/',
                    'score': 1
                },
                {
                    'title': 'キャンピングカーのバッテリー管理完全ガイド',
                    'url': 'https://camper-repair.net/blog/battery-guide/',
                    'score': 1
                },
                {
                    'title': 'キャンピングカーの冷蔵庫トラブルシューティング',
                    'url': 'https://camper-repair.net/blog/refrigerator-troubleshooting/',
                    'score': 1
                }
            ]
            return default_articles
        
        return articles[:3]  # 上位3件を返す
        
    except Exception as e:
        st.error(f"ブログ記事の取得中にエラーが発生しました: {str(e)}")
        # エラー時もデフォルト記事を返す
        return [
            {
                'title': 'キャンピングカーのエアコンメンテナンスガイド',
                'url': 'https://camper-repair.net/blog/aircon-maintenance/',
                'score': 1
            },
            {
                'title': 'キャンピングカーのバッテリー管理完全ガイド',
                'url': 'https://camper-repair.net/blog/battery-guide/',
                'score': 1
            },
            {
                'title': 'キャンピングカーの冷蔵庫トラブルシューティング',
                'url': 'https://camper-repair.net/blog/refrigerator-troubleshooting/',
                'score': 1
            }
        ]

# === RAGとプロンプトテンプレート ===
def rag_retrieve(question: str, documents):
    """RAGで関連文書を取得"""
    # キーワードベースの検索
    relevant_docs = []
    keywords = question.lower().split()
    
    for doc in documents:
        doc_content = doc.page_content.lower()
        score = sum(1 for keyword in keywords if keyword in doc_content)
        if score > 0:
            relevant_docs.append((doc, score))
    
    # スコアでソート
    relevant_docs.sort(key=lambda x: x[1], reverse=True)
    
    if relevant_docs:
        content = relevant_docs[0][0].page_content
        if len(content) > 1000:
            content = content[:1000] + "..."
        return content
    else:
        return "キャンピングカーの修理に関する一般的な情報をお探しします。"

template = """
あなたはキャンピングカーの修理専門家です。以下の文書抜粋を参照して質問に答えてください。

文書抜粋：{document_snippet}

質問：{question}

以下の形式で親しみやすい会話調で回答してください：

【対処法】
• 具体的な手順
• 注意点
• 必要な工具・部品

【関連ブログ記事】
ユーザーの質問に関連するブログ記事があれば、親しみやすい会話調で紹介してください。
例：「この件について、当社のブログで詳しく解説している記事がありますよ！ぜひ参考にしてみてください。」

【岡山キャンピングカー修理サポートセンター】
上記の対処法を試していただき、さらに詳しいアドバイスや実際の修理作業が必要な場合は、お気軽に岡山キャンピングカー修理サポートセンターまでご相談ください！

📞 **お電話でのご相談**
- 電話番号: 080-206-6622
- 営業時間: 年中無休（9:00〜21:00）
- ※不在時は折り返しお電話差し上げます

💬 **メールでのご相談**
- 直接スタッフと相談したいときは直接お電話いただくか、[メールでのご相談](https://camper-repair.net/contact/)も承ります。

**※重要**: 安全な修理作業のため、複雑な修理や専門的な作業が必要な場合は、必ず岡山キャンピングカー修理サポートセンターにご相談ください。

答え：
"""

# === ワークフローの構築 ===
@st.cache_resource
def build_workflow():
    """ワークフローを構築"""
    model = initialize_model()
    tools = initialize_tools()
    tool_node = ToolNode(tools)
    
    def should_continue(state: MessagesState) -> Literal["tools", END]:
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END
    
    def call_model(state: MessagesState):
        messages = state['messages']
        try:
            response = model.invoke(messages)
            return {"messages": [response]}
        except Exception as e:
            error_message = f"申し訳ございませんが、エラーが発生しました: {str(e)}"
            return {"messages": [AIMessage(content=error_message)]}
    
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", 'agent')
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

# === メインアプリケーション ===
def main():
    # レスポンシブなタイトル（スマホ対応）とヘッダー非表示
    st.markdown("""
    <style>
                    @media (max-width: 768px) {
                    .mobile-title h1 {
                        font-size: 1.4rem !important;
                        line-height: 1.3 !important;
                    }
                    .mobile-title p {
                        font-size: 0.8rem !important;
                    }
                    /* スマホでのタイトル文字サイズ調整 */
                    h2 {
                        font-size: 1.2rem !important;
                        line-height: 1.2 !important;
                    }
                    p, em {
                        font-size: 0.8rem !important;
                    }
                }
    
    /* 右上のメニュー要素を非表示 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ハンバーガーメニューを非表示 */
    .stDeployButton {display: none;}
    
    /* ヘッダー要素を非表示 */
    .stApp > header {display: none;}
    
    /* 右上のツールバー要素を非表示 */
    .stApp > div[data-testid="stToolbar"] {display: none;}
    .stApp > div[data-testid="stToolbarActions"] {display: none;}
    
    /* メニューボタンを非表示 */
    .stApp > div[data-testid="stMenuButton"] {display: none;}
    .stApp > div[data-testid="stMenu"] {display: none;}
    
    /* ヘッダーアクションを非表示 */
    .stApp > div[data-testid="stHeaderActions"] {display: none;}
    
    /* メインコンテンツの上部マージンを調整 */
    .main .block-container {
        padding-top: 1rem;
    }
    
    /* 右上のアイコン類を非表示 */
    .stApp > div[data-testid="stDecoration"] {display: none;}
    .stApp > div[data-testid="stStatusWidget"] {display: none;}
    /* フォークボタンとGitHubボタンを非表示 */
    .stApp > div[data-testid="stGitHubButton"] {display: none;}
    .stApp > div[data-testid="stForkButton"] {display: none;}
    /* 3点メニューを非表示 */
    .stApp > div[data-testid="stMenuButton"] {display: none;}
    /* ユーザーアバターを非表示 */
    .stApp > div[data-testid="stUserAvatar"] {display: none;}
    /* Streamlitブランディングを非表示 */
    .stApp > div[data-testid="stStreamlitBranding"] {display: none;}
    /* 右下のホスト情報を非表示 */
    .stApp > div[data-testid="stBottomBlock"] {display: none;}
    .stApp > div[data-testid="stBottomContainer"] {display: none;}
    
    /* サイドバーを常に表示 */
    .stApp > div[data-testid="stSidebar"] {
        display: block !important;
    }
    
    /* スマホでのサイドバー表示を確保 */
    @media (max-width: 768px) {
        .stApp > div[data-testid="stSidebar"] {
            display: block !important;
            width: 100% !important;
        }
    }
    </style>

    """, unsafe_allow_html=True)
    
    # タイトルを表示（中央揃え、改行付き）
    st.markdown("<h2 style='text-align: center;'>🔧 キャンピングカー修理専門<br>AIチャット</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic;'>経験豊富なキャンピングカー修理アドバイザーAIが<br>修理について詳しくお答えします</p>", unsafe_allow_html=True)
    
    # サイドバー
    with st.sidebar:
        # クイック質問の表示/非表示を制御
        if 'show_quick_questions' not in st.session_state:
            st.session_state.show_quick_questions = False
        
        # クイック質問ボタン
        if st.button("📋 クイック質問", use_container_width=True):
            st.session_state.show_quick_questions = not st.session_state.show_quick_questions
            st.rerun()
        
        # クイック質問が表示されている場合
        if st.session_state.show_quick_questions:
            st.markdown("---")
            st.markdown("**よくある質問：**")
            
            if st.button("🔋 バッテリー上がり", use_container_width=True):
                prompt = "バッテリーが上がってエンジンが始動しない時の対処法を教えてください"
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()
            
            if st.button("🚰 水道ポンプ", use_container_width=True):
                prompt = "水道ポンプから水が出ない時の修理方法は？"
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()
            
            if st.button("🔥 ガスコンロ", use_container_width=True):
                prompt = "ガスコンロが点火しない時の対処法を教えてください"
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()
            
            if st.button("🧊 冷蔵庫", use_container_width=True):
                prompt = "冷蔵庫が冷えない時の修理方法は？"
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()
            
            if st.button("🔧 定期点検", use_container_width=True):
                prompt = "キャンピングカーの定期点検項目とスケジュールは？"
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()
        
        st.divider()
        
        if st.button("🆕 新しい会話を開始", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_id = str(uuid.uuid4())
            st.rerun()
    
    # メインエリア
    # チャット履歴の表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # クイック質問からの自動回答処理
    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
        # 最新のメッセージがユーザーからの場合、AI回答を生成
        prompt = st.session_state.messages[-1]["content"]
        
        # AIの回答を生成
        with st.chat_message("assistant", avatar="https://camper-repair.net/blog/wp-content/uploads/2025/05/dummy_staff_01-150x138-1.png"):
            with st.spinner("🔧 修理アドバイスを生成中..."):
                try:
                    # ドキュメントとワークフローを取得
                    documents = initialize_database()
                    app_flow = build_workflow()
                    
                    # RAGで関連文書を取得
                    document_snippet = rag_retrieve(prompt, documents)
                    
                    # プロンプトを構築
                    content = template.format(document_snippet=document_snippet, question=prompt)
                    
                    # 会話履歴を構築（最新の5件のみ）
                    history = []
                    recent_messages = st.session_state.messages[-5:-1]  # 最新の5件のみ
                    for msg in recent_messages:
                        if msg["role"] == "user":
                            history.append(HumanMessage(content=msg["content"]))
                        else:
                            history.append(AIMessage(content=msg["content"]))
                    
                    # 新しいメッセージを追加
                    inputs = history + [HumanMessage(content=content)]
                    thread = {"configurable": {"thread_id": st.session_state.conversation_id}}
                    
                    # 回答を生成
                    response = ""
                    for event in app_flow.stream({"messages": inputs}, thread, stream_mode="values"):
                        if "messages" in event and event["messages"]:
                            response = event["messages"][-1].content
                    
                    # 回答を表示
                    st.markdown(response)
                    
                    # ブログ記事の検索と表示
                    blog_articles = search_blog_articles(prompt)
                    st.markdown("---")
                    st.markdown("**📝 関連ブログ記事**")
                    if blog_articles:
                        for article in blog_articles:
                            st.markdown(f"• [{article['title']}]({article['url']})")
                        st.markdown("*より詳しい情報は上記の記事をご覧ください*")
                    else:
                        st.markdown("• [キャンピングカーのエアコンメンテナンスガイド](https://camper-repair.net/blog/aircon-maintenance/)")
                        st.markdown("• [キャンピングカーのバッテリー管理完全ガイド](https://camper-repair.net/blog/battery-guide/)")
                        st.markdown("• [キャンピングカーの冷蔵庫トラブルシューティング](https://camper-repair.net/blog/refrigerator-troubleshooting/)")
                        st.markdown("*より詳しい情報は上記の記事をご覧ください*")
                    
                    # 岡山サポートセンターリンク
                    st.markdown("---")
                    st.markdown("**🏢 岡山キャンピングカー修理サポートセンター**")
                    st.markdown("📞 **電話番号**: 080-206-6622")
                    st.markdown("⏰ **営業時間**: 年中無休（9:00〜21:00）")
                    st.markdown("*※不在時は折り返しお電話差し上げます*")
                    st.markdown("💬 **メールでのご相談**: [お問合わせフォーム](https://camper-repair.net/contact/)")
                    st.markdown("*直接スタッフと相談したいときは直接お電話いただくか、メールでのご相談も承ります*")
                    st.markdown("**⚠️ 重要**: 安全な修理作業のため、複雑な修理や専門的な作業が必要な場合は、必ず岡山キャンピングカー修理サポートセンターにご相談ください。")
                    
                    # AIメッセージを履歴に追加
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")
    
    # ユーザー入力（常に最後に表示）
    if prompt := st.chat_input("キャンピングカーの修理について質問してください..."):
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AIの回答を生成
        with st.chat_message("assistant", avatar="https://camper-repair.net/blog/wp-content/uploads/2025/05/dummy_staff_01-150x138-1.png"):
            with st.spinner("🔧 修理アドバイスを生成中..."):
                try:
                    # ドキュメントとワークフローを取得
                    documents = initialize_database()
                    app_flow = build_workflow()
                    
                    # RAGで関連文書を取得
                    document_snippet = rag_retrieve(prompt, documents)
                    
                    # プロンプトを構築
                    content = template.format(document_snippet=document_snippet, question=prompt)
                    
                    # 会話履歴を構築（最新の5件のみ）
                    history = []
                    recent_messages = st.session_state.messages[-5:-1]  # 最新の5件のみ
                    for msg in recent_messages:
                        if msg["role"] == "user":
                            history.append(HumanMessage(content=msg["content"]))
                        else:
                            history.append(AIMessage(content=msg["content"]))
                    
                    # 新しいメッセージを追加
                    inputs = history + [HumanMessage(content=content)]
                    thread = {"configurable": {"thread_id": st.session_state.conversation_id}}
                    
                    # 回答を生成
                    response = ""
                    for event in app_flow.stream({"messages": inputs}, thread, stream_mode="values"):
                        if "messages" in event and event["messages"]:
                            response = event["messages"][-1].content
                    
                    # 回答を表示
                    st.markdown(response)
                    
                    # ブログ記事の検索と表示
                    blog_articles = search_blog_articles(prompt)
                    st.markdown("---")
                    st.markdown("**📝 関連ブログ記事**")
                    if blog_articles:
                        for article in blog_articles:
                            st.markdown(f"• [{article['title']}]({article['url']})")
                        st.markdown("*より詳しい情報は上記の記事をご覧ください*")
                    else:
                        st.markdown("• [キャンピングカーのエアコンメンテナンスガイド](https://camper-repair.net/blog/aircon-maintenance/)")
                        st.markdown("• [キャンピングカーのバッテリー管理完全ガイド](https://camper-repair.net/blog/battery-guide/)")
                        st.markdown("• [キャンピングカーの冷蔵庫トラブルシューティング](https://camper-repair.net/blog/refrigerator-troubleshooting/)")
                        st.markdown("*より詳しい情報は上記の記事をご覧ください*")
                    
                    # 岡山サポートセンターリンク
                    st.markdown("---")
                    st.markdown("**🏢 岡山キャンピングカー修理サポートセンター**")
                    st.markdown("📞 **電話番号**: 080-206-6622")
                    st.markdown("⏰ **営業時間**: 年中無休（9:00〜21:00）")
                    st.markdown("*※不在時は折り返しお電話差し上げます*")
                    st.markdown("💬 **メールでのご相談**: [お問合わせフォーム](https://camper-repair.net/contact/)")
                    st.markdown("*直接スタッフと相談したいときは直接お電話いただくか、メールでのご相談も承ります*")
                    st.markdown("**⚠️ 重要**: 安全な修理作業のため、複雑な修理や専門的な作業が必要な場合は、必ず岡山キャンピングカー修理サポートセンターにご相談ください。")
                    
                    # AIメッセージを履歴に追加
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main() 