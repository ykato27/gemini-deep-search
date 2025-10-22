"""
Companies - 企業動向分析

関連企業の出現頻度とトレンドを分析します。
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ページ設定
st.set_page_config(
    page_title="Companies - 企業動向",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 企業動向分析")
st.markdown("記事に登場する企業の動向を分析します")
st.markdown("---")


@st.cache_data
def load_company_trends():
    """企業トレンドデータを読み込む"""
    companies_path = Path("reports/trends/companies.json")
    if not companies_path.exists():
        return None

    with open(companies_path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_category_trends():
    """カテゴリトレンドデータを読み込む"""
    categories_path = Path("reports/trends/categories.json")
    if not categories_path.exists():
        return None

    with open(categories_path, "r", encoding="utf-8") as f:
        return json.load(f)


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


@st.cache_data
def calculate_company_trend_changes(company_trends):
    """企業の前週比変化を計算"""
    changes = {}

    for company, trend_data in company_trends.items():
        if len(trend_data) < 2:
            continue

        latest = trend_data[-1]['count']
        previous = trend_data[-2]['count']

        if previous > 0:
            change_pct = ((latest - previous) / previous) * 100
        elif latest > 0:
            change_pct = 100
        else:
            change_pct = 0

        change_abs = latest - previous

        changes[company] = {
            'latest': latest,
            'previous': previous,
            'change_abs': change_abs,
            'change_pct': change_pct
        }

    return changes


# データ読み込み
company_trends = load_company_trends()
category_trends = load_category_trends()
all_articles = load_all_articles()

# データチェック
if not company_trends:
    st.info("企業データがありません。記事に企業情報が含まれていない可能性があります。")
    st.stop()

if not company_trends or len(company_trends) == 0:
    st.warning("企業データが見つかりません。")
    st.stop()

# 企業トレンド変化を計算
trend_changes = calculate_company_trend_changes(company_trends)

# --- 企業ランキング ---
st.subheader("🏆 企業出現頻度ランキング（全期間）")

# 総出現回数でソート
company_ranking = sorted(
    [
        (company, sum(item['count'] for item in trend))
        for company, trend in company_trends.items()
    ],
    key=lambda x: x[1],
    reverse=True
)

if company_ranking:
    # テーブル形式で表示
    rank_data = []
    for i, (company, total_count) in enumerate(company_ranking[:20], 1):
        # 前週比を取得
        if company in trend_changes:
            change = trend_changes[company]
            change_str = f"{change['change_pct']:+.0f}%"
            latest_count = change['latest']
        else:
            change_str = "-"
            latest_count = 0

        # 主なカテゴリを取得（記事から）
        company_articles = [
            a for a in all_articles
            if company in a.get('related_companies', [])
        ]
        categories = [a.get('category', '不明') for a in company_articles]
        main_category = max(set(categories), key=categories.count) if categories else '不明'

        rank_data.append({
            '順位': i,
            '企業名': company,
            '総出現回数': total_count,
            '最新週': latest_count,
            '前週比': change_str,
            '主なカテゴリ': main_category
        })

    df_ranking = pd.DataFrame(rank_data)
    st.dataframe(df_ranking, use_container_width=True, hide_index=True)

    st.markdown("---")

    # --- 企業別トレンドグラフ ---
    st.subheader("📊 企業別トレンドグラフ")

    # 企業選択
    top_companies = [company for company, count in company_ranking[:20]]

    selected_companies = st.multiselect(
        "表示する企業を選択（複数選択可、最大10社）",
        options=top_companies,
        default=top_companies[:3] if len(top_companies) >= 3 else top_companies,
        help="時系列で企業の出現頻度を比較します"
    )

    if selected_companies:
        # データを整形
        chart_data = []
        for company in selected_companies[:10]:
            trend = company_trends[company]
            for item in trend:
                chart_data.append({
                    'date': item['date'],
                    'company': company,
                    'count': item['count']
                })

        df_chart = pd.DataFrame(chart_data)
        df_chart['date'] = pd.to_datetime(df_chart['date'])

        # 折れ線グラフ
        fig = px.line(
            df_chart,
            x='date',
            y='count',
            color='company',
            markers=True,
            title="",
            labels={'date': '日付', 'count': '出現回数', 'company': '企業'},
            height=500
        )

        fig.update_traces(
            line=dict(width=3),
            marker=dict(size=8)
        )

        fig.update_layout(
            xaxis_title="レポート日",
            yaxis_title="出現回数",
            legend_title="企業",
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

        # 企業別統計
        with st.expander("📊 選択企業の統計情報"):
            stats_data = []
            for company in selected_companies:
                trend = company_trends[company]
                counts = [item['count'] for item in trend]

                stats_data.append({
                    '企業': company,
                    '総出現回数': sum(counts),
                    '平均': f"{sum(counts) / len(counts):.1f}" if counts else 0,
                    '最大': max(counts) if counts else 0,
                    '最新週': counts[-1] if counts else 0
                })

            df_stats = pd.DataFrame(stats_data)
            st.dataframe(df_stats, use_container_width=True, hide_index=True)

    else:
        st.info("企業を選択してください")

    st.markdown("---")

    # --- 企業×カテゴリのヒートマップ ---
    st.subheader("🔥 企業×カテゴリのヒートマップ")

    # 企業×カテゴリの集計
    company_category_matrix = {}
    for company in top_companies[:15]:  # 上位15社
        company_articles = [
            a for a in all_articles
            if company in a.get('related_companies', [])
        ]

        category_counts = {}
        for article in company_articles:
            category = article.get('category', '不明')
            category_counts[category] = category_counts.get(category, 0) + 1

        company_category_matrix[company] = category_counts

    # データフレーム化
    df_matrix = pd.DataFrame(company_category_matrix).T.fillna(0).astype(int)

    if not df_matrix.empty:
        # ヒートマップ
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=df_matrix.values,
            x=df_matrix.columns,
            y=df_matrix.index,
            colorscale='Blues',
            text=df_matrix.values,
            texttemplate='%{text}',
            textfont={"size": 10},
            hovertemplate='企業: %{y}<br>カテゴリ: %{x}<br>記事数: %{z}<extra></extra>'
        ))

        fig_heatmap.update_layout(
            title="",
            xaxis_title="カテゴリ",
            yaxis_title="企業",
            height=max(400, len(df_matrix) * 30),
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("ヒートマップ用のデータがありません")

    st.markdown("---")

    # --- 企業の動向サマリー ---
    st.subheader("📰 企業別の最新記事")

    selected_company_detail = st.selectbox(
        "詳細を表示する企業を選択",
        options=top_companies
    )

    if selected_company_detail:
        company_articles = [
            a for a in all_articles
            if selected_company_detail in a.get('related_companies', [])
        ]

        # 最新5件を表示
        company_articles_sorted = sorted(
            company_articles,
            key=lambda x: x.get('report_date', ''),
            reverse=True
        )[:5]

        if company_articles_sorted:
            st.markdown(f"### {selected_company_detail}の最新記事（最新5件）")

            for i, article in enumerate(company_articles_sorted, 1):
                with st.expander(
                    f"{i}. {article.get('title', '(タイトルなし)')} | "
                    f"{article.get('report_date', '不明')}"
                ):
                    col_a, col_b = st.columns([2, 1])

                    with col_a:
                        st.markdown("**📝 要約**")
                        st.write(article.get('summary_japanese', '要約なし'))

                        st.markdown("**🔑 重要ポイント**")
                        for point in article.get('key_points', []):
                            st.markdown(f"- {point}")

                    with col_b:
                        st.markdown("**📌 情報**")
                        st.write(f"**情報源**: {article.get('source', '不明')}")
                        st.write(f"**公開日**: {article.get('published_date', '不明')}")
                        st.write(f"**カテゴリ**: {article.get('category', '不明')}")
                        st.write(f"**信頼度**: {article.get('confidence_score', 0):.2f}")

                        if article.get('url'):
                            st.markdown(f"[🔗 記事を開く]({article['url']})")
        else:
            st.info(f"{selected_company_detail}の記事が見つかりませんでした")

else:
    st.info("企業データがありません")

# フッター
st.markdown("---")
st.caption("💡 ヒント: 企業を選択してトレンドグラフで比較できます")
