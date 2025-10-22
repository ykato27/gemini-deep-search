"""
Home - 概要ダッシュボード

KPI指標、記事数推移、カテゴリ分布などの全体像を表示します。
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ページ設定
st.set_page_config(
    page_title="Home - 概要ダッシュボード",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 概要ダッシュボード")
st.markdown("週次レポートの全体像を把握します")
st.markdown("---")


@st.cache_data
def load_summary_data():
    """週次サマリーデータを読み込む"""
    summary_path = Path("reports/trends/summary.json")
    if not summary_path.exists():
        return None

    with open(summary_path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_weekly_data():
    """全ての週次データを読み込む"""
    weekly_data_dir = Path("reports/weekly_data")
    if not weekly_data_dir.exists():
        return []

    data = []
    for file in sorted(weekly_data_dir.glob("*.json")):
        with open(file, "r", encoding="utf-8") as f:
            data.append(json.load(f))

    return data


@st.cache_data
def load_category_trends():
    """カテゴリトレンドデータを読み込む"""
    categories_path = Path("reports/trends/categories.json")
    if not categories_path.exists():
        return None

    with open(categories_path, "r", encoding="utf-8") as f:
        return json.load(f)


# データ読み込み
summary_data = load_summary_data()
weekly_data = load_weekly_data()
category_trends = load_category_trends()

# データチェック
if not summary_data:
    st.error("トレンドデータが見つかりません。`python analyze_trends.py` を実行してください。")
    st.stop()

# DataFrameに変換
df_summary = pd.DataFrame(summary_data)
df_summary['report_date'] = pd.to_datetime(df_summary['report_date'])

# --- KPIカード ---
st.subheader("📊 主要指標（KPI）")

col1, col2, col3, col4 = st.columns(4)

# 総記事数
total_articles = df_summary['article_count'].sum()
latest_articles = df_summary.iloc[-1]['article_count'] if len(df_summary) > 0 else 0
prev_articles = df_summary.iloc[-2]['article_count'] if len(df_summary) > 1 else latest_articles
article_change = latest_articles - prev_articles
article_change_pct = (article_change / prev_articles * 100) if prev_articles > 0 else 0

with col1:
    st.metric(
        label="総記事数",
        value=f"{total_articles}件",
        delta=f"{article_change:+d}件 ({article_change_pct:+.1f}%)",
        help="全期間での収集記事数"
    )

# 今週の記事数
with col2:
    st.metric(
        label="今週の記事数",
        value=f"{latest_articles}件",
        help="最新週の記事数"
    )

# 製造業関連記事の割合
total_manufacturing = df_summary['manufacturing_related_count'].sum()
manufacturing_ratio = (total_manufacturing / total_articles * 100) if total_articles > 0 else 0
latest_manufacturing = df_summary.iloc[-1]['manufacturing_related_count'] if len(df_summary) > 0 else 0
prev_manufacturing_ratio = (df_summary.iloc[-2]['manufacturing_related_count'] / prev_articles * 100) if len(df_summary) > 1 and prev_articles > 0 else manufacturing_ratio
manufacturing_ratio_change = manufacturing_ratio - prev_manufacturing_ratio

with col3:
    st.metric(
        label="製造業関連",
        value=f"{manufacturing_ratio:.1f}%",
        delta=f"{manufacturing_ratio_change:+.1f}%",
        help="製造業に関連する記事の割合"
    )

# 平均信頼度スコア
avg_confidence = df_summary['avg_confidence_score'].mean()
latest_confidence = df_summary.iloc[-1]['avg_confidence_score'] if len(df_summary) > 0 else 0
prev_confidence = df_summary.iloc[-2]['avg_confidence_score'] if len(df_summary) > 1 else latest_confidence
confidence_change = latest_confidence - prev_confidence

with col4:
    st.metric(
        label="平均信頼度スコア",
        value=f"{latest_confidence:.2f}",
        delta=f"{confidence_change:+.2f}",
        help="記事の信頼性評価（0.0-1.0）"
    )

st.markdown("---")

# --- グラフセクション ---
col_left, col_right = st.columns(2)

# 左列: 記事数推移グラフ
with col_left:
    st.subheader("📈 記事数推移")

    fig_articles = go.Figure()

    fig_articles.add_trace(go.Scatter(
        x=df_summary['report_date'],
        y=df_summary['article_count'],
        mode='lines+markers',
        name='記事数',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8),
        hovertemplate='%{x|%Y-%m-%d}<br>記事数: %{y}件<extra></extra>'
    ))

    fig_articles.update_layout(
        xaxis_title="レポート日",
        yaxis_title="記事数",
        hovermode='x unified',
        height=400,
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(fig_articles, use_container_width=True)

# 右列: カテゴリ分布の推移
with col_right:
    st.subheader("📂 カテゴリ分布の推移")

    if category_trends:
        # データを整形
        category_data = []
        for category, trend in category_trends.items():
            for item in trend:
                category_data.append({
                    'date': item['date'],
                    'category': category,
                    'count': item['count']
                })

        df_categories = pd.DataFrame(category_data)
        df_categories['date'] = pd.to_datetime(df_categories['date'])

        # 積み上げ棒グラフ
        fig_categories = px.bar(
            df_categories,
            x='date',
            y='count',
            color='category',
            title="",
            labels={'date': 'レポート日', 'count': '記事数', 'category': 'カテゴリ'},
            height=400
        )

        fig_categories.update_layout(
            xaxis_title="レポート日",
            yaxis_title="記事数",
            legend_title="カテゴリ",
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(fig_categories, use_container_width=True)
    else:
        st.info("カテゴリトレンドデータがありません")

st.markdown("---")

# --- 製造業関連記事の割合推移 ---
st.subheader("🏭 製造業関連記事の割合推移")

# 割合を計算
df_summary['manufacturing_ratio'] = (
    df_summary['manufacturing_related_count'] / df_summary['article_count'] * 100
).fillna(0)

fig_manufacturing = go.Figure()

fig_manufacturing.add_trace(go.Scatter(
    x=df_summary['report_date'],
    y=df_summary['manufacturing_ratio'],
    mode='lines+markers',
    name='製造業関連割合',
    fill='tozeroy',
    line=dict(color='#2ca02c', width=3),
    marker=dict(size=8),
    hovertemplate='%{x|%Y-%m-%d}<br>割合: %{y:.1f}%<extra></extra>'
))

fig_manufacturing.update_layout(
    xaxis_title="レポート日",
    yaxis_title="製造業関連割合 (%)",
    hovermode='x unified',
    height=350,
    margin=dict(l=0, r=0, t=10, b=0)
)

st.plotly_chart(fig_manufacturing, use_container_width=True)

st.markdown("---")

# --- 最新記事一覧 ---
st.subheader("📰 最新週の注目記事 TOP5")

if weekly_data:
    latest_week = weekly_data[-1]
    articles = latest_week.get('articles', [])

    # 信頼度スコアでソート
    sorted_articles = sorted(
        articles,
        key=lambda x: x.get('confidence_score', 0),
        reverse=True
    )[:5]

    for i, article in enumerate(sorted_articles, 1):
        with st.expander(f"{i}. {article.get('title', '(タイトルなし)')} (信頼度: {article.get('confidence_score', 0):.2f})"):
            col_a, col_b = st.columns([2, 1])

            with col_a:
                st.markdown(f"**📝 要約**")
                st.write(article.get('summary_japanese', '要約なし'))

                st.markdown(f"**🔑 重要ポイント**")
                for point in article.get('key_points', []):
                    st.markdown(f"- {point}")

            with col_b:
                st.markdown(f"**📌 情報**")
                st.write(f"**情報源**: {article.get('source', '不明')}")
                st.write(f"**公開日**: {article.get('published_date', '不明')}")
                st.write(f"**地域**: {article.get('region', '不明')}")
                st.write(f"**カテゴリ**: {article.get('category', '不明')}")
                st.write(f"**製造業関連**: {article.get('manufacturing_relevance', '不明')}")

                if article.get('related_companies'):
                    st.write(f"**関連企業**: {', '.join(article['related_companies'])}")

                if article.get('tags'):
                    st.write(f"**タグ**: {', '.join(article['tags'][:5])}")

                st.markdown(f"[🔗 記事を開く]({article.get('url', '#')})")

else:
    st.info("週次データがありません")

# フッター
st.markdown("---")
st.caption("💡 ヒント: 左のサイドバーから「🔍 Search」で記事を検索できます")
