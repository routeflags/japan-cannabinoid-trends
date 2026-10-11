# cannabinoid-social-trends — カンナビノイド規制前後の X (Twitter) 言及データ

規制イベント（指定薬物指定）前後の X (Twitter) 上の言及量・内容を比較するための
raw 収集データセット。自然実験（pre-post 比較 + 対照系列）の設計で収集している。

- ステータス: **raw 収集のみ**（interim / processed は未作成）
- 収集元: Apify（X 検索）
- 関連分析: [`research/x/`](../../research/x/) 配下のレポート群

## 収集 Run 一覧

`data/raw/x/<run-id>/` に run 単位で格納。run-id 形式は
`YYYYMMDDTHHMMSSZ-<内容>`（AGENTS.md 準拠。ただし 2026-10-04 の初期 2 件は
この規約化以前の `YYYYMMDD-<内容>` 形式）。

| run-id | 対象 | 内容 |
|--------|------|------|
| `20261004-h4cbh-hhbd` | H4CBH / HHBD | 初期収集（h4cbh/, hhbd/ に records + run_metadata） |
| `20261005T140332Z-cbn-pre-post-regulation` | CBN（CBG 対照） | CBN 指定薬物化（2026-06-01）前後 + CBG 対照 |
| `20261005T140548Z-h4cbh-hhbd-expanded` | H4CBH / HHBD | 拡大収集 |
| `20261006T104633Z-main-compounds` | CBD / THC / CBG / CBN | 主要 4 化合物 |
| `20261008T102022Z-crdh` | CRDH | records のみ（run_metadata なし） |
| `20261008T121158Z-hhch` | HHCH | records + run_metadata |
| `20261008T121238Z-crdp` | CRDP | records + run_metadata |
| `20261008T124749Z-hhc-pre-post-regulation` | HHC（CBG 対照） | HHC 規制前後 + CBG 対照 |
| `20261008T124749Z-thch-pre-post-regulation` | THCH | THCH 規制前後 |
| `20261008T124749Z-thco-pre-post-regulation` | THC-O | THC-O 規制前後 |
| `20261008T125934Z-crdh-expanded` | CRDH | 拡大収集 |

## データ形式

- `records.json` または `<compound>_pre.json` / `<compound>_post.json` /
  `cbg_control.json` — Apify Actor の items リスト（投稿単位:
  `tweet_id`, `screen_name`, `created_at`, `text`, `favorites` 等）
- `run_metadata.json` — Apify Actor run のメタデータ
  （`id`, `status`, `usageTotalUsd`, `startedAt`, `finishedAt`）

pre/post ファイルを持つ run は「規制前」「規制後」の 2 窓で収集し、
`cbg_control.json` は**指定を受けていない CBG を対照系列**として同一方法で収集したもの
（差分の差分法の概念に基づく比較用）。

## Git ポリシー

`data/raw/` 配下はデフォルトで Git 非追跡
（リポジトリルート `.gitignore` の `**/data/raw/*` により除外）。
X 投稿の再配布権利・プライバシー評価が未完了のため、raw はローカル保持とし
公開対象から除外している（[`docs/specs/raw-data-policy.md`](../../docs/specs/raw-data-policy.md) 参照）。

## 制約・既知の制限

- 各 run は最大約 100 件のサンプルであり、母集団全体の代表ではない
- X 検索結果は非決定的。同一クエリでも再実行結果が変わりうる
- 規制前後比較は**時系列の関連**を示すものであり、因果を主張するものではない

## 関連ドキュメント

- 収集方法の詳細: [methodology.md](./methodology.md)
- 分析レポート例: [`research/x/20261006-cbn-natural-experiment.md`](../../research/x/20261006-cbn-natural-experiment.md),
  [`research/x/20261008-regulatory-comparison-batch2.md`](../../research/x/20261008-regulatory-comparison-batch2.md)
- 分析スクリプト: [`scripts/analysis/regulatory_comparison.py`](../../scripts/analysis/regulatory_comparison.py)
