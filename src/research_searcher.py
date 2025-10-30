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
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

# Suppress LangGraph deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langgraph")
warnings.filterwarnings("ignore", message=".*create_react_agent.*")

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
# Note: create_react_agent shows deprecation warning but still works in current version
from langgraph.prebuilt import create_react_agent

# 設定ファイル読み込み
from config_loader import get_config


def parse_publication_date(date_str: str):
    if not date_str:
        return None

    normalized = date_str.strip()
    lowered = normalized.lower()
    if lowered in {"", "n/a", "na", "unknown"}:
        return None

    if normalized in {"不明", "未設定", "不詳", "―"}:
        return None

    if '\ufffd' in normalized:
        return None

    # Handle relative expressions such as "3 days ago" or "last week"
    relative_match = re.match(r"^(\d{1,2})\s+(day|days|hour|hours|week|weeks)\s+ago$", lowered)
    if relative_match:
        value, unit = relative_match.groups()
        amount = int(value)
        now = datetime.now()
        if unit.startswith("day"):
            return now - timedelta(days=amount)
        if unit.startswith("hour"):
            return now - timedelta(hours=amount)
        if unit.startswith("week"):
            return now - timedelta(weeks=amount)

    if lowered in {"yesterday", "昨日"}:
        return datetime.now() - timedelta(days=1)
    if lowered in {"today", "本日", "きょう", "今日"}:
        return datetime.now()

    # Handle Japanese date expressions such as "2024年5月20日"
    jp_date_match = re.match(r"^(\d{4})年(\d{1,2})月(\d{1,2})日$", normalized)
    if jp_date_match:
        year, month, day = map(int, jp_date_match.groups())
        return datetime(year, month, day)

    # Handle compact numeric formats such as 20240520
    if re.fullmatch(r"\d{8}", normalized):
        try:
            return datetime.strptime(normalized, "%Y%m%d")
        except ValueError:
            pass

    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m",
        "%Y/%m",
        "%Y.%m",
        "%Y",
    ]

    # Remove ordinal suffixes from English dates (e.g., "May 5th, 2024")
    normalized_no_suffix = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", normalized, flags=re.IGNORECASE)

    for fmt in date_formats:
        try:
            parsed = datetime.strptime(normalized_no_suffix, fmt)
            if fmt in {"%Y-%m", "%Y/%m", "%Y.%m"}:
                return parsed.replace(day=1)
            if fmt == "%Y":
                return parsed.replace(month=1, day=1)
            return parsed
        except ValueError:
            continue

    # Try ISO 8601 style formats (with or without timezone)
    iso_candidate = normalized
    if iso_candidate.endswith("Z"):
        iso_candidate = iso_candidate[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(iso_candidate)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc)
        return parsed
    except ValueError:
        pass

    # Fallback to RFC 2822 and other email style date strings
    try:
        parsed = parsedate_to_datetime(normalized_no_suffix)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc)
        return parsed
    except (TypeError, ValueError, OverflowError):
        pass

    return None



