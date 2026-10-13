# G6 Git Tracking Inventory（Phase 1）— 追跡状態の棚卸し

**日付:** 2026-10-13
**仕様:** `docs/plans/20261013f.md` §15（ローカル計画書。履歴外）
**機械可読版:** [`g6-git-tracking-inventory.json`](./g6-git-tracking-inventory.json)（再生成: `python -m validation.cli audit-git-tracking`）
**非破壊:** 読取専用 git（`ls-files --error-unmatch` / `check-ignore --no-index` のみ）。raw 内容の変更なし（`raw_modified: false`）。`git add` / `git rm` / 履歴改変なし。

---

## 1. 対象と方法

- 対象: `datasets/**` の成果物ファイル（`.gitkeep` / `.gitignore` 除外、`private/` 既定除外）**134 件** + 主要非 dataset パス（`docs/audits` / `exports/taxonomy` / `docs/plans` / 既知 local-only / private マーカー）**39 件**。
- 分類は実 git 状態（P1: `.gitignore` 記載のみで判断しない。既追跡ファイルに ignore は効かない §8）:
  - `tracked`（index 登録）/ `ignored`（untracked + ignore 合致）/ `untracked_unignored`（どちらでもない。将来の誤追加リスク G6-T06）/ `absent`（既知 local-only がこの checkout に不存在。P8: 不存在をゼロと扱わない）。
- `private/` 配下は存在と除外状態のみ記録し、内容を開かない・列挙しない・数えない・ハッシュしない。
- 危険パターン画面: `.gitignore` に `*.csv` 等の一括除外が無いことを機械的に検査（`ignore_warnings`）。

## 2. 結果サマリ（worktree 実測、2026-10-13）

| state | 件数 |
|---|---|
| `tracked` | 153 |
| `ignored` | 5 |
| `absent` | 15 |
| `untracked_unignored` | 0 |

- dataset 成果物 134 件は**全件 tracked**（うち google_trends raw 99 件。`.gitignore` の `**/data/raw/*` に対する `google_trends/` 例外どおり）。
- `untracked_unignored` 0 件（`accidental_add_risk: []`）。将来の誤追加リスクは現時点で検出なし。
- `ignore_warnings` 1 件（`*.db`。下記 §4 参照のレビュー済み例外）。
- `raw_modified: false`（走査前後の sha256 一致。G6-T15）。

## 3. 内訳

- **tracked 153**: dataset 134 + `docs/audits` 13 + `exports/taxonomy` 6（いずれも追跡対象として意図どおり）。
- **ignored 5**: `docs/plans/*.md`（`/docs/plans` 規則どおり。ユーザーのローカル研究計画。追跡化しない）+ `.venv`。
- **absent 15**: `trends.db`（ルート）/ `datasets/*/data/trends.db`（2 件）/ `.staging` / `.quarantine` / `tmp` / private マーカー 9 件。いずれもこの worktree に不存在。親報告のメインチェックアウト実在データ（`trends.db`、`docs/plans` の 8 計画書等）は worktree に複製されないため、ここでは `absent` として記録する（存在の有無はメインチェックアウト側の事実を優先する）。
- **private マーカー**: 9 件全て `absent`（worktree 内に `private/` ディレクトリなし）。除外規則（`datasets/*/data/private/`）は有効。内容は未検査（§13 の枠に従う）。

## 4. 危険パターン・所見（値は出さない）

- 広範囲除外（`*.csv` 等）なし。
- 機密の追跡なし（`private/` 追跡 0、`*.key` / `.env` 追跡 0）。
- 秘密情報の混入は `validate-registries` の secret scan + 公開ゲート PUB-05 で別途検査（本監査はパス名のみ）。
- `.gitignore` の `*.db` 系 4 行（2026-10-13 追加）は、**レビュー済みの例外**として記録する: 追加時点で追跡中の `*.db` は 0 件であり、コミット済み研究データを隠すことはできない（`git ls-files` で実測）。inventory の `GITIGNORE_BLANKET_PATTERN` 警告は意図どおりに発火しており、将来のレビューで再確認する。

## 5. 追跡↔除外の変更提案（適用しない。親判断待ち）

- 新規収集 run の `datasets/*/data/raw`（非 google_trends）を引き続き除外するかは**未確定**（判断待ち①）。現状は除外中であり、本スライスは現状を追認するのみ。
- `*.db` / `*.sqlite` の除外追加は**適用済み**（2026-10-13。本監査で警告として記録し、レビュー例外として文書化）。`*.sqlite*` は実データに現れた時点で追加する。
- `docs/plans` の gitignore 解除は行わない（厳禁事項どおり）。

## 6. 再現手順

```bash
python3 -m validation.cli audit-git-tracking
python3 -m validation.cli audit-git-tracking --include-private  # private 存在時のみ（値は出ない）
```
