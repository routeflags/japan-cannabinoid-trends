# 移行計画

## 概要

このドキュメントは、古いリポジトリからのデータ移行計画を定義します。

## 現在のリポジトリ構造

```
hammerhead/
├── .serena/
├── .opencode/
├── datasets/
│   ├── cbx-x-trends/
│   │   ├── analysis/
│   │   ├── data/
│   │   └── metadata/
│   └── x-26week-trends/
│       ├── analysis/
│       ├── data/
│       └── metadata/
├── docs/
│   ├── plans/
│   ├── issues/
│   └── session-summary-20260917.md
├── .github/
│   ├── agents/
│   ├── skills/
│   ├── node_modules/
│   ├── .gitignore
│   ├── package-lock.json
│   └── package.json
├── .git/
├── metadata/
│   └── datapackage.json
├── src/
│   ├── collection/
│   └── processing/
├── LICENSE
├── CHANGELOG.md
├── project.json
├── CITATION.cff
├── methodology.md
├── README.md
├── .gitignore
├── opencode.json
└── AGENTS.md
```

## 目標構造

README.mdで説明されている理想的な構造：

```
hammerhead/
├── channels/
│   ├── youtube/
│   ├── instagram/
│   ├── facebook/
│   ├── x/
│   └── tiktok/
├── research/
│   ├── trends/
│   ├── keywords/
│   ├── competitors/
│   └── audiences/
├── data/
│   ├── youtube/
│   │   ├── raw/
│   │   └── processed/
│   ├── instagram/
│   │   ├── raw/
│   │   └── processed/
│   ├── facebook/
│   │   ├── raw/
│   │   └── processed/
│   ├── x/
│   │   ├── raw/
│   │   └── processed/
│   └── tiktok/
│       ├── raw/
│       └── processed/
├── strategy/
├── content/
│   ├── ideas/
│   ├── briefs/
│   ├── drafts/
│   └── calendar/
├── campaigns/
├── assets/
│   ├── source/
│   ├── working/
│   └── approved/
├── publishing/
│   ├── scheduled/
│   └── published/
├── experiments/
├── reports/
│   ├── weekly/
│   ├── monthly/
│   └── quarterly/
├── shared/
│   ├── schemas/
│   ├── templates/
│   └── definitions/
├── scripts/
├── archive/
├── .github/
│   └── agents/
├── README.md
├── AGENTS.md
└── .gitignore
```

## 移行ステップ

### フェーズ1：ディレクトリ構造の作成

1. **必要なディレクトリを作成**
   - channels/
   - research/
   - data/
   - strategy/
   - content/
   - campaigns/
   - assets/
   - publishing/
   - experiments/
   - reports/
   - shared/
   - scripts/
   - archive/

2. **プラットフォーム別ディレクトリを作成**
   - channels/youtube/
   - channels/instagram/
   - channels/facebook/
   - channels/x/
   - channels/tiktok/

3. **データディレクトリを作成**
   - data/youtube/raw/
   - data/youtube/processed/
   - data/instagram/raw/
   - data/instagram/processed/
   - data/facebook/raw/
   - data/facebook/processed/
   - data/x/raw/
   - data/x/processed/
   - data/tiktok/raw/
   - data/tiktok/processed/

### フェーズ2：既存データの移行

#### datasets/ の移行