def search_and_extract_data(target_year: int = None):
    """
    週次調査データをWeb検索し、構造化されたJSONとして保存する。
    Phase 1: エージェントで非構造化テキスト抽出
    Phase 2: 別LLMコールでJSON整形（トークン削減）
    """
    print("\n" + "=" * 60)
    print("🚀 Phase 1: 事例検索とデータ抽出を開始")
    print("=" * 60)

    # --- 0. 設定ファイル読み込み ---
    config = get_config()

    # --- 1. 環境変数の確認 ---
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    tavily_api_key = os.environ.get("TAVILY_API_KEY")

    if not google_api_key or not tavily_api_key:
        print("❌ エラー: GOOGLE_API_KEY/TAVILY_API_KEYが設定されていません")
        sys.exit(1)
    print("✓ APIキーを確認しました")

    # --- 2. 検索対象年の設定と期間の計算 ---
    today = datetime.now()
    days_back = config.get("search.days_back", 7)
    start_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    year = target_year or today.year

    print(f"📅 検索対象年: {year}")
    print(f"🗓️ 検索開始日: {start_date} (過去{days_back}日間)")

    # --- 3. LLMとツールの準備 ---
    model = ChatGoogleGenerativeAI(
        model=config.get("llm.searcher.model", "gemini-2.5-flash"),
        temperature=config.get("llm.searcher.temperature", 0),
    )

    search_tool = TavilySearch(
        max_results=config.get("tavily.max_results", 5),
        search_depth=config.get("tavily.search_depth", "advanced"),
        include_raw_content=config.get("tavily.include_raw_content", False),
        start_date=start_date,
    )
    tools = [search_tool]

    # --- 4. エージェントの作成 ---
    agent_executor = create_react_agent(model, tools)
    print("✓ ReActエージェントを設定しました")

    # --- 5. Phase 1: 非構造化テキスト抽出プロンプト（簡潔版） ---
    min_articles = config.get("search.min_articles", 3)
    max_articles = config.get("search.max_articles", 5)
    keywords = config.get("search.keywords", [
        "skills management latest trends",
        "talent management workforce news"
    ])
    keywords_str = "\n   - ".join([f'"{kw}"' for kw in keywords])

    search_prompt = f"""
あなたは優秀なリサーチアナリストです。以下のタスクを**効率的に**実行してください。

# タスク
過去{days_back}日間（{start_date}以降）の**製造業向けスキルマネジメント・タレントマネジメント**関連の欧米記事を**{min_articles}～{max_articles}件**収集し、簡潔に情報を抽出してください。

# 検索方法
1. 以下のキーワードリストから、**最も効果的と思われる3～5個を選んで検索**してください：
   {keywords_str}

2. 検索の優先順位：
   - **製造業（manufacturing, industrial, plant, factory）に関連する記事を優先**
   - 具体的な企業名・プロダクト名（AG5, Kahuna, Skills Base, iMocha, Indeavor等）が含まれる記事
   - Industry 4.0、スマートマニュファクチャリング、スキルギャップ分析に関する記事
   - 実践的なケーススタディや導入事例

3. 検索結果から**最も関連性の高い{min_articles}～{max_articles}記事**を選んでください

4. **web_fetchツールは使用せず**、検索結果のスニペット情報のみを使用してください（トークン節約のため）

# 出力形式
各記事を以下の**簡潔な形式**で出力してください：

---
記事 1
タイトル: [タイトル]
URL: [URL]
情報源: [メディア名]
公開日: [YYYY-MM-DD形式で記載。不明な場合は「不明」]
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

# 重要な制約
- **公開日が{start_date}以降（過去{days_back}日以内）の記事のみを選択してください**
- 古い記事（例：「2025年の予測」を扱った数ヶ月前の記事）は除外してください
- **製造業・工場・プラント関連の記事を優先的に選択してください**
- 検索は**効率的に**（3～5個のキーワードで3～5回程度）実施してください
- web_fetchは**使用しない**でください
- 記事数は**{min_articles}～{max_articles}件**で十分です
- 簡潔に情報をまとめてください
"""

    print("🔍 最新動向調査を開始します（トークン節約モード）...")

    # --- 6. Phase 1: エージェントの実行（テキスト抽出） ---
    MAX_RETRIES = config.get("agent.max_retries", 3)
    INITIAL_DELAY = config.get("agent.initial_delay", 60)
    recursion_limit = config.get("agent.recursion_limit", 30)
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
                config={"recursion_limit": recursion_limit}
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

                # デバッグ: 実際の出力内容を表示
                preview_length = config.get("debug.preview_length", 500)
                if config.get("debug.enabled", False):
                    print(f"\n📊 デバッグ: 出力文字数 = {len(raw_text_output)}")
                    print(f"📊 デバッグ: 出力プレビュー（最初の{preview_length}文字）:\n{raw_text_output[:preview_length]}\n")

                # テキスト出力の簡易検証（最低800文字を要求し、記事情報の存在を確認）
                min_chars = 800
                has_article_markers = "記事" in raw_text_output or "タイトル" in raw_text_output
                has_enough_content = len(raw_text_output) > min_chars

                if has_enough_content and has_article_markers:
                    print(f"✅ テキストデータを取得しました。文字数: {len(raw_text_output)}")
                    break
                else:
                    print("\n⚠️ 出力が不十分です。再試行します。")
                    print(f"   - 文字数条件: {has_enough_content} (実際: {len(raw_text_output)}文字、最低: {min_chars}文字)")
                    print(f"   - キーワード条件: {has_article_markers}")
                    if attempt == MAX_RETRIES - 1:
                        # 最後の試行でも失敗した場合、部分的な結果でも使用
                        if raw_text_output and len(raw_text_output) > 200:
                            print("⚠️ 部分的な結果を使用します")
                            print(f"\n📊 取得したテキスト（最初の500文字）:\n{raw_text_output[:500]}\n")
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

            # デバッグ情報の出力
            if config.get("debug.enabled", False) or attempt > 0:
                print(f"\n📊 デバッグ: JSON型 = {type(parsed_data)}")
                if isinstance(parsed_data, list):
                    print(f"📊 デバッグ: 配列の長さ = {len(parsed_data)}")
                print(f"📊 デバッグ: JSON出力（最初の500文字）:\n{json_output[:500]}\n")

            if isinstance(parsed_data, list) and len(parsed_data) > 0:
                # 日付フィルタリング: start_date以降の記事のみを保持
                start_date_limit = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date_limit = datetime.strptime(end_date, "%Y-%m-%d").date()

                original_count = len(parsed_data)
                filtered_data = []
                for article in parsed_data:
                    pub_date_str = article.get("published_date")

                    # Filter articles to the requested 7-day window
                    parsed_datetime = parse_publication_date(pub_date_str)

                    if not parsed_datetime:
                        print(
                            f"[WARN] Skipping article with unparsed date: {article.get('title', 'Unknown title')}"
                            f" (published_date={pub_date_str})"
                        )
                        continue

                    published_date = parsed_datetime.date()

                    if published_date < start_date_limit or published_date > end_date_limit:
                        print(f"[WARN] Skipping article outside window: {article.get('title', 'Unknown title')} (published_date={pub_date_str})")
                        continue

                    filtered_data.append(article)
                parsed_data = filtered_data

                if len(parsed_data) > 0:
                    print(f"✅ JSONデータを正常に変換しました。記事数: {len(parsed_data)}件（フィルタリング後）")
                    if original_count != len(parsed_data):
                        print(f"📊 フィルタリング前の記事数: {original_count}件")
                    break
                else:
                    print("⚠️ フィルタリング後の記事が0件です。再試行します。")
                    print(f"📊 フィルタリング前の記事数: {original_count}件")
                    print(f"📊 検索期間: {start_date} ～ {end_date}")
                    if attempt == MAX_RETRIES - 1:
                        print(f"\n📊 入力テキスト（最初の500文字）:\n{raw_text_output[:500]}\n")
                        raise ValueError("有効な記事が見つかりませんでした（フィルタリング後0件）。検索期間内の記事がありませんでした。")
                    continue
            else:
                # JSONが配列でない、または空配列の場合
                error_msg = f"JSONの形式が期待通りではありません。型: {type(parsed_data)}"
                if isinstance(parsed_data, list):
                    error_msg = "JSONは配列ですが、空です（長さ0）。"
                print(f"⚠️ {error_msg}")
                print(f"📊 JSON出力（最初の1000文字）:\n{json_output[:1000]}\n")
                print(f"📊 入力テキスト（最初の500文字）:\n{raw_text_output[:500]}\n")

                if attempt == MAX_RETRIES - 1:
                    raise ValueError(f"{error_msg} 入力テキストが不十分か、JSON変換に失敗しました。")
                continue

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
    research_data_path = config.get("data.research_data_path", "reports/research_data.json")
    reports_dir = os.path.dirname(research_data_path) or "reports"
    os.makedirs(reports_dir, exist_ok=True)

    try:
        with open(research_data_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 60)
        print("✅ データ収集完了")
        print(f"💾 保存先: {research_data_path}")
        print(f"📊 記事数: {len(parsed_data)}件")
        print("=" * 60 + "\n")

        return research_data_path

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
