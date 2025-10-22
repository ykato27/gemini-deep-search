"""
トレンド分析スクリプト

過去の週次データ（reports/weekly_data/*.json）を集計し、
時系列のトレンドデータを生成します。

生成されるファイル:
- reports/trends/keywords.json: キーワード出現頻度の時系列データ
- reports/trends/companies.json: 企業出現頻度の時系列データ
- reports/trends/categories.json: カテゴリ分布の時系列データ
- reports/trends/summary.json: 週次サマリーのメタデータ
"""

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def load_weekly_data():
    """週次データを全て読み込む"""
    weekly_data_dir = Path("reports/weekly_data")

    if not weekly_data_dir.exists():
        print("⚠️ reports/weekly_data ディレクトリが見つかりません。")
        return []

    weekly_files = sorted(weekly_data_dir.glob("*.json"))

    if not weekly_files:
        print("⚠️ 週次データファイルが見つかりません。")
        return []

    data = []
    for file in weekly_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data.append(json.load(f))
        except Exception as e:
            print(f"⚠️ {file.name} の読み込みに失敗しました: {e}")

    return data


def analyze_keyword_trends(weekly_data_list):
    """キーワードの時系列トレンドを分析"""
    keyword_trends = defaultdict(list)

    for data in weekly_data_list:
        report_date = data["metadata"]["report_date"]
        articles = data.get("articles", [])

        # 各週のキーワード出現回数をカウント
        keyword_counts = Counter()
        for article in articles:
            tags = article.get("tags", [])
            for tag in tags:
                keyword_counts[tag] += 1

        # 全キーワードについて、その週の出現回数を記録
        for keyword, count in keyword_counts.items():
            keyword_trends[keyword].append({
                "date": report_date,
                "count": count
            })

    # 各キーワードのデータを時系列で完全にする（0埋め）
    all_dates = sorted(set(
        data["metadata"]["report_date"] for data in weekly_data_list
    ))

    complete_trends = {}
    for keyword, trend_data in keyword_trends.items():
        date_counts = {item["date"]: item["count"] for item in trend_data}
        complete_trends[keyword] = [
            {"date": date, "count": date_counts.get(date, 0)}
            for date in all_dates
        ]

    # 総出現回数でソート（トップキーワードを優先）
    sorted_keywords = sorted(
        complete_trends.items(),
        key=lambda x: sum(item["count"] for item in x[1]),
        reverse=True
    )

    return dict(sorted_keywords)


def analyze_company_trends(weekly_data_list):
    """企業の時系列トレンドを分析"""
    company_trends = defaultdict(list)

    for data in weekly_data_list:
        report_date = data["metadata"]["report_date"]
        articles = data.get("articles", [])

        # 各週の企業出現回数をカウント
        company_counts = Counter()
        for article in articles:
            companies = article.get("related_companies", [])
            for company in companies:
                company_counts[company] += 1

        # 全企業について、その週の出現回数を記録
        for company, count in company_counts.items():
            company_trends[company].append({
                "date": report_date,
                "count": count
            })

    # 各企業のデータを時系列で完全にする（0埋め）
    all_dates = sorted(set(
        data["metadata"]["report_date"] for data in weekly_data_list
    ))

    complete_trends = {}
    for company, trend_data in company_trends.items():
        date_counts = {item["date"]: item["count"] for item in trend_data}
        complete_trends[company] = [
            {"date": date, "count": date_counts.get(date, 0)}
            for date in all_dates
        ]

    # 総出現回数でソート（トップ企業を優先）
    sorted_companies = sorted(
        complete_trends.items(),
        key=lambda x: sum(item["count"] for item in x[1]),
        reverse=True
    )

    return dict(sorted_companies)


def analyze_category_trends(weekly_data_list):
    """カテゴリの時系列トレンドを分析"""
    category_trends = defaultdict(list)

    for data in weekly_data_list:
        report_date = data["metadata"]["report_date"]
        category_dist = data.get("extracted_insights", {}).get("category_distribution", {})

        for category, count in category_dist.items():
            category_trends[category].append({
                "date": report_date,
                "count": count
            })

    # 各カテゴリのデータを時系列で完全にする（0埋め）
    all_dates = sorted(set(
        data["metadata"]["report_date"] for data in weekly_data_list
    ))

    complete_trends = {}
    for category, trend_data in category_trends.items():
        date_counts = {item["date"]: item["count"] for item in trend_data}
        complete_trends[category] = [
            {"date": date, "count": date_counts.get(date, 0)}
            for date in all_dates
        ]

    return complete_trends


