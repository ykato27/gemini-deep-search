"""
Phase 2: 分析レポート構造化スクリプト
Phase 1で収集されたJSONデータに基づき、
構造化されたMarkdown形式のレポートを生成する。（コンサルタント視点）
"""
import os
import sys
import json
import traceback
from datetime import datetime

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# JSONファイルパス (検索フェーズと共有)
RESEARCH_DATA_PATH = "reports/research_data.json"

def generate_analysis_report(target_year: int = None):
    """収集したデータから週次レポートを生成する"""
    print("\n" + "=" * 60)
    print("🧠 Phase 2: 分析レポート構造化を開始")
    print("=" * 60)

    # --- 1. 環境変数の確認 ---
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ エラー: GOOGLE_API_KEYが設定されていません")
        sys.exit(1)
    
    # --- 2. JSONデータの読み込み ---
    if not os.path.exists(RESEARCH_DATA_PATH):
        print(f"❌ エラー: 検索データファイルが見つかりません: {RESEARCH_DATA_PATH}")
        print("Phase 1 (research_searcher.py)が正常に実行され、ファイルが作成されているか確認してください。")
        sys.exit(1)

    with open(RESEARCH_DATA_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if not raw_data:
        print("⚠️ 警告: JSONファイルにはデータが含まれていませんでした。レポートを生成できません。")
        sys.exit(0)

    # JSONデータをプロンプトに組み込むために文字列化
    data_string = json.dumps(raw_data, indent=2, ensure_ascii=False)
    
    print(f"✓ {len(raw_data)}件のデータが読み込まれました。")

    # --- 3. LLMの準備 ---
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1, # 分析には少し創造性を許容
    )
    print("✓ LLMを設定しました")

    # --- 4. レポート生成プロンプトの定義 (コンサルタント視点でブラッシュアップ済み) ---
    analysis_prompt = f"""
あなたはグローバル企業の人事戦略を担当する**主席コンサルタント**です。
提供された**JSON形式の調査データ**（一次情報抽出結果）に基づき、クライアント（製造業企業の経営層・人事部門）が**直ちに戦略意思決定に使える**、構造的かつ洞察に満ちた週次レポートをMarkdown形式で作成してください。

単なるデータ要約ではなく、**ビジネス上の意味合い**と**競争優位性**に焦点を当てた分析を行うことがあなたのミッションです。

# 📄 入力データ (JSON)
---
{data_string}
---

# 📋 レポート出力フォーマットと分析深度
上記のJSONデータに含まれる情報を徹底的に分析し、以下の構成でレポートを作成してください。

## エグゼクティブサマリー (Executive Summary)
**最も重要かつインパクトのあるセクションです。** 経営層が5分で全体像を掴めるよう、**具体的な行動（Actionable Insights）**に繋がる洞察を含めてください。

-   **今週の最重要ハイライト (Top 3 Insights)**：収集データから得られる最も戦略的に重要な**3つの洞察**（単なるニュースではなく、それが示唆するトレンドや影響）を箇条書きで提示。
-   **注目トレンドとそのリスク/機会**：トレンドが自社（製造業）にとって**短期/中期的に**どのような機会（Opportunity）とリスク（Risk）をもたらすかを簡潔に分析。
-   **推奨される即時アクション**：今週の動向に基づき、人事部門が**直ちに評価または開始すべき具体的な検討事項**（例: 特定技術のPoC開始、特定パートナーのデューデリジェンス）を1～2点提案。

## 調査結果詳細 (Detailed Findings)
入力JSONデータに含まれる各記事を、以下のMarkdownフォーマットで**忠実に、かつ簡潔に**記載してください。
ただし、信頼性スコアが0.5未満の記事タイトルは記載しないでください。

### [連番]. [記事タイトル]
-   **URL**: [記事URL]
-   **情報源**: [メディア名]
-   **公開日**: YYYY-MM-DD
-   **地域**: [国名]
-   **カテゴリ**: [カテゴリ名]
-   **関連企業**: [企業名1], [企業名2]...
-   **製造業関連**: ✓ あり / - なし
-   **信頼性スコア**: 0.0～1.0

**戦略的要約と意義**:
[記事の要約に加え、**「この動きが業界/競合に与える影響」**という観点を加味した3～5文の日本語要約]

**重要ポイント (Key Strategic Takeaways)**:
-   [ポイント1: 技術的/機能的な側面]
-   [ポイント2: 競合/市場への影響]
-   [ポイント3: 適用可能性/検討事項]

**関連技術タグ**: `tag1` `tag2` `tag3`

**製造業との関連性**: [ある場合の理由を、製造現場やサプライチェーンの文脈で記載]

---

## 戦略的トレンド分析 (Strategic Trend Analysis)
データ全体を統合し、より高度な分析を提供します。

1.  **主要なテーマと進化の方向性**: 出現頻度の高いテーマ（例: スキルギャップのAI駆動型特定）について、**その技術やアプローチが今後1年でどのように進化するか**を予測。
2.  **市場の焦点と競争地図 (Competitive Landscape)**: 注目企業や資金調達の動きから、**どの領域（例: スキルオントロジー、LXP）に資本やイノベーションが集中しているか**を特定。
3.  **テクノロジーの成熟度評価**: 主要な技術タグ（例: Skills Graph, xAPI, AI）について、それぞれ**「黎明期/成長期/成熟期」**のいずれかを評価し、その理由を簡潔に説明。

## 製造業向け行動提言 (Recommended Actions for Manufacturing)
このレポートの結論となる最も重要なセクションです。

-   **フォーカスすべき優先課題**: 製造業特有の課題（例: 技能伝承、多能工育成、OJTデジタル化）に対し、収集したトレンドがどのように役立つか、**優先順位付け**して提言。
-   **次期検討ステップ**: レポート全体を通して最も戦略的と判断した**具体的な3つのアクションアイテム**（例: AIスキルマッピングベンダーのRFI発行、デジタルバッジ導入の事業性評価）を提案。

## 参考情報源一覧 (Source Index)
調査に使用した全URLを箇条書きで一覧化してください。
"""

    # --- 5. LLMの実行 ---
    today = datetime.now()
    year = target_year or today.year
    final_report = None
    
    try:
        response = model.invoke([HumanMessage(content=analysis_prompt)])
        final_report = response.content or "（内容なし）"

    except Exception as e:
        print(f"\n❌ レポート生成中にエラーが発生しました: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

    # --- 6. レポートの保存 ---
    os.makedirs("reports", exist_ok=True)
    date_str = today.strftime("%Y%m%d")
    file_name = f"reports/週次レポート_{year}_{date_str}.md"

    try:
        with open(file_name, "w", encoding="utf-8") as f:
            header = (
                f"# 週次レポート: スキルマネジメント・タレントマネジメント動向 ({year}年版)\n"
                f"**主席コンサルタントによる分析**\n"
                f"**調査対象データ件数**: {len(raw_data)}件\n"
                f"**生成日時**: {today.strftime('%Y年%m月%d日 %H:%M:%S')}\n\n---\n\n"
            )
            f.write(header + final_report)

        print("\n" + "=" * 60)
        print("✓ レポート生成完了 (コンサルタント視点)")
        print("=" * 60)
        print(f"📄 保存先: {file_name}")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Markdownファイルの保存中にエラーが発生しました: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    year_arg = None
    if len(sys.argv) > 1:
        try:
            year_arg = int(sys.argv[1])
        except ValueError:
            print("⚠️ 年指定が不正です。整数で指定してください。例: python research_analyzer.py 2026")

    generate_analysis_report(target_year=year_arg)
