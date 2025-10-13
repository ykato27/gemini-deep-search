"""
週次スキルマネジメント・タレントマネジメント調査レポート生成スクリプト
"""
import os
import sys
from datetime import datetime
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent


def generate_report():
    """週次レポートを生成する"""
    
    # 環境変数の確認
    google_api_key = os.environ.get('GOOGLE_API_KEY')
    tavily_api_key = os.environ.get('TAVILY_API_KEY')
    
    if not google_api_key or not tavily_api_key:
        print("❌ エラー: APIキーが設定されていません")
        print(f"GOOGLE_API_KEY: {'設定済み' if google_api_key else '未設定'}")
        print(f"TAVILY_API_KEY: {'設定済み' if tavily_api_key else '未設定'}")
        sys.exit(1)
    
    print("✓ APIキーを確認しました")
    
    # --- 1. LLMとツールの準備 ---
    model = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0
    )
    # 検索結果を増やし、深い検索を有効化
    search_tool = TavilySearch(
        max_results=10,
        search_depth="advanced",
        include_raw_content=True
    )
    tools = [search_tool]
    
    # --- 2. エージェントの作成 ---
    agent_executor = create_react_agent(model, tools)
    
    # --- 3. 調査プロンプトの定義 ---
    today = datetime.now()
    
    prompt = f"""
あなたは優秀なリサーチアナリストです。以下のタスクを実行してください。

# 🎯 タスク
**過去1週間以内に公開された**スキルマネジメント・タレントマネジメント**に関する欧米の最新記事を調査し、詳細なレポートを作成してください。

**重要な検索方法**:
- 検索クエリには必ず時間フィルタを含めてください:
  - "past week"
  - "last 7 days"  
  - "2025"
- 複数の検索を実行して、幅広い情報を収集してください
- 各記事のURLを必ずweb_fetchで取得し、詳細を確認してください

# 🔍 調査対象
**対象地域**: 米国、英国、ドイツ、フランス、オランダ、スウェーデン、イタリア、スペイン

**検索キーワード（これらを組み合わせて複数回検索してください）**: 
- "skill management" + "past week"
- "skills management" + "last 7 days"
- "talent management" + "2025"
- "competency mapping" + "recent"
- "skills taxonomy" + "past week"
- "workforce upskilling" + "last 7 days"
- "reskilling" + "2025"
- "digital credentials" + "recent"
- "learning experience platform" + "past week"
- "manufacturing workforce" + "2025"
- "factory training" + "recent"
- "skills-based organization" + "last 7 days"
- "skills-first hiring" + "past week"
- "learning record store" + "2025"
- "xAPI" + "recent"
- "skills graph" + "past week"

**必須**: 最低でも10～15回の検索を実行し、その後web_fetchで記事の詳細を取得してください。

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
    
    print(f"📊 調査対象: 過去1週間以内の最新記事")
    print("🔍 スキルマネジメント・タレントマネジメントの最新動向調査を開始します...\n")
    
    # --- 4. エージェントの実行 ---
    try:
        response = agent_executor.invoke({
            "messages": [HumanMessage(content=prompt)]
        })
        
        # 最後のメッセージからレポートを取得
        final_report = response['messages'][-1].content
        
        # --- 5. レポートの保存 ---
        # reportsディレクトリの作成
        os.makedirs('reports', exist_ok=True)
        
        # ファイル名に日付を含める（YYYYMMDD形式）
        date_str = today.strftime('%Y%m%d')
        file_name = f"reports/週次レポート_{date_str}.md"
        
        with open(file_name, "w", encoding="utf-8") as f:
            # レポートヘッダーを追加
            header = f"""# 週次レポート: スキルマネジメント・タレントマネジメント動向
**調査対象**: 過去1週間以内の最新記事  
**生成日時**: {today.strftime('%Y年%m月%d日 %H:%M:%S')}

---

"""
            f.write(header + final_report)
        
        print("\n" + "="*60)
        print("     ✓ レポート生成完了")
        print("="*60)
        print(f"📄 保存先: {file_name}")
        print(f"📊 調査対象: 過去1週間以内の最新記事")
        print("="*60 + "\n")
        
        return file_name
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    generate_report()