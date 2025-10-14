"""
週次スキルマネジメント・タレントマネジメント調査レポート生成スクリプト
（検索対象年をパラメータとして指定可能）
"""

import os
import sys
import time
import traceback
from datetime import datetime

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
        max_results=10,
        search_depth="advanced",
        include_raw_content=True,
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
- "skill management" + "past week"
- "skills management" + "last 7 days"
- "talent management" + "{year}"
- "competency mapping" + "recent"
- "skills taxonomy" + "past week"
- "workforce upskilling" + "last 7 days"
- "reskilling" + "{year}"
- "digital credentials" + "recent"
- "learning experience platform" + "past week"
- "manufacturing workforce" + "{year}"
- "factory training" + "recent"
- "skills-based organization" + "last 7 days"
- "skills-first hiring" + "past week"
- "learning record store" + "{year}"
- "xAPI" + "recent"
- "skills graph" + "past week"

**必須**: 5～10回程度の**多様な検索**を実行し、情報を収集してください。

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

2. **目標件数**: 10～20件の記事を収集

3. **優先順位**:
   - 第1優先: 製造業に直接関連する記事
   - 第2優先: 隣接分野（LMS、HRテック、デジタルバッジ、workforce development等）
   - 第3優先: 一般的なスキルマネジメント関連

4. **重複除外**: 同じ内容の記事は除外

5. **URLの正確性**: 検索結果から正確にURLをコピーすること

6. **最新性の確認**: 記事の公開日を必ず確認し、本当に最新の記事かチェック

# 📄 レポート出力フォーマット
以下の構成でMarkdown形式のレポートを作成してください：

## エグゼクティブサマリー
- 今週のハイライト（3～5点）
- 注目トレンド
- 製造業関連の重要トピック

## 調査結果詳細
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

**要約**:
[3～5文の日本語要約]

**重要ポイント**:
- [ポイント1]
- [ポイント2]
- [ポイント3]

**関連技術タグ**: `tag1` `tag2` `tag3`

**製造業との関連性**: [ある場合の理由を記載]

---

## トレンド分析
- 主要なテーマ（出現頻度順）
- 注目企業・組織
- 技術トレンド

## 製造業向け推奨アクション
製造業企業が注目すべきポイントと推奨される次のステップ

## 参考情報源一覧
調査に使用した全URL（箇条書き）

---

それでは調査を開始してください。**必ず15回以上のweb_search→web_fetchの組み合わせ**を実行し、詳細な情報を収集してください。
"""

    print(f"📊 調査対象: 過去1週間以内の最新記事 ({year}年版)")
    print("🔍 スキルマネジメント・タレントマネジメントの最新動向調査を開始します...\n")

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
            header = (
                "# 週次レポート: スキルマネジメント・タレントマネジメント動向\n"
                f"**調査対象**: 過去1週間以内の最新記事 ({year}年版)  \n"
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