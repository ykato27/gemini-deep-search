"""
Trends - トレンド分析

キーワード・タグの時系列トレンドを分析します。
"""

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ページ設定
st.set_page_config(
    page_title="Trends - トレンド分析",
    page_icon="📈",
    layout="wide"
)

st.title("📈 トレンド分析")
st.markdown("キーワード・タグの出現頻度を時系列で分析します")
st.markdown("---")


@st.cache_data
def load_keyword_trends():
    """キーワードトレンドデータを読み込む"""
    keywords_path = Path("reports/trends/keywords.json")
    if not keywords_path.exists():
        return None

    with open(keywords_path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_summary_data():
    """週次サマリーデータを読み込む"""
    summary_path = Path("reports/trends/summary.json")
    if not summary_path.exists():
        return None

    with open(summary_path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def calculate_trend_changes(keyword_trends):
    """キーワードの前週比変化を計算"""
    changes = {}

    for keyword, trend_data in keyword_trends.items():
        if len(trend_data) < 2:
            continue

        # 最新週と前週の出現回数
        latest = trend_data[-1]['count']
        previous = trend_data[-2]['count']

        # 変化率を計算
        if previous > 0:
            change_pct = ((latest - previous) / previous) * 100
        elif latest > 0:
            change_pct = 100  # 前週0から出現
        else:
            change_pct = 0  # 両方とも0

        change_abs = latest - previous

        changes[keyword] = {
            'latest': latest,
            'previous': previous,
            'change_abs': change_abs,
            'change_pct': change_pct
        }

    return changes


# データ読み込み
keyword_trends = load_keyword_trends()
summary_data = load_summary_data()

# データチェック
if not keyword_trends:
    st.error("トレンドデータが見つかりません。`python analyze_trends.py` を実行してください。")
    st.stop()

# トレンド変化を計算
trend_changes = calculate_trend_changes(keyword_trends)

# --- サイドバー: フィルター ---
st.sidebar.header("🎛️ フィルター設定")

# 期間選択
st.sidebar.subheader("📅 表示期間")
all_dates = sorted(set(
    item['date'] for trend in keyword_trends.values() for item in trend
))

if len(all_dates) >= 2:
    period_options = {
        f"全期間（{len(all_dates)}週）": len(all_dates),
        "過去4週": min(4, len(all_dates)),
        "過去8週": min(8, len(all_dates)),
        "過去12週": min(12, len(all_dates)),
    }
    selected_period_label = st.sidebar.selectbox(
        "期間を選択",
        options=list(period_options.keys()),
        index=0
    )
    num_weeks = period_options[selected_period_label]
    display_dates = all_dates[-num_weeks:]
else:
    display_dates = all_dates
    st.sidebar.info("データが不足しています")

# 最小出現回数フィルター
st.sidebar.subheader("🔢 最小出現回数")
min_count = st.sidebar.slider(
    "全期間での最小出現回数",
    min_value=0,
    max_value=20,
    value=2,
    help="この回数以上出現したキーワードのみ表示"
)

# キーワードフィルタリング
filtered_keywords = {
    keyword: trend
    for keyword, trend in keyword_trends.items()
    if sum(item['count'] for item in trend) >= min_count
}

st.sidebar.markdown(f"**表示対象**: {len(filtered_keywords)}キーワード / {len(keyword_trends)}キーワード")

# --- 急上昇/減少トレンド ---
st.subheader("🔥 急上昇・急減少キーワード")

col_rising, col_falling = st.columns(2)

# 急上昇キーワード（前週比+30%以上）
rising_keywords = sorted(
    [
        (keyword, data)
        for keyword, data in trend_changes.items()
        if data['change_pct'] >= 30 and data['latest'] >= 2
    ],
    key=lambda x: x[1]['change_pct'],
    reverse=True
)[:10]

with col_rising:
    st.markdown("### 🔥 急上昇キーワード（前週比+30%以上）")

    if rising_keywords:
        for i, (keyword, data) in enumerate(rising_keywords, 1):
            with st.container():
                st.markdown(
                    f"**{i}. {keyword}** "
                    f"<span style='color: red; font-weight: bold;'>+{data['change_pct']:.0f}%</span> "
                    f"({data['previous']}回 → {data['latest']}回)",
                    unsafe_allow_html=True
                )
    else:
        st.info("該当するキーワードがありません")

# 急減少キーワード（前週比-30%以上）
falling_keywords = sorted(
    [
        (keyword, data)
        for keyword, data in trend_changes.items()
        if data['change_pct'] <= -30 and data['previous'] >= 2
    ],
    key=lambda x: x[1]['change_pct']
)[:10]

with col_falling:
    st.markdown("### ❄️ 急減少キーワード（前週比-30%以上）")

    if falling_keywords:
        for i, (keyword, data) in enumerate(falling_keywords, 1):
            with st.container():
                st.markdown(
                    f"**{i}. {keyword}** "
                    f"<span style='color: blue; font-weight: bold;'>{data['change_pct']:.0f}%</span> "
                    f"({data['previous']}回 → {data['latest']}回)",
                    unsafe_allow_html=True
                )
    else:
        st.info("該当するキーワードがありません")

st.markdown("---")

# --- キーワードランキング ---
st.subheader("🏆 キーワード出現頻度ランキング（全期間）")

# 総出現回数でソート
keyword_ranking = sorted(
    [
        (keyword, sum(item['count'] for item in trend))
        for keyword, trend in filtered_keywords.items()
    ],
    key=lambda x: x[1],
    reverse=True
)[:20]

col_rank1, col_rank2 = st.columns(2)

with col_rank1:
    st.markdown("### TOP 1-10")
    for i, (keyword, count) in enumerate(keyword_ranking[:10], 1):
        st.markdown(f"{i}. **{keyword}**: {count}回")

with col_rank2:
    st.markdown("### TOP 11-20")
    for i, (keyword, count) in enumerate(keyword_ranking[10:20], 11):
        st.markdown(f"{i}. **{keyword}**: {count}回")

st.markdown("---")

# --- キーワード時系列グラフ ---
st.subheader("📊 キーワード時系列トレンド")

# キーワード選択（マルチセレクト）
top_keywords = [kw for kw, count in keyword_ranking[:20]]

selected_keywords = st.multiselect(
    "表示するキーワードを選択（複数選択可）",
    options=top_keywords,
    default=top_keywords[:5] if len(top_keywords) >= 5 else top_keywords[:3],
    help="最大10個まで選択可能"
)

if not selected_keywords:
    st.info("キーワードを選択してください")
else:
    # データを整形
    chart_data = []
    for keyword in selected_keywords[:10]:  # 最大10個まで
        trend = keyword_trends[keyword]
        for item in trend:
            if item['date'] in display_dates:
                chart_data.append({
                    'date': item['date'],
                    'keyword': keyword,
                    'count': item['count']
                })

    df_chart = pd.DataFrame(chart_data)
    df_chart['date'] = pd.to_datetime(df_chart['date'])

    # Plotlyで折れ線グラフ作成
    fig = px.line(
        df_chart,
        x='date',
        y='count',
        color='keyword',
        markers=True,
        title="",
        labels={'date': '日付', 'count': '出現回数', 'keyword': 'キーワード'},
        height=500
    )

    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8)
    )

    fig.update_layout(
        xaxis_title="レポート日",
        yaxis_title="出現回数",
        legend_title="キーワード",
        hovermode='x unified',
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

    # 統計情報
    with st.expander("📊 選択キーワードの統計情報"):
        stats_data = []
        for keyword in selected_keywords:
            trend = keyword_trends[keyword]
            counts = [item['count'] for item in trend if item['date'] in display_dates]

            stats_data.append({
                'キーワード': keyword,
                '総出現回数': sum(counts),
                '平均': f"{sum(counts) / len(counts):.1f}" if counts else 0,
                '最大': max(counts) if counts else 0,
                '最小': min(counts) if counts else 0,
                '最新週': counts[-1] if counts else 0
            })

        df_stats = pd.DataFrame(stats_data)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)

