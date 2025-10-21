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

### ✨ 最新の改善点（2025-10-21更新）

- ✅ **日付フィルタリング**: Tavily検索に `time_range="week"` を追加し、確実に過去7日間のデータのみを取得
- ✅ **検索範囲の拡大**: 25件/検索 × 20-25回の多様な検索で包括的な情報収集
- ✅ **多様なキーワード**: 基本/技術/製造業/業界トレンドの4カテゴリで体系的に検索
- ✅ **戦略的レポート**: エグゼクティブサマリー、トレンド分析、製造業向け行動提言を含む高品質レポート
- ✅ **API制限対応**: Gemini 2.5 Flash (10 RPM, 250 RPD) の制限内で安全に動作

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
