# 🌐 Gemini Deep Search — Weekly Research Automation

自動で**「スキルマネジメント・タレントマネジメント」に関する欧米の最新トレンド記事を収集・分析し、Markdownレポートとして出力する**ツールです。
Google Gemini（Generative AI）＋ Tavily（ウェブ検索API）＋ LangGraph（LangChainエージェント）を組み合わせた、リサーチ自動化ワークフローを構築しています。

---

## 🚀 概要

本リポジトリは、以下のタスクを自動化します。

1. **過去1週間以内**に公開された
   “Skill Management” / “Talent Management” 関連の海外記事を自動検索
2. **記事本文を自動抽出・要約・分析**
3. **週次レポート（Markdown）を自動生成**
4. GitHub Actionsによる**毎週自動実行＆レポートの自動コミット**

---

## 📁 ディレクトリ構成

```
gemini-deep-search/
├── weekly_research.py       # メインスクリプト（週次レポート生成）
├── .github/
│   └── workflows/
│       └── weekly_research.yml   # GitHub Actions設定（自動実行）
└── reports/
    └── 週次レポート_2025_YYYYMMDD.md  # 自動生成されるレポート
```

---

## ⚙️ セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/ykato27/gemini-deep-search.git
cd gemini-deep-search
```

### 2. 依存パッケージをインストール

```bash
pip install --upgrade pip
pip install langchain-google-genai langchain-tavily langgraph
```

### 3. APIキーを設定

環境変数に以下を設定してください。

```bash
export GOOGLE_API_KEY="your_google_gemini_api_key"
export TAVILY_API_KEY="your_tavily_api_key"
```

> ※ Tavily: [https://tavily.com](https://tavily.com)
> ※ Gemini API: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

## 🧠 実行方法

### 手動実行

```bash
python weekly_research.py
```

特定の年を指定したい場合は引数を追加：

```bash
python weekly_research.py 2024
```

実行後、以下のようにレポートが `reports/` フォルダに生成されます。

```
reports/
└── 週次レポート_2025_20251014.md
```

---

## 🤖 自動実行（GitHub Actions）

`.github/workflows/weekly_research.yml` により、
**毎週日曜23:00（日本時間・UTC 9:00）** に自動でレポート生成が行われます。

### 設定方法

1. GitHubリポジトリ → **Settings → Secrets → Actions**
2. 以下の2つを追加：

   * `GOOGLE_API_KEY`
   * `TAVILY_API_KEY`
3. 次回スケジュール（毎週日曜）に自動実行され、
   `/reports/` に新しいMarkdownレポートが自動コミットされます。

---

## 🧩 スクリプトの構成

### `weekly_research.py`

主要な処理の流れ：

1. **APIキー検証**
2. **Gemini + Tavilyのツールセット構築**
3. **LangGraphエージェント生成**
4. **自動検索プロンプトの生成**
5. **エージェント実行（15回以上の web_search + web_fetch）**
6. **レポートMarkdown生成・保存**

---

## 🧾 出力されるレポート例（構造）

```markdown
# 週次レポート: スキルマネジメント・タレントマネジメント動向
**調査対象**: 過去1週間以内の最新記事 
**生成日時**: 2025年10月14日 09:00:00

---

## エグゼクティブサマリー
- 今週の注目トピック
- 製造業でのスキル可視化事例
- LMS × AIトレンド

## 調査結果詳細

### 1. Siemens launches new skill platform
- **URL**: https://example.com
- **情報源**: HRTechNews
- **公開日**: 2025-10-10
- **地域**: ドイツ
- **カテゴリ**: feature
- **関連企業**: Siemens
- **製造業関連**: ✓ あり
- **信頼性スコア**: 0.92

**要約**:
Siemensが製造業向けスキル可視化プラットフォームを発表。AIを用いたスキル推定と資格管理を統合。

**重要ポイント**:
- スキルデータ統合の自動化
- LRSとの連携
- 製造業特化のUI/UX

**関連技術タグ**: `skills graph` `LRS` `AI`

---

## トレンド分析
- **主要テーマ**: Skills Graph, Upskilling, LXP
- **注目企業**: Siemens, Degreed, Cornerstone
- **技術トレンド**: AI × LMS、xAPI拡張

```

---

## 💡 利用技術スタック

| カテゴリ   | 使用技術                         |
| ------ | ---------------------------- |
| LLM    | **Gemini 2.5 Flash**         |
| 検索API  | **Tavily Search API**        |
| エージェント | **LangGraph**（LangChainベース）  |
| 実行環境   | Python 3.11 / GitHub Actions |
| 出力形式   | Markdown（自動コミット）             |

---

