"""
トレンド分析ダッシュボード - メインページ

週次レポートの過去データを可視化し、トレンド分析を行うダッシュボードです。
"""

import streamlit as st
from pathlib import Path

# ページ設定
st.set_page_config(
    page_title="週次レポート - トレンド分析ダッシュボード",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .feature-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# サイドバー
with st.sidebar:
    st.image("https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg", width=50)
    st.title("週次レポート分析")
    st.markdown("---")

    # データ状態の確認
    weekly_data_dir = Path("reports/weekly_data")
    trends_dir = Path("reports/trends")

    if weekly_data_dir.exists():
        weekly_files = list(weekly_data_dir.glob("*.json"))
        st.metric("保存されている週次データ", f"{len(weekly_files)}週分")
    else:
        st.warning("週次データが見つかりません")

    if trends_dir.exists():
        st.success("✓ トレンドデータ生成済み")
    else:
        st.info("トレンドデータを生成してください")

    st.markdown("---")
    st.markdown("""
    ### 📖 使い方

    左のナビゲーションから各ページを選択してください：

    - **🏠 Home**: 概要ダッシュボード
    - **🔍 Search**: 記事検索・詳細閲覧

    *(Phase 3以降で追加予定)*
    - **📈 Trends**: トレンド分析
    - **🏢 Companies**: 企業動向
    """)

# メインコンテンツ
st.markdown('<div class="main-header">📊 週次レポート - トレンド分析ダッシュボード</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">スキルマネジメント・タレントマネジメントの海外動向を可視化</div>', unsafe_allow_html=True)

st.markdown("---")

# 紹介セクション
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>🎯 このダッシュボードについて</h3>
        <p>
        週次で自動生成される「スキルマネジメント・タレントマネジメント」に関する
        海外トレンドレポートの過去データを分析・可視化するツールです。
        </p>
        <ul>
            <li>時系列でのトレンド変化を追跡</li>
            <li>キーワード・企業・カテゴリの分析</li>
            <li>記事の検索・フィルタリング</li>
            <li>詳細な記事内容の閲覧</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>🚀 実装状況</h3>
        <p><strong>Phase 1 (完了)</strong></p>
        <ul>
            <li>✅ 週次データの構造化保存</li>
            <li>✅ トレンドデータの集計</li>
            <li>✅ データ基盤の整備</li>
        </ul>
        <p><strong>Phase 2 (実装中)</strong></p>
        <ul>
            <li>🔄 基本ダッシュボード</li>
            <li>🔄 記事検索機能</li>
        </ul>
        <p><strong>Phase 3-5 (予定)</strong></p>
        <ul>
            <li>⏳ 高度なトレンド分析</li>
            <li>⏳ 企業動向分析</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# クイックスタート
st.subheader("🏁 クイックスタート")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **ステップ 1**

    左のサイドバーから
    **🏠 Home** を選択して
    全体の概要を確認
    """)

with col2:
    st.info("""
    **ステップ 2**

    **🔍 Search** で
    特定の記事を検索・
    詳細を閲覧
    """)

with col3:
    st.info("""
    **ステップ 3**

    (Phase 3以降)
    **📈 Trends** で
    時系列の変化を分析
    """)

# データ生成方法
with st.expander("📚 データの生成方法"):
    st.markdown("""
    ### 週次レポートの生成

    ```bash
    # レポート生成（週次データも自動保存）
    python weekly_research.py
    ```

    ### トレンドデータの更新

    ```bash
    # 過去の週次データから集計
    python analyze_trends.py
    ```

    ### テストデータの作成

    ```bash
    # 開発用のサンプルデータ生成
    python create_test_data.py
    python analyze_trends.py
    ```

    GitHub Actionsによる自動実行でも、週次データは自動的に保存されます。
    """)

# フッター
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>Powered by Gemini 2.5 Flash + Tavily Search API + LangGraph</p>
    <p>📧 メール送信機能 | 🤖 自動実行（GitHub Actions）</p>
</div>
""", unsafe_allow_html=True)