def generate_summary(weekly_data_list):
    """週次サマリーを生成"""
    summary = []

    for data in weekly_data_list:
        metadata = data["metadata"]
        insights = data.get("extracted_insights", {})

        summary.append({
            "report_date": metadata["report_date"],
            "start_date": metadata.get("start_date", ""),
            "end_date": metadata.get("end_date", ""),
            "article_count": metadata.get("article_count", 0),
            "manufacturing_related_count": insights.get("manufacturing_related_count", 0),
            "avg_confidence_score": insights.get("avg_confidence_score", 0.0),
            "top_keywords": insights.get("top_keywords", [])[:5],
            "top_companies": insights.get("top_companies", [])[:3],
            "execution_time": metadata.get("execution_time", "")
        })

    return sorted(summary, key=lambda x: x["report_date"])


def main():
    """メイン処理"""
    print("=" * 60)
    print("📊 トレンド分析を開始します...")
    print("=" * 60)

    # 週次データの読み込み
    weekly_data_list = load_weekly_data()

    if not weekly_data_list:
        print("❌ 分析するデータがありません。")
        return

    print(f"✓ {len(weekly_data_list)}件の週次データを読み込みました。")

    # トレンドディレクトリの作成
    trends_dir = Path("reports/trends")
    trends_dir.mkdir(parents=True, exist_ok=True)

    # キーワードトレンドの分析
    print("\n📈 キーワードトレンドを分析中...")
    keyword_trends = analyze_keyword_trends(weekly_data_list)
    with open(trends_dir / "keywords.json", "w", encoding="utf-8") as f:
        json.dump(keyword_trends, f, ensure_ascii=False, indent=2)
    print(f"✓ キーワード: {len(keyword_trends)}種類")

    # 企業トレンドの分析
    print("\n🏢 企業トレンドを分析中...")
    company_trends = analyze_company_trends(weekly_data_list)
    with open(trends_dir / "companies.json", "w", encoding="utf-8") as f:
        json.dump(company_trends, f, ensure_ascii=False, indent=2)
    print(f"✓ 企業: {len(company_trends)}社")

    # カテゴリトレンドの分析
    print("\n📂 カテゴリトレンドを分析中...")
    category_trends = analyze_category_trends(weekly_data_list)
    with open(trends_dir / "categories.json", "w", encoding="utf-8") as f:
        json.dump(category_trends, f, ensure_ascii=False, indent=2)
    print(f"✓ カテゴリ: {len(category_trends)}種類")

    # 週次サマリーの生成
    print("\n📋 週次サマリーを生成中...")
    summary = generate_summary(weekly_data_list)
    with open(trends_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"✓ サマリー: {len(summary)}週分")

    # 結果サマリーの表示
    print("\n" + "=" * 60)
    print("✓ トレンド分析完了")
    print("=" * 60)
    print(f"📁 保存先: {trends_dir}/")
    print(f"📊 分析期間: {summary[0]['report_date']} ～ {summary[-1]['report_date']}")
    print(f"📰 総記事数: {sum(s['article_count'] for s in summary)}件")
    print(f"🏭 製造業関連: {sum(s['manufacturing_related_count'] for s in summary)}件")

    # トップキーワード（全期間）
    top_keywords = sorted(
        keyword_trends.items(),
        key=lambda x: sum(item["count"] for item in x[1]),
        reverse=True
    )[:5]
    print(f"\n🏷️ トップキーワード（全期間）:")
    for keyword, trend_data in top_keywords:
        total = sum(item["count"] for item in trend_data)
        print(f"  • {keyword}: {total}回")

    # トップ企業（全期間）
    if company_trends:
        top_companies = sorted(
            company_trends.items(),
            key=lambda x: sum(item["count"] for item in x[1]),
            reverse=True
        )[:5]
        print(f"\n🏢 トップ企業（全期間）:")
        for company, trend_data in top_companies:
            total = sum(item["count"] for item in trend_data)
            print(f"  • {company}: {total}回")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
