"""
テストデータ作成スクリプト

既存の research_data.json から週次データを生成してテストします。
"""

import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


def create_test_weekly_data():
    """テスト用の週次データを作成"""

    # research_data.jsonを読み込む
    research_data_path = Path("reports/research_data.json")
    if not research_data_path.exists():
        print("❌ research_data.jsonが見つかりません。")
        return

    with open(research_data_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # 週次データディレクトリの作成
    weekly_data_dir = Path("reports/weekly_data")
    weekly_data_dir.mkdir(parents=True, exist_ok=True)

    # テストデータとして、過去3週間分のデータを作成
    # （実際には同じarticlesデータを使い回すが、日付を変えて保存）
    today = datetime.now()

    for i in range(3):
        # i週間前の日付
        report_date = today - timedelta(weeks=i)
        start_date = report_date - timedelta(days=7)
        end_date = report_date

        # キーワード、企業、カテゴリの集計
        all_tags = []
        all_companies = []
        category_counts = Counter()
        manufacturing_related = 0
        confidence_scores = []

        for article in articles:
            if "tags" in article and article["tags"]:
                all_tags.extend(article["tags"])

            if "related_companies" in article and article["related_companies"]:
                all_companies.extend(article["related_companies"])

            if "category" in article and article["category"]:
                category_counts[article["category"]] += 1

            if article.get("manufacturing_relevance") == "あり":
                manufacturing_related += 1

            if "confidence_score" in article and article["confidence_score"]:
                try:
                    confidence_scores.append(float(article["confidence_score"]))
                except (ValueError, TypeError):
                    pass

        keyword_counter = Counter(all_tags)
        company_counter = Counter(all_companies)

        top_keywords = [kw for kw, count in keyword_counter.most_common(10)]
        top_companies = [company for company, count in company_counter.most_common(10)]

        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        # 週次データの構築
        weekly_data = {
            "metadata": {
                "report_date": report_date.strftime("%Y-%m-%d"),
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "article_count": len(articles),
                "execution_time": report_date.strftime("%Y-%m-%d %H:%M:%S")
            },
            "articles": articles,
            "extracted_insights": {
                "top_keywords": top_keywords,
                "top_companies": top_companies,
                "category_distribution": dict(category_counts),
                "manufacturing_related_count": manufacturing_related,
                "avg_confidence_score": round(avg_confidence, 2)
            }
        }

        # ファイル名: YYYYMMDD.json
        date_str = report_date.strftime("%Y%m%d")
        weekly_file = weekly_data_dir / f"{date_str}.json"

        with open(weekly_file, "w", encoding="utf-8") as f:
            json.dump(weekly_data, f, ensure_ascii=False, indent=2)

        print(f"✓ テストデータ作成: {weekly_file}")
        print(f"  - レポート日: {report_date.strftime('%Y-%m-%d')}")
        print(f"  - 記事数: {len(articles)}件")

    print("\n✓ テストデータの作成が完了しました。")


if __name__ == "__main__":
    create_test_weekly_data()
