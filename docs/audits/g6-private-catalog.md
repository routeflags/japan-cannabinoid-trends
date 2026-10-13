# G6 Private Data Catalog — 境界の枠（値は出さない）

**日付:** 2026-10-13
**仕様:** `docs/plans/20261013f.md` §13
**機械可読版:** [`g6-private-catalog.json`](./g6-private-catalog.json)（再生成: `python -m validation.cli audit-private-catalog`）
**厳守:** 存在と除外状態のみ。内容を開かない・列挙しない・数えない・ハッシュしない。値は一切出力しない。

---

## 1. 結果（worktree 実測）

- マーカー 9 件（`datasets/*/data/private`）: `present 0` / `absent 9`。
- 全件 `classification: restricted` / `availability: private` / `publication_status: not_approved`（Fail closed）。
- 除外規則（`.gitignore: datasets/*/data/private/`）は有効。追跡化も参照もしない。

## 2. 境界の意味

- Storage / Git Tracking / Publication は3軸独立（§4）。private マーカーの `ignored` は「Git に載せない」ことだけを意味し、研究データとしての管理（来歴・完全性）や公開可否の判断を代替しない（P1/P2）。
- Catalog 自体を公開する場合は別途公開審査が必要（§13）。本ファイルはパス名と状態のみのため審査対象外の情報を含まない。
- 機密 run の扱いは**存在記録まで**（判断待ち④）。内容分類は行わない。
