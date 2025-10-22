"""
Phase 1: 事例検索・データ収集スクリプト（トークン最適化版）
- Phase 1: エージェントで構造化されていないテキスト形式で記事情報を抽出
- Phase 2: 別のLLMコールでシンプルにJSON整形（トークン使用量を大幅削減）
- レート制限対策: 適切な待機時間とバッチ処理
"""
import os
import sys
import time
import json
import traceback
import warnings
from datetime import datetime, timedelta

# Suppress LangGraph deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langgraph")

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
# Note: create_react_agent shows deprecation warning but still works in current version
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

    # --- 2. 検索対象年の設定と期間の計算 ---
    today = datetime.now()
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    year = target_year or today.year
    
    print(f"📅 検索対象年: {year}")
    print(f"🗓️ 検索開始日: {start_date} (過去1週間)")

    # --- 3. LLMとツールの準備 ---
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
    )

    search_tool = TavilySearch(
        max_results=5,  # 結果数を減らしてトークンを節約
        search_depth="advanced",  # basicに変更してトークンを節約
        include_raw_content=False,  # raw contentを無効化してトークンを節約
        time_range=f"{start_date}:{end_date}"
    )
    tools = [search_tool]
    
    # --- 4. エージェントの作成 ---
    agent_executor = create_react_agent(model, tools)
    print("✓ ReActエージェントを設定しました")

    # --- 5. Phase 1: 非構造化テキスト抽出プロンプト（簡潔版） ---
    search_prompt = f"""
あなたは優秀なリサーチアナリストです。以下のタスクを**効率的に**実行してください。

# タスク
過去1週間（{start_date}以降）のスキルマネジメント・タレントマネジメント関連の欧米記事を**3～5件**収集し、簡潔に情報を抽出してください。

# 検索方法
1. 以下のキーワードで**2～3回**だけ検索してください：
   - "skills management {year} past week"
   - "talent management workforce {year} recent"
   
2. 検索結果から**最も関連性の高い3～5記事**を選んでください

3. **web_fetchツールは使用せず**、検索結果のスニペット情報のみを使用してください（トークン節約のため）

# 出力形式
各記事を以下の**簡潔な形式**で出力してください：

---
記事 1
タイトル: [タイトル]
URL: [URL]
情報源: [メディア名]
公開日: [YYYY-MM-DD]
地域: [国/地域]
カテゴリー: [feature/case_study/partnership/etc]
関連企業: [企業名、なければ「なし」]
要約: [2～3文の日本語要約]
重要ポイント: [ポイント1] / [ポイント2] / [ポイント3]
タグ: [tag1, tag2, tag3]
製造業関連: [あり/なし]
関連性理由: [1文、なければ「該当なし」]
信頼度: [0.0～1.0]
---

# 重要
- 検索は**最小限**（2～3回）に抑えてください
- web_fetchは**使用しない**でください
- 記事数は**3～5件**で十分です
- 簡潔に情報をまとめてください
"""
    
    print("🔍 最新動向調査を開始します（トークン節約モード）...")

    # --- 6. Phase 1: エージェントの実行（テキスト抽出） ---
    MAX_RETRIES = 3  # 再試行回数を減らす
    INITIAL_DELAY = 60  # 初期待機時間を60秒に延長
    raw_text_output = None

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                # APIクォータリセット待ち（1分間隔を考慮）
                delay = max(60, INITIAL_DELAY * (2 ** (attempt - 1)))
                print(f"\n⚠️ APIクォータ超過のため、{delay:.0f}秒待機します... (試行 {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)

            print(f"📡 エージェント実行中... (試行 {attempt + 1}/{MAX_RETRIES})")
            response = agent_executor.invoke(
                {"messages": [HumanMessage(content=search_prompt)]},
                config={"recursion_limit": 15}  # 再帰制限を設定してトークンを節約
            )
            
            messages = response.get("messages", [])
            if messages and hasattr(messages[-1], "content"):
                content = messages[-1].content

                # contentがリスト形式の場合（新しいAPI形式）、テキストを抽出
                if isinstance(content, list) and len(content) > 0:
                    # リストの最初の要素からテキストを抽出
                    if isinstance(content[0], dict) and 'text' in content[0]:
                        raw_text_output = content[0]['text']
                    else:
                        raw_text_output = str(content)
                else:
                    # 従来の文字列形式
                    raw_text_output = content

                # デバッグ: 実際の出力内容を表示（最初の500文字）
                print(f"\n📊 デバッグ: 出力文字数 = {len(raw_text_output)}")
                print(f"📊 デバッグ: 出力プレビュー（最初の500文字）:\n{raw_text_output[:500]}\n")

                # テキスト出力の簡易検証
                if len(raw_text_output) > 200 and ("記事" in raw_text_output or "タイトル" in raw_text_output):
                    print(f"✅ テキストデータを取得しました。文字数: {len(raw_text_output)}")
                    break
                else:
                    print("\n⚠️ 出力が不十分です。再試行します。")
                    print(f"   - 文字数条件: {len(raw_text_output) > 200} (実際: {len(raw_text_output)}文字)")
                    print(f"   - キーワード条件: {'記事' in raw_text_output or 'タイトル' in raw_text_output}")
                    if attempt == MAX_RETRIES - 1:
                        # 最後の試行でも失敗した場合、部分的な結果でも使用
                        if raw_text_output and len(raw_text_output) > 100:
                            print("⚠️ 部分的な結果を使用します")
                            break
                        print(f"\n📊 最終的な出力内容（デバッグ）:\n{raw_text_output[:1000]}\n")
                        raise ValueError("有効なテキスト出力が得られませんでした")
                    continue
            else:
                print("❌ エージェントからの出力取得に失敗しました。")
                print(f"📊 デバッグ: messages = {messages}")
                if attempt == MAX_RETRIES - 1:
                    sys.exit(1)
                continue

        except Exception as e:
            error_message = str(e)
            if "429" in error_message or "ResourceExhausted" in error_message or "Quota exceeded" in error_message:
                if attempt == MAX_RETRIES - 1:
                    print(f"\n❌ 最大再試行回数に達しました。")
                    print("💡 対策: しばらく待ってから再実行するか、有料プランへのアップグレードを検討してください。")
                    print("📊 Gemini API無料枠: 1分あたり250,000トークン")
                    traceback.print_exc()
                    sys.exit(1)
                print(f"⏳ APIクォータ超過を検出。待機後に再試行します...")
                continue
            
            print(f"\n❌ 予期せぬエラーが発生しました: {error_message}")
            traceback.print_exc()
            if attempt == MAX_RETRIES - 1:
                sys.exit(1)
            continue

    if not raw_text_output:
        print("❌ テキスト出力の取得に失敗しました")
        sys.exit(1)

    # --- 7. Phase 2: JSON整形（別LLMコール・トークン削減） ---
    print("\n" + "=" * 60)
    print("🔄 Phase 2: JSONフォーマットへの変換を開始")
    print("=" * 60)
    
    # クォータリセット待ち
    print("⏳ APIクォータリセットのため60秒待機します...")
    time.sleep(60)
    
    # JSON整形用の軽量LLMインスタンス（エージェント履歴なし）
    formatting_model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
    )
    
    json_formatting_prompt = f"""
以下のテキストには記事情報が含まれています。これをJSON配列に整形してください。

入力テキスト:
{raw_text_output}

出力: 以下の形式のJSON配列のみを出力（説明文やコードブロック記号なし）

[
  {{
    "title": "記事タイトル",
    "url": "URL",
    "source": "情報源",
    "published_date": "YYYY-MM-DD",
    "region": "地域",
    "category": "カテゴリー",
    "related_companies": ["企業名"],
    "summary_japanese": "要約",
    "key_points": ["ポイント1", "ポイント2", "ポイント3"],
    "tags": ["tag1", "tag2"],
    "manufacturing_relevance": "あり or なし",
    "relevance_reason": "理由 or 該当なし",
    "confidence_score": 0.0～1.0の数値
  }}
]

重要: JSON配列のみを出力。前後に一切の説明やマークダウンを含めないこと。
"""

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                delay = 60
                print(f"\n⚠️ 待機中... (試行 {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)

            print(f"🔄 JSON変換中... (試行 {attempt + 1}/{MAX_RETRIES})")
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
            
            if isinstance(parsed_data, list) and len(parsed_data) > 0:
                print(f"✅ JSONデータを正常に変換しました。記事数: {len(parsed_data)}件")
                break
            else:
                raise ValueError("JSONの形式が期待通り（非空の配列）ではありません。")

        except json.JSONDecodeError as e:
            print(f"\n❌ JSON変換に失敗しました: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                print("\n生のJSON出力（デバッグ用）:")
                print(json_output[:2000] if len(json_output) > 2000 else json_output)
                sys.exit(1)
            continue
            
        except Exception as e:
            error_message = str(e)
            if "429" in error_message or "ResourceExhausted" in error_message or "Quota exceeded" in error_message:
                if attempt == MAX_RETRIES - 1:
                    print(f"\n❌ 最大再試行回数に達しました。")
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
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 60)
        print("✅ データ収集完了")
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