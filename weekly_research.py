"""
週次スキルマネジメント・タレントマネジメント調査レポート生成スクリプト
（検索対象年をパラメータとして指定可能）
"""

import os
import sys
import time
import traceback
from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent


def generate_report(target_year: int = None):
    """週次レポートを生成する"""

    # --- 1. 環境変数の確認 ---
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    tavily_api_key = os.environ.get("TAVILY_API_KEY")

    if not google_api_key or not tavily_api_key:
        print("❌ エラー: APIキーが設定されていません")
        print(f"GOOGLE_API_KEY: {'設定済み' if google_api_key else '未設定'}")
        print(f"TAVILY_API_KEY: {'設定済み' if tavily_api_key else '未設定'}")
        sys.exit(1)

    print("✓ APIキーを確認しました")

    # --- 2. LLMとツールの準備 ---
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
    )

    search_tool = TavilySearch(
        max_results=25,  # Deep Research風に検索結果数を増加（無料プラン1000クレ/月の範囲内）
        search_depth="advanced",
        include_raw_content=True,
        time_range="week",  # 過去1週間のデータのみを取得
    )

    tools = [search_tool]

    # --- 3. エージェントの作成 ---
    agent_executor = create_react_agent(model, tools)

    # --- 4. 検索対象年の設定 ---
    today = datetime.now()
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    year = target_year or today.year  # ← デフォルトは現在の年
    print(f"📅 検索対象年: {year}")

    # --- 5. 調査プロンプトの定義 ---
    prompt = f"""
あなたは優秀なリサーチアナリストです。以下のタスクを実行してください。

# 🎯 タスク
**過去1週間以内（{start_date}以降）に公開された**スキルマネジメント・タレントマネジメント**に関する欧米の最新記事を調査し、詳細なレポートを作成してください。

**重要な検索方法**:
- 検索クエリには必ず時間フィルタを含めてください:
  - "past week"
  - "last 7 days"  
  - "{year}"
- 複数の検索を実行して、幅広い情報を収集してください
- 各記事のURLを必ずweb_fetchで取得し、詳細を確認してください

# 🔍 調査対象
**対象地域**: 米国、英国、ドイツ、フランス、オランダ、スウェーデン、イタリア、スペイン

**検索キーワード（これらを組み合わせて複数回検索してください）**:

**基本検索ワード（各3回ずつ異なる組み合わせで検索）**:
- "skill management" / "skills management" / "talent management"
- "competency management" / "competency mapping" / "skills assessment"
- "workforce development" / "workforce upskilling" / "reskilling"
- "learning and development" / "L&D trends" / "employee training"

**技術・プラットフォーム関連**:
- "skills taxonomy" / "skills ontology" / "skills graph"
- "learning experience platform" / "LXP" / "learning management system"
- "digital credentials" / "digital badges" / "micro-credentials"
- "learning record store" / "xAPI" / "learning analytics"
- "AI skills management" / "AI-powered learning" / "AI talent development"
- "skills-based organization" / "skills-first hiring" / "skills marketplace"

**製造業・産業特化**:
- "manufacturing workforce" / "factory training" / "industrial upskilling"
- "manufacturing skills gap" / "factory automation training" / "smart factory workforce"
- "manufacturing talent" / "production workforce development"

**地域・業界トレンド**:
- "HR technology trends" / "HRTech innovation" / "talent tech"
- "future of work skills" / "workforce transformation" / "skills economy"
- "employee retention" / "talent retention strategies"

**必須**: 20～25回程度の**多様な検索**を実行し、幅広く深い情報を収集してください。
（Gemini API無料プラン: 10 RPM, 250 RPD の制限を考慮した安全な設定）
- 各カテゴリから複数のキーワードを選択
- 同じキーワードでも異なる組み合わせで検索
- 検索結果が少ない場合は、別のキーワードで追加検索

# 📋 各記事から抽出すべき情報
1. **基本情報**
   - 記事タイトル
   - URL（必須・正確にコピー）
   - 情報源（メディア名）
   - 公開日（記事から取得）
   - 対象地域/国

2. **分類・カテゴリ**
   - feature / partnership / case_study / integration / funding / acquisition / pricing / regulation / research / dev_update

3. **主体情報**
   - 関連企業・組織名（複数可）

4. **詳細内容**
   - 記事要約（日本語で3～5文）
   - 技術/機能の重要ポイント（3点、箇条書き）
   - 関連技術タグ（例: badge, LRS, xAPI, skills graph, AI, LMS, HRTech等）

5. **製造業関連性**
   - 製造業との関連性: あり/なし
   - 関連がある場合の理由（1～2文）

6. **信頼性評価**
   - confidence_score: 0.0～1.0（情報源の信頼性と内容の具体性を総合評価）

# ⚠️ 重要な調査ルール
1. **必ずweb_fetchツールを使用して記事本文を読むこと**
   - 検索結果のスニペットだけで判断しない
   - 各記事の詳細内容を確認してから情報を抽出する

2. **目標件数**: 15～30件の記事を収集（Deep Research風に詳細な調査、Gemini API制限内）

3. **優先順位**:
   - 第1優先: 製造業に直接関連する記事
   - 第2優先: 隣接分野（LMS、HRテック、デジタルバッジ、workforce development等）
   - 第3優先: 一般的なスキルマネジメント関連

4. **重複除外**: 同じ内容の記事は除外

5. **URLの正確性**: 検索結果から正確にURLをコピーすること

6. **最新性の確認**: 記事の公開日を必ず確認し、本当に最新の記事かチェック

# 📄 レポート出力フォーマット
以下の構成でMarkdown形式のレポートを作成してください：

## エグゼクティブサマリー (Executive Summary)
- **今週の最重要ハイライト（Top 3 Insights）**: データから得られた最も重要な3つの洞察
- **注目トレンドとそのリスク/機会**: 特定されたトレンドと、製造業にとっての機会とリスクを明示
- **推奨される即時アクション**: 経営層が今すぐ着手すべき具体的なアクション（2-3項目）

## 調査結果詳細 (Detailed Findings)

各記事を以下のフォーマットで記載：

### [連番]. [記事タイトル]
- **URL**: [記事URL]
- **情報源**: [メディア名]
- **公開日**: YYYY-MM-DD
- **地域**: [国名]
- **カテゴリ**: [カテゴリ名]
- **関連企業**: [企業名1], [企業名2]...
- **製造業関連**: ✓ あり / - なし
- **信頼性スコア**: 0.0～1.0

**戦略的要約と意義**:
[この記事が示す戦略的な意味合いと、なぜ今重要なのかを3-5文で記載]

**重要ポイント (Key Strategic Takeaways)**:
- [ビジネスインパクトの観点からのポイント1]
- [競争優位性の観点からのポイント2]
- [実装可能性の観点からのポイント3]

**関連技術タグ**: `tag1` `tag2` `tag3`

**製造業との関連性**: [製造業のどの領域（例: 技能伝承、多能工育成、OJT、DX推進等）にどのように活用できるか具体的に記載]

---

## 戦略的トレンド分析 (Strategic Trend Analysis)

### 1. 主要なテーマと進化の方向性
- 今週のデータから浮かび上がる主要テーマ（3-5個）
- これらのテーマが今後6-12ヶ月でどう進化するかの予測
- 各テーマの成熟度（萌芽期/成長期/成熟期）

### 2. 市場の焦点と競争地図 (Competitive Landscape)
- 注目を集めている企業・組織とその戦略
- 資金調達やM&Aの動向
- 競争が激化している領域と新たな市場機会

### 3. テクノロジーの成熟度評価
各技術トレンドについて、以下を評価：
- 現在の成熟度（萌芽期/成長期/成熟期/衰退期）
- 製造業への適用可能性（高/中/低）
- 投資のタイミング（今すぐ/6ヶ月以内/12ヶ月以内/様子見）

---

## 製造業向け行動提言 (Recommended Actions for Manufacturing)

### フォーカスすべき優先課題
製造業が今週の調査結果から優先的に取り組むべき3-5つの課題と、その理由

### 次期検討ステップ
- **短期（1-3ヶ月）**: すぐに着手できる具体的なアクション
- **中期（3-6ヶ月）**: 計画・準備が必要な施策
- **長期（6-12ヶ月）**: 戦略的に検討すべき投資や変革

## 参考情報源一覧
調査に使用した全URL（箇条書き）

---

それでは調査を開始してください。**必ず20-25回の検索を実行**し、各検索結果から関連性の高い記事を選んでweb_fetchで詳細を確認してください。

**調査の進め方（Gemini API制限を考慮した最適化プラン）**:
1. まず基本検索ワードで8回程度検索し、主要トレンドを把握
2. 技術・プラットフォーム関連で8回程度検索し、具体的なソリューションを調査
3. 製造業特化で4回程度検索し、産業別の動向を確認
4. 地域・業界トレンドで3回程度検索し、広い視野で情報を収集
5. 不足している情報があれば、追加で2-3回検索して補完

合計20-25回の検索を通じて、包括的かつ深い調査レポートを作成してください。
（推定実行時間: 約5-6分、API呼び出し: 約50-60回 / 250回制限）
"""

    print(f"📊 調査対象: 過去1週間以内の最新記事 ({year}年版)")
    print("🔍 スキルマネジメント・タレントマネジメントの最新動向調査を開始します...")
    print("⚙️  API制限: Gemini 2.5 Flash (10 RPM, 250 RPD) / Tavily (1000 credits/月)")
    print("⏱️  推定実行時間: 約5-6分 (20-25回の検索実行)\n")

    # --- 6. エージェントの実行 ---
    MAX_RETRIES = 5
    INITIAL_DELAY = 10
    final_report = None

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                delay = INITIAL_DELAY * (2 ** (attempt - 1))
                print(f"\n⚠️ Quota超過のため、{delay:.0f}秒待機してから再試行します... (試行回数: {attempt}/{MAX_RETRIES})")
                time.sleep(delay)

            response = agent_executor.invoke({"messages": [HumanMessage(content=prompt)]})

            messages = response.get("messages", [])
            if messages and hasattr(messages[-1], "content"):
                final_report = messages[-1].content or "（内容なし）"
            else:
                final_report = "（レポート生成に失敗しました。レスポンス形式を確認してください。）"
            break

        except Exception as e:
            error_message = str(e)
            if "429 You exceeded your current quota" in error_message or "ResourceExhausted" in error_message:
                if attempt == MAX_RETRIES - 1:
                    print(f"\n❌ 最大再試行回数に達しました。APIの割り当てを確認してください。")
                    traceback.print_exc()
                    sys.exit(1)
                continue

            print(f"\n❌ 予期せぬエラーが発生しました: {error_message}")
            traceback.print_exc()
            sys.exit(1)

    # --- 7. レポートの保存 ---
    os.makedirs("reports", exist_ok=True)
    date_str = today.strftime("%Y%m%d")
    file_name = f"reports/週次レポート_{year}_{date_str}.md"

    try:
        with open(file_name, "w", encoding="utf-8") as f:
            # レポート内の記事数をカウント（簡易的な推定）
            article_count = final_report.count("**URL**:")

            header = (
                "# 週次レポート: スキルマネジメント・タレントマネジメント動向 "
                f"({year}年版)\n"
                "**主席コンサルタントによる分析**\n"
                f"**調査対象データ件数**: {article_count}件\n"
                f"**生成日時**: {today.strftime('%Y年%m月%d日 %H:%M:%S')}\n\n---\n\n"
            )
            f.write(header + final_report)

        print("\n" + "=" * 60)
        print("✓ レポート生成完了")
        print("=" * 60)
        print(f"📄 保存先: {file_name}")
        print("📊 調査対象: 過去1週間以内の最新記事")
        print("=" * 60 + "\n")

        return file_name

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # コマンドライン引数で年を指定できるようにする
    year_arg = None
    if len(sys.argv) > 1:
        try:
            year_arg = int(sys.argv[1])
        except ValueError:
            print("⚠️ 年指定が不正です。整数で指定してください。例: python weekly_research.py 2026")

    generate_report(target_year=year_arg)