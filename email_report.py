"""
週次レポートのメール送信スクリプト
最新のMarkdownレポートを読み込み、Gemini APIで要約を生成してGmail経由で送信
"""

import os
import sys
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

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
    """Gemini APIでメール用の要約を生成（指定フォーマット）"""
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
以下の週次レポートを、技術調査メール（他社動向の俯瞰）として要約してください。

# 重要な制約
- 「件名：」という文字列は絶対に出力しないでください
- HTMLメール形式で出力してください
- シンプルなHTMLのみ使用（装飾は最小限）

# 目的
他社動向を俯瞰し、3分で読める簡潔なレポートを作成する

# 必須の構成（この順番で必ず出力）

【冒頭リード】
今週の主要テーマを2-3行で要約してください。
「お疲れ様です。」から始めてください。

【今週の注目トレンド】
3～5個のトレンドを箇条書きで出力：
・トレンド名: 1行説明

【他社動向まとめ】
主要な企業・組織の動向を以下の形式で出力してください（3～5社）。
各社2-3行以内で簡潔に。
**重要**: 企業名の後に、必ずその情報源となった記事のリンクを付けてください。

＜企業名1＞ [<a href="記事URL">記事タイトル（短縮版）</a>]
  主な動き: 具体的な取り組み内容
  製造業への示唆: 製造業への応用可能性

例：
＜Randstad＞ [<a href="https://...">管理部門スキル2025</a>]
  主な動き: デジタルリテラシーと適応性を強調
  製造業への示唆: バックオフィスDX推進に活用可能

【要約】
全体を1-2文で総括してください。

【情報源】
調査した全記事のURLをクリック可能なリンクとして列挙してください。
形式: <a href="URL">URL</a> を箇条書き（・）で
※「他社動向まとめ」で既に使用したURLも含めて、全URLを列挙してください

# 出力形式（HTMLメール）
以下のようなシンプルなHTML形式で出力してください：

<html>
<head><meta charset="utf-8"></head>
<body style="font-family: sans-serif; line-height: 1.6; color: #333;">
<p>お疲れ様です。<br>
今週は...</p>

<p><strong>【今週の注目トレンド】</strong><br>
・トレンド名: 説明<br>
・トレンド名: 説明</p>

<p><strong>【他社動向まとめ】</strong><br>
<br>
＜企業名＞ [<a href="URL">記事タイトル</a>]<br>
&nbsp;&nbsp;主な動き: 内容<br>
&nbsp;&nbsp;製造業への示唆: 内容</p>

<p><strong>【要約】</strong><br>
要約文</p>

<p><strong>【情報源】</strong><br>
・<a href="URL1">URL1</a><br>
・<a href="URL2">URL2</a></p>
</body>
</html>

# 元のレポート
{report_content[:10000]}

---

上記の構成に従って、HTMLメールを作成してください。
「件名：」という文字列は絶対に含めないでください。
URLは必ず<a href="...">タグでハイパーリンクにしてください。
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

    # 日付をフォーマット（20251021 → 2025/10/21）
    date_str = report_info["date"]
    formatted_date = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:8]}"

    # メール作成
    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg["Subject"] = f"{formatted_date} 週次レポート｜海外スキルベース調査レポート"

    # メール本文（HTML形式）
    # summaryがすでにHTMLの<html>...</html>を含んでいる場合、bodyタグの中身だけを抽出
    body_content = summary

    # <body>...</body>の中身だけを抽出（存在する場合）
    body_match = re.search(r'<body[^>]*>(.*?)</body>', summary, re.DOTALL)
    if body_match:
        body_content = body_match.group(1)

    # 完全なHTMLメールを構築
    body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
{body_content}

<hr style="border: none; border-top: 2px solid #ddd; margin: 30px 0;">

<p><strong>【詳細レポート】</strong></p>
<p>より詳しい戦略的トレンド分析、製造業向け行動提言は以下をご覧ください：<br>
<a href="{github_link}">{github_link}</a></p>
</body>
</html>
"""

    msg.attach(MIMEText(body, "html", "utf-8"))

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