st.markdown("---")

# --- キーワード比較（バーチャート） ---
st.subheader("📊 キーワード比較（最新週 vs 過去平均）")

if len(display_dates) >= 2:
    # 比較対象キーワード選択
    comparison_keywords = st.multiselect(
        "比較するキーワードを選択",
        options=top_keywords,
        default=top_keywords[:5] if len(top_keywords) >= 5 else top_keywords[:3],
        help="最新週と過去平均を比較します",
        key="comparison_select"
    )

    if comparison_keywords:
        comparison_data = []

        for keyword in comparison_keywords[:10]:
            trend = keyword_trends[keyword]
            counts = [item['count'] for item in trend if item['date'] in display_dates]

            if len(counts) >= 2:
                latest = counts[-1]
                avg_past = sum(counts[:-1]) / len(counts[:-1])

                comparison_data.append({
                    'キーワード': keyword,
                    '最新週': latest,
                    '過去平均': round(avg_past, 1)
                })

        if comparison_data:
            df_comparison = pd.DataFrame(comparison_data)

            # 棒グラフ
            fig_comparison = go.Figure()

            fig_comparison.add_trace(go.Bar(
                name='最新週',
                x=df_comparison['キーワード'],
                y=df_comparison['最新週'],
                marker_color='#1f77b4'
            ))

            fig_comparison.add_trace(go.Bar(
                name='過去平均',
                x=df_comparison['キーワード'],
                y=df_comparison['過去平均'],
                marker_color='#ff7f0e'
            ))

            fig_comparison.update_layout(
                barmode='group',
                xaxis_title="キーワード",
                yaxis_title="出現回数",
                legend_title="",
                height=400,
                margin=dict(l=0, r=0, t=10, b=0)
            )

            st.plotly_chart(fig_comparison, use_container_width=True)
        else:
            st.info("比較データがありません")
    else:
        st.info("キーワードを選択してください")
else:
    st.info("比較には2週間以上のデータが必要です")

# フッター
st.markdown("---")
st.caption("💡 ヒント: サイドバーで期間や最小出現回数を調整できます")
