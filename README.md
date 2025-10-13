# 週次スキルマネジメント・タレントマネジメント調査レポート

このリポジトリは、毎週月曜日の朝8時（JST）に自動的にスキルマネジメント・タレントマネジメント分野の最新動向を調査し、レポートを生成します。

## 📋 機能

- 過去7日間の欧米（米国、英国、ドイツ、フランス、オランダ、スウェーデン、イタリア、スペイン）の記事を自動収集
- Gemini 1.5 ProとTavily検索を使用した高精度な調査
- 製造業との関連性を重視した分析
- Markdown形式の詳細レポート生成
- GitHub Actionsによる完全自動化

## 🚀 セットアップ

### 1. リポジトリのフォーク/クローン

```bash
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
```

### 2. GitHub Secretsの設定

リポジトリの Settings → Secrets and variables → Actions から以下のSecretを追加:

- `GOOGLE_API_KEY`: Google AI Studio APIキー
  - 取得先: https://aistudio.google.com/app/apikey
  
- `TAVILY_API_KEY`: Tavily検索APIキー
  - 取得先: https://tavily.com/ (サインアップ後、ダッシュボードから取得)

### 3. GitHub Actionsの有効化

- リポジトリの **Actions** タブに移動
- ワークフローを有効化

## 📅 実行スケジュール

- **自動実行**: 毎週月曜日 08:00 JST
- **手動実行**: Actionsタブから「Run workflow」で即座に実行可能

## 📁 ファイル構成

```
.
├── .github/
│   └── workflows/
│       └── weekly_research.yml    # GitHub Actionsワークフロー
├── reports/                        # 生成されたレポート保存先
│   └── 週次レポート_YYYYMMDD.md
├── weekly_research.py              # メインスクリプト
├── requirements.txt                # Python依存パッケージ
└── README.md                       # このファイル
```

## 💻 ローカルでの実行

### 環境構築

```bash
pip install -r requirements.txt
```

### 環境変数の設定

`.env`ファイルを作成:

```env
GOOGLE_API_KEY=your_google_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 実行

```bash
python weekly_research.py
```

生成されたレポートは `reports/週次レポート_YYYYMMDD.md` に保存されます。

## 📊 レポート内容

各レポートには以下の情報が含まれます:

1. **エグゼクティブサマリー**: 今週のハイライトと注目トレンド
2. **調査結果詳細**: 各記事の詳細分析
   - 基本情報（タイトル、URL、公開日、地域）
   - カテゴリ分類
   - 要約と重要ポイント
   - 製造業との関連性
   - 信頼性スコア
3. **トレンド分析**: 主要テーマと注目企業
4. **製造業向け推奨アクション**: 実用的なインサイト
5. **参考情報源一覧**: 全URL

## 🔧 カスタマイズ

### 調査テーマの変更

`weekly_research.py` の `prompt` 変数を編集することで、調査内容をカスタマイズできます。

### 実行スケジュールの変更

`.github/workflows/weekly_research.yml` の `cron` 設定を変更:

```yaml
# 例: 毎日午前9時JST (午前0時UTC)
- cron: '0 0 * * *'
```

## 📝 注意事項

- APIの利用制限に注意してください（特にTavily検索）
- 大量の記事を収集する場合、実行時間が長くなる可能性があります
- GitHub Actionsの無料枠: 月2,000分（パブリックリポジトリは無制限）

## 🆘 トラブルシューティング

### エラー: APIキーが設定されていません
→ GitHub Secretsに正しくAPIキーが登録されているか確認

### エラー: モジュールが見つかりません
→ `requirements.txt` に必要なパッケージが全て記載されているか確認

### レポートが生成されない
→ Actionsタブでワークフローのログを確認

## 📄 ライセンス

MIT License

## 🤝 コントリビューション

Issue や Pull Request を歓迎します!