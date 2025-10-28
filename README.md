# 🌐 Gemini Deep Search — Weekly Research Automation

自動で**「スキルマネジメント・タレントマネジメント」に関する欧米の最新トレンド記事を収集・分析し、Deep Research風の詳細なMarkdownレポートとして出力する**ツールです。
Google Gemini（Generative AI）＋ Tavily（ウェブ検索API）＋ LangGraph（LangChainエージェント）を組み合わせた、リサーチ自動化ワークフローを構築しています。

---

## 🚀 概要

本リポジトリは、以下のタスクを自動化します。

1. **過去7日間以内**に公開された "Skill Management" / "Talent Management" 関連の海外記事を**時間フィルタ付き**で自動検索
2. **20-25回の多角的な検索**で幅広い情報を収集（基本、技術、製造業、業界トレンド）
3. **記事本文を自動抽出・要約・戦略分析**（15-30件の詳細分析）
4. **Deep Research風の高品質レポート（Markdown）を自動生成**
5. GitHub Actionsによる**毎週自動実行＆レポートの自動コミット**

### ✨ 最新の改善点（2025-10-28更新）

- ✅ **設定ファイル対応**: `config.yaml` でシステムパラメータを一元管理（ハードコーディング解消）
- ✅ **複数受信者対応**: メール送信先をカンマ区切りで複数指定可能
- ✅ **日付フィルタリング**: Tavily検索で過去N日間のデータのみを取得（設定可能）
- ✅ **検索キーワードのカスタマイズ**: `config.yaml` でキーワードを自由に追加・変更可能
- ✅ **柔軟なモデル設定**: 検索/分析/メール用にLLMモデルとtemperatureを個別設定可能
- ✅ **戦略的レポート**: エグゼクティブサマリー、トレンド分析、製造業向け行動提言を含む高品質レポート
- ✅ **API制限対応**: Gemini 2.5 Flash (10 RPM, 250 RPD) の制限内で安全に動作

---

## 📁 ディレクトリ構成

```
gemini-deep-search/
├── config.yaml                    # システム設定ファイル（★NEW）
├── weekly_research.py            # メインスクリプト（週次レポート生成）
├── email_report.py                # メール送信スクリプト
├── analyze_trends.py              # トレンド分析スクリプト
├── create_test_data.py            # テストデータ作成スクリプト
├── src/                           # ソースコード
│   ├── config_loader.py           # 設定ファイル読み込みユーティリティ（★NEW）
│   ├── research_searcher.py       # Phase1: 検索・データ収集
│   └── research_analyzer.py       # Phase2: 分析・レポート生成
├── app.py                         # Streamlitダッシュボード（メイン）
├── pages/                         # Streamlitマルチページ
│   ├── 1_🏠_Home.py              # 概要ダッシュボード
│   ├── 2_🔍_Search.py            # 記事検索
│   ├── 3_📈_Trends.py            # トレンド分析
│   └── 4_🏢_Companies.py         # 企業動向分析
├── .streamlit/                    # Streamlit設定
│   └── config.toml
├── .github/
│   └── workflows/
│       └── weekly_research_split.yml   # GitHub Actions設定（自動実行）
└── reports/
    ├── 週次レポート_2025_YYYYMMDD.md  # 自動生成されるレポート
    ├── research_data.json              # 検索データ（中間ファイル）
    ├── weekly_data/                    # 週次データ（トレンド分析用）
    │   ├── 20251022.json
    │   ├── 20251015.json
    │   └── 20251008.json
    └── trends/                         # 集計済みトレンドデータ
        ├── keywords.json               # キーワード時系列データ
        ├── companies.json              # 企業時系列データ
        ├── categories.json             # カテゴリ時系列データ
        └── summary.json                # 週次サマリー
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
pip install -r requirements.txt
```

または個別にインストール：

```bash
# レポート生成用
pip install langchain-google-genai langchain-tavily langgraph python-dotenv PyYAML

# ダッシュボード用
pip install streamlit pandas plotly
```

### 3. システム設定（config.yaml）

プロジェクトルートに `config.yaml` があります。このファイルで、以下のパラメータを一元管理できます：

