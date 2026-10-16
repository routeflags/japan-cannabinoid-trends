# Issue: research-cbd 公開審査 envelope の hash が現行 HTML と乖離（PC-7）

**ID:** ISS-20261016-MNT-001  
**優先度:** P2 (Medium)  
**ステータス:** RESOLVED (2026-10-16)  
**対象:** `publication/research_cbd.html`, `metadata/publication/research-cbd/artifact.json`, `metadata/publication/research-cbd/decision.json`, `docs/audits/publication-contract.json`

## 概要

`1cf786b` の `publication/research_cbd.html` 更新に審査 envelope の再固定が追随しておらず、
PC-7（審査対象 hash の一致）が 2 件の finding として記録されている。envelope の
`requires_review` 判定自体は変わらないため公開可否は変わらないが、審査対象のピンが古いままである。

## 確認された観測

- envelope 記録値: `sha256: c425c10d...`, `byte_length: 19702`（`metadata/publication/research-cbd/artifact.json`）。
- 現行ファイル: `sha256: 8c3718e8...`, 19879 bytes。
- `make audit-publication` は record-only で `PC-7 publication_review_hash_mismatch` 2 件
 （artifact.json / decision.json）を検出。2026-10-16 の保守で
  `docs/audits/publication-contract.json` を再生成し、`catalog_run_count: 48` と合わせて記録済み。
- `decision.json` は `status: requires_review` のままであり、PUB-10 の公開承認条件
  （approved かつ同一 sha256）は満たさない。黙って公開可能になる状態ではない。

## 影響

- CBD ページの内容審査が「どの版に対するものか」が機械的に追跡できない。
- 放置しても公開ゲートは閉じたまま（安全側）だが、乖離が常態化すると PC-7 記録が狼少年化する。

## 対応方針

- envelope の再固定は審査判断を伴うため、パイプライン保守では行わない。owner レビューで以下を選択する。
  - (a) 現行 HTML を審査対象として再ピンする: `artifact.json` の `sha256` / `byte_length` と
    `decision.json` の `artifact_sha256` を更新し、日付つき notes を残す。`status` は
    `requires_review` のまま（承認ではない）。
  - (b) HTML 側を差し戻す: `1cf786b` の当該 hunk が意図しない変更だった場合。
- いずれも `make audit-publication` の再生成で finding が消えることを確認する。

## 解決記録（2026-10-16）

Owner が案A（現行 HTML を審査対象として再ピン）を選択した。

- `metadata/publication/research-cbd/artifact.json` の `sha256` / `byte_length` を
  現行 `publication/research_cbd.html`（`sha256: 8c3718e8...`, 19879 bytes）へ更新。
- `metadata/publication/research-cbd/decision.json` の `artifact_sha256` を同一 hash へ更新。
- `status` は `requires_review` のまま維持し、`reviewed_at` / `reviewer` は null のまま。
  内容承認ではなく、審査対象の再固定である。
- `docs/audits/publication-contract.json` を再生成し、`finding_count: 0` を確認。
- `make test`: 1446 passed / 4 skipped。

## 完了条件

- [x] owner が (a) / (b) を選択し、envelope または HTML を更新した
- [x] `docs/audits/publication-contract.json` 再生成で `finding_count: 0` になる
- [x] `make test` が green のままである
