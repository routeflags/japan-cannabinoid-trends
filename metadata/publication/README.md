# 公開審査の記録（publication review records） — 2026-10-15

`validation.cli gate-publication`（G6 §10、record-only）の**入力**を、実行のたびに
その場で作るのではなく**追跡ファイルとして残す**ための置き場。判定の出力は
`docs/audits/g6-publication-eligibility.json`（日付付きの説明は同 `.md`）。

ISS-20261015-PUB-015 の対応（メンテナ指示: ゲートを再実行して verdict を更新）で、
「判定履歴が非公開の会話に依存する」状態を解消するために導入した。

## 規則

- 1 成果物 = 1 ディレクトリ（`<artifact_id>/`）に `artifact.json` / `evidence.json` /
  `decision.json` を置く。入力がリポジトリ内にあるので、判定は登録された生成コマンドで
  再現できる（`tests/validation/test_audit_report_freshness.py` が検査する）。
- `artifact.json` の `sha256` は実ファイルから検算する。承認は内容変更で無効
  （G6-T09）: `decision.json` の `artifact_sha256` と一致しなければ PUB-10 は FAIL。
- `evidence.json` の各フラグは**日付のある根拠**を `citations` に持たねばならない。
  根拠が無い項目は記録しない（未確認 = WARNING。**推測で PASS にしない**）。
- ゲートは記録のみ。公開・Release 作成・Zenodo アップロード・DOI 発行は行わない。

## 再実行

```bash
python -m validation.cli gate-publication \
  --artifact  metadata/publication/<artifact_id>/artifact.json \
  --decision  metadata/publication/<artifact_id>/decision.json \
  --evidence  metadata/publication/<artifact_id>/evidence.json \
  --output    docs/audits/g6-publication-eligibility.json
```
