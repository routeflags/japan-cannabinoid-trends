---
name: agent-file-trace
description: |
  エージェントが会話中に読んだファイルの履歴をデバッグトレースとして出力する。
  「何をみて判断したか」「ファイルの読み取り順序を確認して」「デバッグトレース出して」
  「どのファイルを見たか教えて」などの依頼で使う。
---

# Agent File Trace

## トリガー

- 「何をみて判断したか」
- 「ファイルの読み取り順序を確認して」
- 「デバッグトレース出して」
- 「どのファイルを見たか教えて」
- 「エージェントの思考プロセスを確認して」

## 目的

エージェントが会話中に読み取ったファイルの履歴を、時系列順にデバッグトレースとして出力する。

## 出力形式

```markdown
## ファイル読み取りトレース

| 順番 | タイミング | ファイルパス | 目的 |
|------|-----------|-------------|------|
| 1 | 初回 | `README.md` | リポジトリ構成の確認 |
| 2 | 判断時 | `products/211_mamawako/product.jsonc` | 商品状態の確認 |

## 判断根拠マッピング

| 判断 | 根拠としたファイル | 使用した値 |
|------|-------------------|-----------|
| 「draftは未登録」 | `amazon-product-model.jsonc` のコメント | `// draft -> ... -> submitted` |
| 「登録作業が必要」 | `product.jsonc` | `workflow.status: "draft"` |

## 読み取り未実行のファイル

- `amazon-listing-guide` スキル（判断後に確認）
- `operations/issues/` の問題記録
```

## 実装方法

### 方法1: 手動記録

会話中にエージェントが読んだファイルを手動で記録し、依頼があった際に出力する。

### 方法2: セッションログからの抽出

OpenCode のセッションログから `read` ツールの呼び出し履歴を抽出する。

```bash
# セッションログから read ツールの呼び出しを抽出
grep -E '"tool":"read"' .opencode/sessions/*/logs/*.jsonl | \
  jq -r '.args.filePath // .args.path' | \
  sort | uniq -c | sort -rn
```

### 方法3: Git diff からの推定

最近の変更ファイルと、その変更がどの判断に影響したかを追跡する。

```bash
# 最近の変更ファイル一覧
git log --oneline --name-only -10

# 特定ファイルの変更履歴
git log --oneline --follow -- <file-path>
```

## 出力例

```markdown
## ファイル読み取りトレース

| 順番 | タイミング | ファイルパス | 目的 |
|------|-----------|-------------|------|
| 1 | 初回 | `README.md` | リポジトリ構成の確認 |
| 2 | 判断時 | `products/211_mamawako/product.jsonc` | 商品状態の確認 |
| 3 | 判断時 | `products/212_h4cbh40_cbx10/product.jsonc` | 商品状態の確認 |
| 4 | 根拠確認 | `shared/templates/amazon-product-model.jsonc` | workflow定義の確認 |
| 5 | 根拠確認 | `operations/issues/20260410_asin_reactivation_postmortem.md` | 過去問題の確認 |

## 判断根拠マッピング

| 判断 | 根拠としたファイル | 使用した値 |
|------|-------------------|-----------|
| 「A: 商品をAmazonに登録する」 | `product.jsonc` × 2 | `workflow.status: "draft"` (両方) |
| 「draftは未登録」 | `amazon-product-model.jsonc` | L8 コメント |
| 「登録作業が必要」 | `product.jsonc` | `submission.submitted_at: null` |

## 読み取り未実行のファイル

- `amazon-listing-guide` スキル（判断後に確認→順序定義を発見）
- `operations/issues/20260408_amazon_appeal.md`（未確認）
```

## 使用上の注意

- このスキルは**記録の出力**であり、自動記録ではない
- エージェントは各判断時に「何を見て」「何を判断したか」を明示的责任を持つ
- デバッグトレースは**判断の透明性**を高め、誤判断の原因特定に使う

## 関連スキル

- `amazon-listing-guide`: 出品フローの定義
- `amazon-product-json`: 商品JSON作成フロー
