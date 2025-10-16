"""
Phase 1: 事例検索・データ収集スクリプト（トークン最適化版）
- Phase 1: エージェントで構造化されていないテキスト形式で記事情報を抽出
- Phase 2: 別のLLMコールでシンプルにJSON整形（トークン使用量を大幅削減）
"""
import os
import sys
import time
import json
import traceback
from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent

# JSONファイルパス (分析フェーズと共有)
RESEARCH_DATA_PATH = "reports/research_data.json"

def search_and_extract_data(target_year: int = None):
    """
    週次調査データをWeb検索し、構造化されたJSONとして保存する。
    Phase 1: エージェントで非構造化テキスト抽出
    Phase 2: 別LLMコールでJSON整形（トークン削減）
    """
    print("\n" + "=" * 60)
    print("🚀 Phase 1: 事例検索とデータ抽出を開始")
    print("=" * 60)

    # --- 1. 環境変数の確認 ---
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    tavily_api_key = os.environ.get("TAVILY_API_KEY")

    if not google_api_key or not tavily_api_key:
        print("❌ エラー: GOOGLE_API_KEY/TAVILY_API_KEYが設定されていません")
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
    print("✓ ReActエージェントを設定しました")

    # --- 4. 検索対象年の設定と期間の計算 ---
    today = datetime.now()
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    year = target_year or today.year
    
    print(f"📅 検索対象年: {year}")
    print(f"🗓️ 検索開始日: {start_date} (過去1週間)")

    # --- 5. Phase 1: 非構造化テキスト抽出プロンプト ---
    search_prompt = f"""
あなたは優秀なリサーチアナリストです。Web検索と情報抽出を行い、結果を**シンプルなテキスト形式**で出力してください。

# 🎯 タスク
**過去1週間以内（{start_date}以降）に公開された**スキルマネジメント・タレントマネジメント**に関する欧米の最新記事を調査し、各記事の情報を抽出してください。

# 🔍 調査対象とキーワード
- **対象地域**: 米国、英国、ドイツ、フランス、オランダ、スウェーデン、イタリア、スペイン
- **検索キーワード**: 以下のキーワードと時間フィルタ（"past week", "last 7 days", "{year}"）を組み合わせて、**多様な検索を5回以上実行**してください。
  - "skill management", "skills management", "talent management", "competency mapping", "skills taxonomy", "workforce upskilling", "reskilling", "digital credentials", "learning experience platform", "skills-based organization", "skills-first hiring", "manufacturing workforce", "factory training"
- **必須**: 検索結果のURLに対して**web_fetch**ツールを使用し、記事本文を読んで情報を抽出してください。

# 📄 出力形式
各記事について、以下の情報を**簡潔なテキスト形式**で出力してください。目標は**10～20件**の記事です。

各記事は以下の形式で記載してください：

---
## 記事 [番号]

**タイトル**: [記事タイトル]
**URL**: [正確な記事URL]
**情報源**: [メディア名]
**公開日**: [YYYY-MM-DD形式]
**地域**: [対象地域/国]
**カテゴリー**: [feature/partnership/case_study/integration/funding/acquisition/pricing/regulation/research/dev_update のいずれか]
**関連企業**: [企業名をカンマ区切り、なければ「なし」]

**要約**:
[3～5文の日本語要約]

**重要ポイント**:
- [ポイント1]
- [ポイント2]
- [ポイント3]

**タグ**: [tag1, tag2, tag3 などカンマ区切り]
**製造業関連性**: [あり/なし]
**関連性理由**: [ある場合は1～2文で説明、なければ「該当なし」]
**信頼度**: [0.0～1.0の数値]

---

# ⚠️ 重要な調査ルール
1. **必ずweb_fetchツールを使用して記事本文を読むこと**
2. 目標件数は**10～20件**の記事を収集すること
3. 最も関連性の高い記事を優先すること（特に製造業関連）
4. 重複記事は除外すること
5. 出力は上記のシンプルなテキスト形式で、記事ごとに「---」で区切ること
"""
    
    print("🔍 スキルマネジメント・タレントマネジメントの最新動向調査を開始します...")

    # --- 6. Phase 1: エージェントの実行（テキスト抽出） ---
    MAX_RETRIES = 5
    INITIAL_DELAY = 10
    raw_text_output = None

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                delay = INITIAL_DELAY * (2 ** (attempt - 1))
                print(f"\n⚠️ Quota超過のため、{delay:.0f}秒待機してから再試行します... (試行回数: {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)

            response = agent_executor.invoke({"messages": [HumanMessage(content=search_prompt)]})
            
            messages = response.get("messages", [])
            if messages and hasattr(messages[-1], "content"):
                raw_text_output = messages[-1].content
                
                # テキスト出力の簡易検証（最低限の内容があるか）
                if len(raw_text_output) > 500 and "##" in raw_text_output:
                    print(f"✅ テキストデータを正常に取得しました。文字数: {len(raw_text_output)}")
                    break
                else:
                    print("\n⚠️ 出力が短すぎるか形式が不正です。再試行します。")
                    if attempt == MAX_RETRIES - 1:
                        raise ValueError("有効なテキスト出力が得られませんでした")
                    continue
            else:
                print("❌ エージェントからの出力取得に失敗しました。")
                if attempt == MAX_RETRIES - 1:
                    sys.exit(1)
                continue

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

    # --- 7. Phase 2: JSON整形（別LLMコール・トークン削減） ---
    print("\n" + "=" * 60)
    print("🔄 Phase 2: JSONフォーマットへの変換を開始")
    print("=" * 60)
    
    # JSON整形用の軽量LLMインスタンス（エージェント履歴なし）
    formatting_model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
    )
    
    json_formatting_prompt = f"""
以下のテキストには、複数の記事情報が含まれています。
これらの情報を、指定されたJSONスキーマに従って整形してください。

# 入力テキスト:
{raw_text_output}

# 出力JSONスキーマ:
以下の形式のJSON配列として出力してください。他のテキストや説明は一切含めず、純粋なJSON配列のみを出力してください。
```json
[
  {{
    "title": "記事タイトル",
    "url": "正確な記事のURL",
    "source": "情報源（メディア名）",
    "published_date": "YYYY-MM-DD",
    "region": "対象地域/国",
    "category": "feature/partnership/case_study/integration/funding/acquisition/pricing/regulation/research/dev_updateのいずれか",
    "related_companies": ["企業名1", "企業名2"],
    "summary_japanese": "3～5文の日本語要約",
    "key_points": ["重要ポイント1", "重要ポイント2", "重要ポイント3"],
    "tags": ["tag1", "tag2", "tag3"],
    "manufacturing_relevance": "あり" or "なし",
    "relevance_reason": "関連性がある場合の理由（1～2文）",
    "confidence_score": 0.0から1.0の間の数値
  }}
]
```

# 重要事項:
- 出力は上記JSONスキーマに厳密に従うこと
- JSON配列のみを出力し、前後に説明文やマークダウンのコードブロック記号（```）を含めないこと
- すべての記事を配列に含めること
- フィールドが不明な場合は妥当な推測値または空の値を使用すること
"""

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                delay = INITIAL_DELAY * (2 ** (attempt - 1))
                print(f"\n⚠️ Quota超過のため、{delay:.0f}秒待機してから再試行します... (試行回数: {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)

            formatting_response = formatting_model.invoke([HumanMessage(content=json_formatting_prompt)])
            json_output = formatting_response.content
            
            # マークダウンのコードブロックを削除
            json_output = json_output.strip()
            if json_output.startswith("```json"):
                json_output = json_output[7:]
            if json_output.startswith("```"):
                json_output = json_output[3:]
            if json_output.endswith("```"):
                json_output = json_output[:-3]
            json_output = json_output.strip()
            
            # JSONパースを試行
            parsed_data = json.loads(json_output)
            
            if isinstance(parsed_data, list) and parsed_data:
                print(f"✅ JSONデータを正常に変換しました。記事数: {len(parsed_data)}件")
                break
            else:
                raise ValueError("JSONの形式が期待通り（非空の配列）ではありません。")

        except json.JSONDecodeError as e:
            print(f"\n❌ JSON変換に失敗しました: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                print("生のJSON出力（デバッグ用）:")
                print(json_output[:1000])  # 最初の1000文字のみ表示
                sys.exit(1)
            continue
            
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
            if attempt == MAX_RETRIES - 1:
                sys.exit(1)
            continue

    # --- 8. JSONデータの保存 ---
    os.makedirs("reports", exist_ok=True)
    
    try:
        with open(RESEARCH_DATA_PATH, "w", encoding="utf-8") as f:
            f.write(json.dumps(parsed_data, indent=2, ensure_ascii=False))

        print("\n" + "=" * 60)
        print("✓ データ収集完了")
        print(f"💾 保存先: {RESEARCH_DATA_PATH}")
        print(f"📊 記事数: {len(parsed_data)}件")
        print("=" * 60 + "\n")
        
        return RESEARCH_DATA_PATH

    except Exception as e:
        print(f"\n❌ JSONファイルの保存中にエラーが発生しました: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    year_arg = None
    if len(sys.argv) > 1:
        try:
            year_arg = int(sys.argv[1])
        except ValueError:
            print("⚠️ 年指定が不正です。整数で指定してください。例: python research_searcher.py 2026")

    search_and_extract_data(target_year=year_arg)