**主な設定項目**:
- **LLMモデル設定**: モデル名、temperature（検索/分析/メール用に個別設定）
- **Tavily検索設定**: max_results、search_depth、include_raw_content
- **検索パラメータ**: 検索期間（days_back）、記事数、キーワード
- **エージェント設定**: リトライ回数、待機時間、再帰制限
- **データ保存先**: JSONファイルパス、レポート保存ディレクトリ
- **メール設定**: SMTPサーバー、件名テンプレート、GitHubリポジトリURL
- **レポート設定**: タイトルテンプレート、ファイル名形式

**デフォルト設定**（`config.yaml`）:
```yaml
llm:
  searcher:
    model: "gemini-2.5-flash"
    temperature: 0
  analyzer:
    model: "gemini-2.5-flash"
    temperature: 0.1
  email:
    model: "gemini-2.5-flash"
    temperature: 0.3

tavily:
  max_results: 5
  search_depth: "advanced"
  include_raw_content: false

search:
  days_back: 7
  min_articles: 3
  max_articles: 5
  keywords:
    - "skills management latest trends"
    - "talent management workforce news"

agent:
  max_retries: 3
  initial_delay: 60
  recursion_limit: 30
```

**カスタマイズ方法**:
設定を変更したい場合は、`config.yaml` を直接編集してください。例：
- 検索期間を14日間に変更: `search.days_back: 14`
- より多くの記事を収集: `tavily.max_results: 10`
- 検索キーワードを追加: `search.keywords` にキーワードを追加