1. **datasets/cbx-x-trends/** の確認
   - プラットフォーム: X (Twitter)
   - データタイプ: トレンドデータ
   - 移行先: data/x/raw/ または data/x/processed/

2. **datasets/x-26week-trends/** の確認
   - プラットフォーム: X (Twitter)
   - データタイプ: 26週間のトレンドデータ
   - 移行先: data/x/raw/ または data/x/processed/

#### metadata/ の移行

1. **metadata/datapackage.json** の確認
   - 移行先: shared/schemas/

### フェーズ3：ドキュメントの整理

1. **docs/** の整理
   - docs/plans/ → docs/plans/ に保持
   - docs/issues/ → docs/issues/ に保持
   - docs/session-summary-20260917.md → docs/ に保持

2. **README.md** の更新
   - 現在の構造に合わせて更新

### フェーズ4：スクリプトの整理

1. **src/** の整理
   - src/collection/ → scripts/collection/ に移動
   - src/processing/ → scripts/processing/ に移動

## 詳細な移行手順

### datasets/cbx-x-trends/ の移行

```bash
# 1. データの確認
ls -la datasets/cbx-x-trends/data/
ls -la datasets/cbx-x-trends/analysis/
ls -la datasets/cbx-x-trends/metadata/

# 2. プラットフォームの識別
# ファイル内容を確認してプラットフォームを特定

# 3. ファイル名の変更
# 命名規則に従ってファイル名を変更

# 4. 移動
mv datasets/cbx-x-trends/data/* data/x/raw/
mv datasets/cbx-x-trends/analysis/* data/x/processed/
mv datasets/cbx-x-trends/metadata/* shared/schemas/
```

### datasets/x-26week-trends/ の移行

```bash
# 同様の手順
mv datasets/x-26week-trends/data/* data/x/raw/
mv datasets/x-26week-trends/analysis/* data/x/processed/
mv datasets/x-26week-trends/metadata/* shared/schemas/
```

### src/ の移行

```bash
# 1. スクリプトの確認
ls -la src/collection/
ls -la src/processing/

# 2. 移動
mv src/collection/* scripts/
mv src/processing/* scripts/
```

### metadata/ の移行

```bash
# 1. メタデータの確認
cat metadata/datapackage.json

# 2. 移動
mv metadata/datapackage.json shared/schemas/
```

## 移行後の検証

### 検証項目

1. **ディレクトリ構造の確認**
   - すべてのディレクトリが存在するか
   - ファイルが正しい場所に配置されているか

2. **データの整合性**
   - ファイルが破損していないか
   - エンコーディングが正しいか

3. **ドキュメントの更新**
   - README.mdが更新されているか
   - すべてのドキュメントが正しい場所にあるか

### 検証コマンド

```bash
# ディレクトリ構造の確認
find . -type d -name "channels" -o -name "research" -o -name "data" -o -name "strategy" -o -name "content" -o -name "campaigns" -o -name "assets" -o -name "publishing" -o -name "experiments" -o -name "reports" -o -name "shared" -o -name "scripts" -o -name "archive"

# ファイル数の確認
find . -type f | wc -l

# Git ステータスの確認
git status
```

## リスクと対策

### リスク1: データの破損
- **対策**: 移行前にバックアップを作成
- **対策**: 移行後に整合性チェックを実施

### リスク2: プロキシアナンスの喪失
- **対策**: 移行前にメタデータを記録
- **対策**: 移行後にプロキシアナンス情報を更新

### リスク3: 参照の破損
- **対移**: 参照を検索して更新
- **対策**: 移行後に参照整合性を確認

### リスク4: 機密情報の漏洩
- **対策**: 移行前に機密情報を確認
- **対策**: .gitignoreを更新

## タイムライン

### フェーズ1: 準備（1日）
- [ ] 古いリポジトリのデータを確認
- [ ] 移行計画を立てる
- [ ] バックアップを作成

### フェーズ2: 移行（2-3日）
- [ ] ディレクトリ構造を作成
- [ ] データを移行
- [ ] ドキュメントを更新

### フェーズ3: 検証（1日）
- [ ] 整合性チェックを実施
- [ ] 参照を確認
- [ ] ドキュメントを最終確認

### フェーズ4: 完了（1日）
- [ ] チームに通知
- [ ] 最終確認
- [ ] 古いリポジトリをアーカイブ

## 成果物

1. **移行済みリポジトリ**: README.mdの構造に従ったリポジトリ
2. **移行ドキュメント**: 移行記録
3. **検証レポート**: 整合性チェック結果
4. **更新されたREADME.md**: 現在の構造を反映したREADME