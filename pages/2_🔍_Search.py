"""
Search - 記事検索・詳細閲覧

過去の記事を検索、フィルタリング、詳細閲覧するページです。
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# ページ設定
st.set_page_config(
    page_title="Search - 記事検索",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 記事検索・詳細閲覧")
st.markdown("過去の記事を検索・フィルタリングして詳細を確認します")
st.markdown("---")


@st.cache_data
def load_all_articles():
    """全ての週次データから記事を読み込む"""
    weekly_data_dir = Path("reports/weekly_data")
    if not weekly_data_dir.exists():
        return []

    all_articles = []
    for file in sorted(weekly_data_dir.glob("*.json")):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            report_date = data['metadata']['report_date']

            for article in data.get('articles', []):
                article['report_date'] = report_date
                all_articles.append(article)

    return all_articles


# データ読み込み
articles = load_all_articles()

if not articles:
    st.error("週次データが見つかりません。`python weekly_research.py` を実行してください。")
    st.stop()

# --- サイドバー: 検索フィルター ---
st.sidebar.header("🔍 検索フィルター")

# キーワード検索
search_query = st.sidebar.text_input(
    "キーワード検索",
    placeholder="タイトル、要約、ポイントから検索...",
    help="記事のタイトル、要約、重要ポイントを全文検索します"
)

# 日付範囲フィルター
st.sidebar.subheader("📅 期間")
all_dates = sorted(set(article['report_date'] for article in articles))
if len(all_dates) >= 2:
    date_range = st.sidebar.date_input(
        "レポート日の範囲",
        value=(datetime.strptime(all_dates[0], "%Y-%m-%d").date(),
               datetime.strptime(all_dates[-1], "%Y-%m-%d").date()),
        help="レポート日でフィルタリング"
    )
else:
    date_range = None
    st.sidebar.info("日付フィルターには2週間以上のデータが必要です")

# カテゴリフィルター
st.sidebar.subheader("🏷️ カテゴリ")
all_categories = sorted(set(
    article.get('category', '不明')
    for article in articles
    if article.get('category')
))
selected_categories = st.sidebar.multiselect(
    "カテゴリを選択",
    options=all_categories,
    default=all_categories,
    help="複数選択可能"
)

# 企業フィルター
st.sidebar.subheader("🏢 企業")
all_companies = sorted(set(
    company
    for article in articles
    for company in article.get('related_companies', [])
    if company
))

if all_companies:
    selected_companies = st.sidebar.multiselect(
        "企業を選択",
        options=['(全て)'] + all_companies,
        default=['(全て)'],
        help="企業でフィルタリング"
    )
else:
    selected_companies = ['(全て)']
    st.sidebar.info("企業データがありません")

# 製造業関連フィルター
st.sidebar.subheader("🏭 製造業関連")
manufacturing_filter = st.sidebar.radio(
    "製造業関連のみ表示",
    options=['全て', 'あり', 'なし'],
    index=0
)

# 信頼度スコアフィルター
st.sidebar.subheader("⭐ 信頼度スコア")
min_confidence = st.sidebar.slider(
    "最小信頼度スコア",
    min_value=0.0,
    max_value=1.0,
    value=0.0,
    step=0.1,
    help="この値以上の信頼度スコアを持つ記事のみ表示"
)

# --- フィルタリング処理 ---
filtered_articles = articles.copy()

# キーワード検索
if search_query:
    search_lower = search_query.lower()
    filtered_articles = [
        article for article in filtered_articles
        if (search_lower in article.get('title', '').lower() or
            search_lower in article.get('summary_japanese', '').lower() or
            any(search_lower in point.lower() for point in article.get('key_points', [])))
    ]

# 日付範囲
if date_range and len(date_range) == 2:
    start_date_str = date_range[0].strftime("%Y-%m-%d")
    end_date_str = date_range[1].strftime("%Y-%m-%d")
    filtered_articles = [
        article for article in filtered_articles
        if start_date_str <= article.get('report_date', '') <= end_date_str
    ]

# カテゴリ
if selected_categories:
    filtered_articles = [
        article for article in filtered_articles
        if article.get('category', '不明') in selected_categories
    ]

# 企業
if selected_companies and '(全て)' not in selected_companies:
    filtered_articles = [
        article for article in filtered_articles
        if any(company in article.get('related_companies', []) for company in selected_companies)
    ]

# 製造業関連
if manufacturing_filter != '全て':
    filtered_articles = [
        article for article in filtered_articles
        if article.get('manufacturing_relevance', 'なし') == manufacturing_filter
    ]

# 信頼度スコア
filtered_articles = [
    article for article in filtered_articles
    if article.get('confidence_score', 0) >= min_confidence
]

# --- メインコンテンツ ---
st.subheader(f"📊 検索結果: {len(filtered_articles)}件 / {len(articles)}件")

# ソートオプション
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    sort_by = st.selectbox(
        "並び替え",
        options=['信頼度スコア（降順）', '公開日（新しい順）', '公開日（古い順）', 'レポート日（新しい順）', 'レポート日（古い順）'],
        index=0
    )

with col2:
    items_per_page = st.selectbox(
        "表示件数",
        options=[10, 25, 50, 100],
        index=1
    )

with col3:
    if st.button("📥 CSVエクスポート"):
        # CSVエクスポート用のDataFrame作成
        export_data = []
        for article in filtered_articles:
            export_data.append({
                'タイトル': article.get('title', ''),
                'URL': article.get('url', ''),
                '情報源': article.get('source', ''),
                '公開日': article.get('published_date', ''),
                'レポート日': article.get('report_date', ''),
                '地域': article.get('region', ''),
                'カテゴリ': article.get('category', ''),
                '関連企業': ', '.join(article.get('related_companies', [])),
                '製造業関連': article.get('manufacturing_relevance', ''),
                '信頼度スコア': article.get('confidence_score', 0),
                '要約': article.get('summary_japanese', ''),
                'タグ': ', '.join(article.get('tags', []))
            })

        df_export = pd.DataFrame(export_data)
        csv = df_export.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv,
            file_name=f"articles_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# ソート処理
if sort_by == '信頼度スコア（降順）':
    filtered_articles = sorted(filtered_articles, key=lambda x: x.get('confidence_score', 0), reverse=True)
elif sort_by == '公開日（新しい順）':
    filtered_articles = sorted(filtered_articles, key=lambda x: x.get('published_date', ''), reverse=True)
elif sort_by == '公開日（古い順）':
    filtered_articles = sorted(filtered_articles, key=lambda x: x.get('published_date', ''))
elif sort_by == 'レポート日（新しい順）':
    filtered_articles = sorted(filtered_articles, key=lambda x: x.get('report_date', ''), reverse=True)
elif sort_by == 'レポート日（古い順）':
    filtered_articles = sorted(filtered_articles, key=lambda x: x.get('report_date', ''))

st.markdown("---")

# ページネーション
total_pages = (len(filtered_articles) - 1) // items_per_page + 1 if filtered_articles else 1
current_page = st.number_input(
    f"ページ（全{total_pages}ページ）",
    min_value=1,
    max_value=total_pages,
    value=1,
    step=1
)

start_idx = (current_page - 1) * items_per_page
end_idx = start_idx + items_per_page
page_articles = filtered_articles[start_idx:end_idx]

# --- 記事一覧表示 ---
if not page_articles:
    st.info("検索条件に一致する記事が見つかりませんでした。フィルターを調整してください。")
else:
    for i, article in enumerate(page_articles, start=start_idx + 1):
        with st.expander(
            f"**{i}. {article.get('title', '(タイトルなし)')}** | "
            f"信頼度: {article.get('confidence_score', 0):.2f} | "
            f"{article.get('source', '不明')} | "
            f"{article.get('published_date', '不明')}"
        ):
            # 2列レイアウト
            col_detail_left, col_detail_right = st.columns([2, 1])

            with col_detail_left:
                # 要約
                st.markdown("### 📝 要約")
                st.write(article.get('summary_japanese', '要約なし'))

                # 重要ポイント
                st.markdown("### 🔑 重要ポイント")
                for point in article.get('key_points', []):
                    st.markdown(f"- {point}")

                # 製造業との関連性
                if article.get('manufacturing_relevance') == 'あり':
                    st.markdown("### 🏭 製造業との関連性")
                    st.info(article.get('relevance_reason', '記載なし'))

            with col_detail_right:
                # メタ情報
                st.markdown("### 📌 記事情報")
                st.write(f"**情報源**: {article.get('source', '不明')}")
                st.write(f"**公開日**: {article.get('published_date', '不明')}")
                st.write(f"**レポート日**: {article.get('report_date', '不明')}")
                st.write(f"**地域**: {article.get('region', '不明')}")
                st.write(f"**カテゴリ**: {article.get('category', '不明')}")
                st.write(f"**製造業関連**: {article.get('manufacturing_relevance', '不明')}")
                st.write(f"**信頼度スコア**: {article.get('confidence_score', 0):.2f}")

                # 関連企業
                if article.get('related_companies'):
                    st.markdown("### 🏢 関連企業")
                    for company in article['related_companies']:
                        st.markdown(f"- {company}")

                # タグ
                if article.get('tags'):
                    st.markdown("### 🏷️ タグ")
                    tags_display = ' '.join([f"`{tag}`" for tag in article['tags']])
                    st.markdown(tags_display)

                # URLリンク
                st.markdown("---")
                if article.get('url'):
                    st.markdown(f"[🔗 記事を開く]({article['url']})")

# ページネーション（下部）
if total_pages > 1:
    st.markdown("---")
    col_prev, col_info, col_next = st.columns([1, 2, 1])

    with col_prev:
        if current_page > 1:
            if st.button("⬅️ 前のページ"):
                st.rerun()

    with col_info:
        st.markdown(f"<div style='text-align: center;'>ページ {current_page} / {total_pages}</div>", unsafe_allow_html=True)

    with col_next:
        if current_page < total_pages:
            if st.button("次のページ ➡️"):
                st.rerun()

# フッター
st.markdown("---")
st.caption("💡 ヒント: 左のサイドバーでフィルターを調整して絞り込みができます")
