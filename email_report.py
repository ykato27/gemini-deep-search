"""
週次レポートのメール送信スクリプト
最新のMarkdownレポートを読み込み、Gemini APIで要約を生成してGmail経由で送信
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
import re

from langchain_google_genai import ChatGoogleGenerativeAI


def find_latest_report():
    """最新のレポートファイルを検索"""
    reports_dir = Path("reports")
    if not reports_dir.exists():
        print("❌ エラー: reports/ ディレクトリが存在しません")
        sys.exit(1)

    # 週次レポートファイルを検索
    report_files = list(reports_dir.glob("週次レポート_*.md"))

    if not report_files:
        print("❌ エラー: レポートファイルが見つかりません")
        sys.exit(1)

    # 最新のファイルを取得（ファイル名の日付部分でソート）
    latest_report = sorted(report_files, reverse=True)[0]
    print(f"✓ 最新レポート: {latest_report}")

    return latest_report


def extract_report_info(report_path):
    """レポートから情報を抽出"""
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    # ファイル名から日付を抽出（週次レポート_2025_20251021.md）
    filename = report_path.name
    date_match = re.search(r"(\d{8})", filename)
    report_date = date_match.group(1) if date_match else datetime.now().strftime("%Y%m%d")

    # 調査件数を抽出
    count_match = re.search(r"\*\*調査対象データ件数\*\*:\s*(\d+)件", content)
    article_count = count_match.group(1) if count_match else "不明"

    return {
        "content": content,
        "date": report_date,
        "article_count": article_count,
        "filename": filename
    }


def generate_email_summary(report_content, article_count):
    """Gemini APIでメール用の要約を生成"""
    print("📝 Gemini APIでメール用の要約を生成中...")

    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ エラー: GOOGLE_API_KEYが設定されていません")
        sys.exit(1)

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
    )

    prompt = f"""
以下の週次レポートを、メールで送信するための要約を作成してください。

# 要件
- 読了時間: 3～5分
- 構成:
  1. 今週の重要ポイント（Top 3）- 各100文字程度で簡潔に
  2. 注目トレンド - 2-3個を簡潔に
  3. 推奨される即時アクション - 2個を簡潔に
- 調査件数: {article_count}件

# 出力フォーマット
プレーンテキストで、メール本文として送信できる形式で出力してください。
見出しには適度に絵文字を使用し、読みやすくしてください。

# 元のレポート
{report_content[:8000]}

---

上記のレポートから、ビジネスパーソンが3-5分で読める簡潔な要約を作成してください。
"""

    try:
        response = model.invoke(prompt)
        summary = response.content
        print("✓ 要約生成完了")
        return summary
    except Exception as e:
        print(f"❌ 要約生成エラー: {str(e)}")
        sys.exit(1)


def generate_github_link(filename):
    """GitHubのファイルリンクを生成"""
    repo_url = "https://github.com/ykato27/gemini-deep-search"
    file_path = f"reports/{filename}"
    return f"{repo_url}/blob/main/{file_path}"


def send_email(summary, report_info, github_link):
    """Gmail経由でメールを送信"""
    print("📧 メール送信準備中...")

    # 環境変数から設定を取得
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL")

    if not all([gmail_user, gmail_password, recipient]):
        print("❌ エラー: メール送信に必要な環境変数が設定されていません")
        print(f"GMAIL_USER: {'設定済み' if gmail_user else '未設定'}")
        print(f"GMAIL_APP_PASSWORD: {'設定済み' if gmail_password else '未設定'}")
        print(f"RECIPIENT_EMAIL: {'設定済み' if recipient else '未設定'}")
        sys.exit(1)

    # 日付をフォーマット（20251021 → 2025-10-21）
    date_str = report_info["date"]
    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    # メール作成
    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg["Subject"] = f"📊 週次レポート：スキルマネジメント・タレントマネジメント動向（{formatted_date}）"

    # メール本文
    body = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 週次レポート：スキルマネジメント・タレントマネジメント
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

調査日：{formatted_date}
調査件数：{report_info['article_count']}件
読了時間：約3-5分

{summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 詳細レポート
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

より詳しい分析、戦略的トレンド分析、製造業向け行動提言は
以下のリンクからご覧ください：

{github_link}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Generated by Gemini Deep Search
   https://github.com/ykato27/gemini-deep-search
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Gmail SMTP経由で送信
    try:
        print("📤 メール送信中...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.send_message(msg)

        print("✓ メール送信完了")
        print(f"   送信先: {recipient}")
        print(f"   件名: {msg['Subject']}")

    except Exception as e:
        print(f"❌ メール送信エラー: {str(e)}")
        sys.exit(1)


def main():
    """メイン処理"""
    print("=" * 60)
    print("週次レポート メール送信スクリプト")
    print("=" * 60 + "\n")

    # 1. 最新レポートを検索
    report_path = find_latest_report()

    # 2. レポート情報を抽出
    report_info = extract_report_info(report_path)

    # 3. Gemini APIで要約を生成
    summary = generate_email_summary(
        report_info["content"],
        report_info["article_count"]
    )

    # 4. GitHubリンクを生成
    github_link = generate_github_link(report_info["filename"])

    # 5. メール送信
    send_email(summary, report_info, github_link)

    print("\n" + "=" * 60)
    print("✓ 処理完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