### 4. APIキーを設定

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
2. 以下のシークレットを追加：

   **必須（レポート生成用）**:
   * `GOOGLE_API_KEY` - Gemini APIキー
   * `TAVILY_API_KEY` - Tavily Search APIキー

   **メール送信用（オプション）**:
   * `GMAIL_USER` - 送信元Gmailアドレス（例: your-email@gmail.com）
   * `GMAIL_APP_PASSWORD` - Googleアプリパスワード（[取得方法](#gmail-app-password%E3%81%AE%E5%8F%96%E5%BE%97%E6%96%B9%E6%B3%95)）
   * `RECIPIENT_EMAIL` - 送信先メールアドレス（複数指定可能：カンマ区切り）
     - 単一: `recipient@example.com`
     - 複数: `recipient1@example.com,recipient2@example.com,recipient3@example.com`

3. 次回スケジュール（毎週日曜）に自動実行され、
   `/reports/` に新しいMarkdownレポートが自動コミット＆メール送信されます。

---

## 📧 メール送信機能

### 概要

`email_report.py` により、生成されたレポートの要約をGmail経由で自動送信できます。

**メールの内容**:
- **件名**: 週次レポート：スキルマネジメント・タレントマネジメント動向（日付）
- **本文**: Gemini APIで生成した3-5分で読める要約
- **リンク**: 詳細レポートへのGitHubリンク

### Gmail App Passwordの取得方法

1. **Googleアカウントの2段階認証を有効化**
   - https://myaccount.google.com/security
   - 「2段階認証プロセス」を有効にする

2. **アプリパスワードを生成**
   - https://myaccount.google.com/apppasswords
   - アプリを選択: 「メール」
   - デバイスを選択: 「その他（カスタム名）」→「GitHub Actions」
   - 「生成」をクリック
   - 表示された16文字のパスワードをコピー

3. **GitHub Secretsに設定**
   - コピーしたパスワードを `GMAIL_APP_PASSWORD` として登録
   - スペースは削除してください

### 手動でメール送信

ローカルで手動実行する場合：

```bash
# 環境変数を設定
export GOOGLE_API_KEY="your_gemini_api_key"
export GMAIL_USER="your-email@gmail.com"
export GMAIL_APP_PASSWORD="your_app_password"
export RECIPIENT_EMAIL="recipient@example.com"

# 複数の送信先を設定する場合（カンマ区切り）
export RECIPIENT_EMAIL="recipient1@example.com,recipient2@example.com,recipient3@example.com"

# メール送信スクリプトを実行
python email_report.py
```

---

## 📊 トレンド分析機能（Phase 1）

### 概要

週次レポート生成時に、過去のデータを時系列で集計し、トレンド分析を可能にするデータを自動生成します。

**主な機能**:
- 週次データの構造化保存（JSON形式）
- キーワード、企業、カテゴリの時系列集計
- 過去データからのトレンド抽出
- ダッシュボード用データの準備

### データ保存

`weekly_research.py` 実行時に、以下のデータが自動保存されます：

**週次データ (`reports/weekly_data/YYYYMMDD.json`)**:
```json
{
  "metadata": {
    "report_date": "2025-10-22",
    "start_date": "2025-10-15",
    "end_date": "2025-10-22",
    "article_count": 20,
    "execution_time": "2025-10-22 14:30:00"
  },
  "articles": [...],
  "extracted_insights": {
    "top_keywords": ["AI", "スキルベース", "リーダーシップ"],
    "top_companies": ["Google", "Microsoft", "SAP"],
    "category_distribution": {"feature": 12, "research": 5},
    "manufacturing_related_count": 8,
    "avg_confidence_score": 0.85
  }
}
```

### トレンド分析の実行

過去の週次データを集計してトレンドデータを生成します：

```bash
python analyze_trends.py
```

**生成されるファイル**:

1. **`reports/trends/keywords.json`** - キーワード出現頻度の時系列データ
   ```json
   {
     "AI": [
       {"date": "2025-10-08", "count": 5},
       {"date": "2025-10-15", "count": 8},
       {"date": "2025-10-22", "count": 12}
     ]
   }
   ```

2. **`reports/trends/companies.json`** - 企業出現頻度の時系列データ

3. **`reports/trends/categories.json`** - カテゴリ分布の時系列データ

4. **`reports/trends/summary.json`** - 週次サマリーのメタデータ
   ```json
   [
     {
       "report_date": "2025-10-22",
       "article_count": 20,
       "manufacturing_related_count": 8,
       "avg_confidence_score": 0.85,
       "top_keywords": ["AI", "スキルベース"],
       "top_companies": ["Google", "Microsoft"]
     }
   ]
   ```

### テストデータの作成

開発・テスト用にサンプルデータを生成できます：

```bash
python create_test_data.py
```

これにより、過去3週間分のテストデータが `reports/weekly_data/` に作成されます。

### 活用例

- **トレンドの可視化**: 時系列グラフでキーワードや企業の出現頻度を表示
- **急上昇トレンドの検出**: 前週比での増減を自動計算
- **長期的なパターン分析**: 複数週にわたるトレンドの変化を追跡
- **ダッシュボード**: Streamlitでインタラクティブな分析ツールを提供（Phase 2で実装）

---

## 📊 ダッシュボード（Phase 2）

### 概要

Streamlitベースのインタラクティブなダッシュボードで、過去の週次レポートデータを可視化・分析できます。

**実装済み機能**:
- 🏠 **Home**: 概要ダッシュボード（KPI、記事数推移、カテゴリ分布）
- 🔍 **Search**: 記事検索・フィルタリング・詳細閲覧
- 📈 **Trends**: トレンド分析（キーワード時系列、急上昇検出、ランキング、比較）
- 🏢 **Companies**: 企業動向分析（ランキング、時系列、ヒートマップ、記事一覧）

### ダッシュボードの起動

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# ダッシュボードを起動
streamlit run app.py
```

ブラウザで http://localhost:8501 が自動的に開きます。

### 🏠 Home - 概要ダッシュボード

**主要機能**:

1. **KPIカード（4つ）**
   - 総記事数（前週比）
   - 今週の記事数
   - 製造業関連記事の割合（前週比）
   - 平均信頼度スコア（前週比）

2. **記事数推移グラフ**
   - 過去の週次レポートの記事数を時系列で表示
   - インタラクティブなプロット（Plotly）

3. **カテゴリ分布の推移**
   - 積み上げ棒グラフでカテゴリ別の記事数を表示
   - feature、research、case_study等の内訳を可視化

4. **製造業関連記事の割合推移**
   - 製造業関連記事の割合をエリアチャートで表示

5. **最新週の注目記事 TOP5**
   - 信頼度スコアでソートされた上位5件を表示
   - 展開可能なカードで詳細を確認

### 🔍 Search - 記事検索・詳細閲覧

**検索・フィルター機能**:

1. **キーワード検索**
   - タイトル、要約、重要ポイントで全文検索

2. **期間フィルター**
   - レポート日の範囲で絞り込み

3. **カテゴリフィルター**
   - feature、research、case_study等で絞り込み
   - 複数選択可能

4. **企業フィルター**
   - 関連企業で絞り込み

5. **製造業関連フィルター**
   - 製造業関連記事のみ表示

6. **信頼度スコアフィルター**
   - スライダーで最小信頼度を設定

**表示・ソート機能**:

- ソート: 信頼度スコア、公開日、レポート日（昇順・降順）
- ページネーション: 10/25/50/100件表示
- CSVエクスポート: フィルター後の記事をCSVダウンロード

**記事詳細表示**:

- 展開可能なカードで以下を表示:
  - 要約（日本語）
  - 重要ポイント
  - 製造業との関連性
  - メタ情報（情報源、公開日、地域、カテゴリ等）
  - 関連企業
  - タグ
  - 記事URLリンク

### 📈 Trends - トレンド分析（Phase 3）

**主要機能**:

1. **急上昇/急減少キーワード検出**
   - 前週比+30%以上の急上昇キーワードをTOP10表示
   - 前週比-30%以上の急減少キーワードをTOP10表示

2. **キーワード出現頻度ランキング**
   - 全期間でのTOP20キーワードを表示
   - 総出現回数でソート

3. **キーワード時系列トレンドグラフ**
   - 複数キーワードを選択して時系列比較（最大10個）
   - インタラクティブなPlotly折れ線グラフ
   - 期間フィルター（全期間/過去4週/8週/12週）
   - 最小出現回数フィルター

4. **統計情報**
   - 選択キーワードの総出現回数、平均、最大、最小、最新週

5. **キーワード比較（バーチャート）**
   - 最新週 vs 過去平均の比較
   - グループ化された棒グラフ

### 🏢 Companies - 企業動向分析（Phase 3）

**主要機能**:

1. **企業出現頻度ランキング**
   - TOP20企業をテーブル表示
   - 総出現回数、最新週、前週比、主なカテゴリ

2. **企業別トレンドグラフ**
   - 複数企業を選択して時系列比較（最大10社）
   - 出現頻度の推移を折れ線グラフで表示

3. **企業×カテゴリのヒートマップ**
   - 上位15社のカテゴリ別記事数をヒートマップ表示
   - 企業ごとの注力分野を可視化

4. **企業別の最新記事**
   - 選択企業の最新5件の記事を詳細表示
   - 要約、重要ポイント、メタ情報、記事リンク

5. **統計情報**
   - 選択企業の総出現回数、平均、最大、最新週

### デプロイ方法（Streamlit Cloud）

1. GitHubリポジトリをStreamlit Cloudに接続
2. メインファイル: `app.py`
3. Python version: 3.11
4. 自動デプロイ設定

無料で公開ダッシュボードとして利用可能です。

---

## 🧩 スクリプトの構成

### `weekly_research.py`

主要な処理の流れ：

1. **APIキー検証** (`GOOGLE_API_KEY`, `TAVILY_API_KEY`)
2. **Gemini + Tavilyのツールセット構築**
   - Gemini 2.5 Flash (temperature=0)
   - Tavily Search (max_results=25, search_depth="advanced", time_range="week")
3. **LangGraphエージェントの生成**
4. **多角的な検索プロンプトの生成**（4カテゴリ × 多様なキーワード）
5. **エージェント実行（20-25回の検索 + 詳細分析）**
   - 推定実行時間: 5-6分
   - API呼び出し: 約50-60回/250回制限
6. **Deep Research風レポートMarkdown生成・保存**（15-30件の記事分析）

### 🔍 検索キーワードカテゴリ

1. **基本検索**: skill management, talent management, competency mapping, workforce development等
2. **技術・プラットフォーム**: LXP, digital badges, AI-powered learning, skills graph等
3. **製造業特化**: manufacturing workforce, factory training, smart factory workforce等
4. **業界トレンド**: HRTech innovation, workforce transformation, employee retention等

---

## 🧾 出力されるレポート例（構造）

```markdown
# 週次レポート: スキルマネジメント・タレントマネジメント動向 (2025年版)
**主席コンサルタントによる分析**
**調査対象データ件数**: 25件
**生成日時**: 2025年10月21日 22:15:02

---

## エグゼクティブサマリー (Executive Summary)

### 今週の最重要ハイライト (Top 3 Insights)
1. **スキルギャップの深刻化**: 従業員の学習意欲と企業の育成支援のギャップが組織パフォーマンスに直接影響
2. **AI時代のリーダーシップ変革**: データ分析、AI、感情的知性を組み合わせた複合的スキルが必須に
3. **学習機会が定着の鍵**: 継続的な学習提供が人材定着の最も効果的な戦略

### 注目トレンドとそのリスク/機会
- **トレンド**: AI/デジタルスキル需要増大、リーダーシップの変革、学習のパーソナライゼーション
- **製造業の機会**: スマートファクトリー化に必要なデジタルスキル育成、熟練工定着、技能伝承加速
- **製造業のリスク**: スキルギャップ放置による生産性低下、熟練工離職、AI導入失敗

### 推奨される即時アクション
1. **全社的スキルアセスメント実施**: AI駆動型ツールでギャップ特定
2. **AI時代対応リーダーシップ開発**: マネジメント層向け緊急プログラム設計

---

## 調査結果詳細 (Detailed Findings)

### 1. 2025 State of Skills Report - SkillCycle
- **URL**: https://www.skillcycle.com/2025-workplace-skills-report/
- **情報源**: SkillCycle
- **公開日**: 2025-10-01
- **地域**: 米国
- **カテゴリ**: report
- **関連企業**: SkillCycle
- **製造業関連**: - なし
- **信頼性スコア**: 0.9

**戦略的要約と意義**:
従業員のスキル習得意欲と企業側育成支援の不足が、ストレス増加、離職率上昇、パフォーマンス低下に直結。
競合がこのギャップを埋めることで、より高い人材定着と生産性を実現する可能性。

**重要ポイント (Key Strategic Takeaways)**:
- スキルギャップが組織パフォーマンスと従業員エンゲージメントに悪影響
- リーダーシップコーチング需要高まるも、開発計画欠如がストレス要因
- 体系的な育成プログラム早急構築が必要

**関連技術タグ**: `スキルマネジメント` `従業員育成` `リーダーシップ` `職場ストレス`

**製造業との関連性**:
デジタル化・スマートファクトリー化で、技能伝承や多能工育成における体系的開発計画の欠如は大きなリスク。

---

## 戦略的トレンド分析 (Strategic Trend Analysis)

### 1. 主要なテーマと進化の方向性
- **スキルギャップの特定**: データ駆動型AI活用アセスメントが主流化
- **AIとリーダーシップ**: 技術理解+共感力を持つ「AI共生型リーダーシップ」が必須
- **学習のパーソナライゼーション**: 個人別学習パス自動生成、マイクロラーニング活用

### 2. 市場の焦点と競争地図
- **注目領域**: スキルアセスメント、AI駆動型LXP、リーダーシップ開発
- **競争激化**: スキルオントロジー/スキルグラフ基盤のタレントインテリジェンス

### 3. テクノロジーの成熟度評価
- **AI (タレントマネジメント)**: 成長期 - 導入拡大中、ベストプラクティス確立途上
- **スキルマネジメントプラットフォーム**: 成長期 - 認知拡大、全社導入に課題
- **LXP**: 成熟期 - 広く普及、AIパーソナライゼーション強化中

---

## 製造業向け行動提言 (Recommended Actions for Manufacturing)

### フォーカスすべき優先課題
1. **技能伝承と熟練工定着**: 学習機会提供で知識形式知化と若手育成加速
2. **多能工育成**: 技術スキル+ヒューマンスキルの複合育成
3. **OJTデジタル化**: AIパーソナライズド学習で効率化
4. **DX推進リーダーシップ**: AI共生型リーダー育成

### 次期検討ステップ
- **短期（1-3ヶ月）**: AI駆動型スキルアセスメントツールのRFI発行
- **中期（3-6ヶ月）**: AI共生型リーダーシップ開発プログラムPoC開始
- **長期（6-12ヶ月）**: デジタルバッジ/マイクロクレデンシャル導入事業性評価

## 参考情報源一覧
- https://www.skillcycle.com/2025-workplace-skills-report/
- https://www.shrm.org/topics-tools/research/2025-talent-trends/hr-skills
- https://learning.linkedin.com/resources/workplace-learning-report
...
```

---

## 💡 利用技術スタック

| カテゴリ   | 使用技術                         | 設定・制限                                |
| ------ | ---------------------------- | ------------------------------------ |
| LLM    | **Gemini 2.5 Flash**         | temperature=0, 10 RPM / 250 RPD（無料） |
| 検索API  | **Tavily Search API**        | max_results=25, search_depth="advanced", time_range="week"<br>1,000 credits/月（無料） |
| エージェント | **LangGraph**（LangChainベース）  | React Agent                          |
| 実行環境   | Python 3.11 / GitHub Actions | -                                    |
| 出力形式   | Markdown（自動コミット）             | 15-30件の記事分析                         |

### ⚙️ API使用量（無料プラン）

**1回の実行あたり:**
- **Gemini API**: 約50-60回呼び出し / 250回制限（24%使用）
- **Tavily API**: 約20-25クレジット / 1,000クレジット制限（2.5%使用）
- **実行時間**: 約5-6分
- **1日の実行可能回数**: 4-5回

---

## 🎯 主な機能・特徴

### 1. 高精度な日付フィルタリング
- Tavily検索に `time_range="week"` パラメータを設定し、確実に過去7日間のデータのみを取得
- 古いデータが混入する問題を解消

### 2. 包括的な情報収集
- **4カテゴリ × 多様なキーワード**で体系的に検索
  - 基本検索（8回）
  - 技術・プラットフォーム（8回）
  - 製造業特化（4回）
  - 業界トレンド（3回）
- 合計20-25回の検索で幅広くカバー

### 3. Deep Research風の高品質レポート
- **エグゼクティブサマリー**: Top 3 Insights、リスク/機会分析、即時アクション
- **戦略的トレンド分析**: テーマの進化予測、競争地図、技術成熟度評価
- **製造業向け行動提言**: 短期/中期/長期のアクションプラン
- 各記事に戦略的要約とビジネスインパクト分析を含む

### 4. API制限内での安全な動作
- Gemini 2.5 Flash無料プラン（10 RPM, 250 RPD）を考慮した設計
- Tavily無料プラン（1,000 credits/月）で月間40回以上実行可能
- リトライ機能とエラーハンドリングを実装

---

## 📊 期待される成果

このツールを使用することで：

✅ **時間削減**: 手動リサーチに比べて90%以上の時間削減  
✅ **網羅性**: 4カテゴリ × 多様なキーワードで見逃しを最小化  
✅ **品質**: 戦略的分析と実行可能なアクションプランを含む高品質レポート  
✅ **継続性**: GitHub Actionsで毎週自動実行、トレンド追跡が容易  
✅ **コスト**: 完全無料のAPIプラン内で運用可能  

---

## 🔧 トラブルシューティング

### APIレート制限エラーが発生する場合

**Gemini API (10 RPM制限)**
- 自動リトライ機能が実装されているため、通常は自動的に回復します
- 連続実行する場合は6分以上の間隔を空けてください

**Tavily API (1,000 credits/月)**
- 1回の実行で約20-25クレジット使用
- 月間40回程度まで実行可能

### 古いデータが含まれる場合

最新版では `time_range="week"` が設定されているため、過去7日間のデータのみが取得されます。  
それでも古いデータが含まれる場合は、Tavilyの検索インデックス更新タイミングの影響の可能性があります。

---

## 📝 ライセンス

MIT License

---

## 👨‍💻 作成者

[@ykato27](https://github.com/ykato27)

---
