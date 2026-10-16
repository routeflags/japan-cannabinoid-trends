# ドメイン用語集（Glossary）

**版:** 0.1.0（草案、2026-10-16）  
**正本:** 定義は `docs/specs/contracts.md` §2・§2.1・§3.1 と `docs/specs/validation-framework.md` §17 の引用。本ファイルは DDD 導入のための写しであり、定義の変更は各正本側で行う。
**選定:** owner 選定キーワード 4 件（生産・研究・加工・契約、2026-10-16）。バージョン・リリースは owner 決定（2026-10-16）で追加。U3 判断補助のため保管・目録（インベントリー）を追加。生産とリリースの間の工程として出荷を追加。基幹9件。採用ER（`docs/plan/20261016.md`）を読むための補助語29件を別表で整理する。合計38件。

| 用語 | 定義 | コンテキスト | 出典 | 曖昧さ |
|---|---|---|---|---|
| 生産 Production | パイプライン。上流の入力から契約準拠の記録（run / artifact / 加工成果物 / 生成値）を産出し、契約に含まれる検収条件・検証項目に沿って各項目を評価する側（収集・加工）。判定ルール・判定理由・可否の意味は契約／ゲート側に従い、生産側で独自に所有しない | 生産 | `contracts.md` §2、§3.1 | コード名「パイプライン」との使い分け（パイプライン＝実装名、生産＝ドメイン名、§3.1）。台帳 `owner` の値には使わない（下位名 `collection` / `processing` のまま、§3.2）。「判定しない」は「独自の判定規則を所有しない」の意味に改める |
| 出荷 Shipping | 契約の検収条件・検証項目・保管条件を満たした成果物を、指定された保管先（local / repository / remote）へ引き渡し、保管・公開・リリースへ進められる状態にする工程 | 生産と公開の間の工程（保管と隣接） | `contracts.md` §3.1、`context-map.md` §4 U3 | リリース（配布単位・配布行為）とは異なる。出荷は成果物を契約どおり保管先へ渡す工程であり、GitHub / Zenodo で配布単位を成立させるリリースそのものではない |
| 研究 Study | 研究質問・対象範囲・入力証拠・処理方法・成果物・制約を 1 つに束ねる研究単位。`study_id` で識別し `datasets/<study-id>/` に配置する。HTML ページや release ではなく dataset release の根拠になる研究集約 | 研究 | `contracts.md` §2、§2.1 | 日常語の「研究活動」一般との混同。transformation 来歴・evidence・measurement / research view を含む（§2.1） |
| 加工 Processing | 派生成果物の導出宣言と生成値。生産の下位コンテキスト（owner決定 2026-10-16、§4 U1） | 加工（生産の下位） | `contracts.md` §2.1、§3.1 | 上位の生産との包含関係は確定（独立させない）。実装は `src/processing/` |
| 保管 Storage | artifact manifest、artifact registry、storage policy、reader インターフェースを扱い、成果物の配置・読み取り・追跡可能性を支えるコンテキスト | 保管 | `contracts.md` §2.1、§3.2、`src/storage/` | 採用・公開可否の判定 owner ではない。検証は保管契約を検査してよいが、保管が検証 gate / verdict / judgment を所有するわけではない。U3 では validation との隣接関係として扱う |
| 目録 Inventory（インベントリー） | 保管対象や既存成果物を非破壊に棚卸しし、path・size・sha256・format・追跡状態などの監査用事実を列挙する記録またはその生成処理 | 保管（監査・検証が再計算して照合する） | `validation-framework.md` §17、`docs/audits/g4-storage-inventory.md`、`src/storage/inventory.py` | 目録は観測・記録であり、採用・公開・研究解釈の判定ではない。内容を正規化・修正する処理ではなく、raw を改変しない。`inventory` は「棚卸し」の意味で、商品在庫の増減管理ではない |
| 契約 Contract | 境界を越えて渡されるデータ／振る舞いについて、版を持ち機械検証可能な形で宣言した合意。検収条件・検証項目・保管条件を含む。下位にスキーマ契約・レジストリ文書・インターフェース契約・ゲート契約・判断記録を含む総称 | 検証（総称の所有）。下位種別のゲート契約の所有も契約とする（owner決定 2026-10-16、§4 U2） | `contracts.md` §2 | 総称としてのみ使う（個別文書名には使わない。例：`collection-run-v1` であって `collection-run契約` ではない）。1つの契約が複数の保管対象・保管先を束ねることがある。版・宣言場所・検査は下位種別ごとに異なる（§2表）。ゲート契約はその一種（段階遷移の可否判定。検査・行使は検証・研究が分担するが所有は契約。版は未宣言＝既知ギャップG1、§10→U4。版はバージョンと同義（次項）。配布単位のリリース（次々項）とは区別する） |
| バージョン Version | 契約の意味的同一性を識別する版表示。「版」は同義語（`contracts.md` の用語）。「バージョンを持つ」とは次の3点が揃うこと：①値が宣言場所に存在 ②台帳 `version` 列に記録 ③検査が一致を検証 | 契約（種別ごとに形が異なる。詳細は `context-map.md` §5） | 本ファイル、`context-map.md` §5（定義）。未宣言方針は `contracts.md` §10 | 文書版（本ファイル冒頭の「版: 0.1.0」等、仕様書の版付け慣行）もバージョンの一種。コード・正本の識別子（`schema_version`、`SCHEMA_VERSIONS`、`ADAPTER_CONTRACT_VERSION` 等）はこの語に対応する。複数バージョンの併存を許す（§5方針）。配布単位のリリース（次項）とは区別する |
| リリース Release | バージョン（版）の配布単位・配布行為。git tag / Zenodo による公開配布（例 v1.13.x、`docs/specs/release-process.md`） | 公開（配布工程。契約の版管理とは別の関心事） | `docs/specs/release-process.md`、git tag | バージョン（版、前項）と区別する。「契約リリース」という言い方はしない |

## 採用ER補助語（2026-10-16）

`docs/plan/20261016.md` の採用済み ER 図を読むための補助語。正本を増やす表ではなく、基幹用語・既存仕様への写しである。

| 用語 | 定義 | 関連コンテキスト | 出典 | 曖昧さ |
|---|---|---|---|---|
| 規約 Terms of Service | 第三者プラットフォーム・API・サービスが利用条件として提示する規約。契約に取り込まれる外部制約の1種 | 契約・研究 | `docs/plan/20261016.md`、AGENTS.md Social Data / First-Party Data | 契約そのものではなく、契約が参照・取り込む外部条件。規約の解釈は法的判断を伴う場合がある |
| 法令枠組み Legal Framework | 日本国内法・国際条約・管轄法など、研究・収集・公開・保管の制約になる法令体系 | 契約・研究・公開 | `docs/plan/20261016.md`、AGENTS.md Research Claims / Publication Gate | 法的助言ではない。法令上の可否は owner / 専門家判断を要する場合がある |
| 第三者制約 Third-party Constraint | 規約、API制限、再配布条件、レート制限、外部サービス固有の制約 | 契約・研究・生産 | `docs/plan/20261016.md` | 第三者の事実・条件であり、研究仮説や解釈ではない |
| 第三者 Third Party | プラットフォーム、API提供者、外部アーカイブ、データ提供者など、リポジトリ外の主体 | 契約・研究・保管 | `docs/plan/20261016.md` | 人間の研究協力者・著者とは別。ここでは外部サービス/組織を指す |
| プラットフォーム Platform | X、YouTube、Google Trends など、観測対象または収集元になる第三者サービス | 研究・生産 | `docs/plan/20261016.md`、AGENTS.md Source Separation | raw schema や adapter を単一プラットフォームに一般化しない |
| API | 第三者または内部モジュールが提供する機械的インターフェース。収集・検証・保管の呼び出し口になる | 生産・検証・保管 | `docs/plan/20261016.md` | APIがあることは利用許諾を意味しない。規約・法令・契約条件と併せて扱う |
| 管轄 Jurisdiction | 法令枠組みが適用される地域・制度単位 | 契約・研究・公開 | `docs/plan/20261016.md` | geographic scope（研究対象地域）と法的管轄は一致しない場合がある |
| 日本 Japan | 本リポジトリの主要地理スコープであり、法令枠組み上の管轄例 | 研究・契約 | `project.json` scope、`docs/plan/20261016.md` | 日本での観測対象と、日本法の適用判断は区別する |
| 国際 International | 国際条約・越境配布・外部アーカイブ等に関わる管轄例 | 契約・公開 | `docs/plan/20261016.md` | 国際的な参照は、特定国の規制適合を自動的に保証しない |
| 制約 Constraint | 研究・生産・保管・公開を制限する条件。規約・法令・プライバシー・再配布条件・技術制限を含む | 研究・契約 | `docs/plan/20261016.md` | 制約は観測事実や解釈ではなく、行為を制限する条件 |
| 研究質問 Study Question | 研究が答えようとする問い。分析を導くが、観測結果や因果主張そのものではない | 研究 | `docs/plan/20261016.md` | 研究質問は仮説や結論と区別する |
| 分析 Analysis | 観測・派生データから研究質問に答えるための計算・比較・可視化・記述 | 研究 | `docs/plan/20261016.md`、AGENTS.md Evidence Levels | 観測・派生・解釈を混同しない。分析は raw を変更しない |
| 中間成果物 Intermediate Artifact | 生産過程で生成され、最終的な成果物に至る前の一時的または中間的な artifact | 生産・加工・保管 | `docs/plan/20261016.md` | `data/interim/` と対応する場合があるが、必ず同義ではない。raw を置換しない |
| 成果物 Artifact | 生産・加工・研究・検証・公開が生成または扱う保管対象。raw payload、run metadata、processed file、audit snapshot、publication HTML 等を含む | 生産・保管・研究・検証・公開 | `docs/plan/20261016.md`、`contracts.md` §3.1 | すべての artifact が deliverable ではない。private / restricted artifact は公開対象ではない |
| 検収条件 Acceptance Condition | 契約に含まれる、成果物を次工程へ進めてよいかを評価する条件 | 契約・生産・出荷 | `docs/plan/20261016.md`、`contracts.md` §2・§3.1 | 生産は評価するが、条件の意味を独自に変更しない |
| 検証項目 Validation Item | 契約に含まれる、検証が確認すべき項目。schema、hash、manifest、registry、privacy、publication review など | 契約・検証・生産 | `docs/plan/20261016.md`、`contracts.md` §2・§3.1 | 検証項目は検証結果ではない。手動/自動の実施形態と分ける |
| 保管条件 Storage Condition | 契約に含まれる、何をどこにどう保管し、どう読める・追跡できる必要があるかを定める条件 | 契約・保管・検証 | `docs/plan/20261016.md`、`context-map.md` §4 U3 | 保管条件は契約の一部であり、契約そのものではない。1契約が複数の保管条件を持ち得る |
| 検収評価 Acceptance Evaluation | 生産が契約の検収条件・検証項目に沿って各項目を評価する行為または記録 | 生産・契約 | `docs/plan/20261016.md`、`contracts.md` §3.1 | 判定ルール・判定理由・可否の意味を生産側が独自所有することではない |
| 保管先 Storage Target | 成果物を置く具体的な場所・媒体・サービス。local / repository / remote を含む | 保管・出荷 | `docs/plan/20261016.md`、`context-map.md` §4 U3 | 保管先に存在することは公開・リリース済みを意味しない |
| ローカル保管 Local Storage | worktree、checkout、`.staging/`、local-only private directory など、ローカル環境上の保管先 | 保管・生産 | `docs/plan/20261016.md` | ローカルに存在するだけでは commit / publish / release 可能ではない |
| リポジトリ保管 Repository Storage | Git 管理下の repository 内に置かれ、レビュー・再現可能性の対象になる保管先 | 保管 | `docs/plan/20261016.md` | Git管理下でも公開適格とは限らない。private / sensitive data は commit しない |
| リモート保管 Remote Storage | GitHub、Zenodo、外部アーカイブ等、ローカル外の保管先 | 保管・公開 | `docs/plan/20261016.md` | remote に置くことは release 完了を意味しない。公開・配布には別途 gate / review が必要 |
| GitHub | リモート保管先の具体例。repository、release、release asset を含み得る | 保管・公開 | `docs/plan/20261016.md`、`docs/specs/release-process.md` | GitHub repository と GitHub release は区別する |
| Zenodo | DOI archive になり得るリモート保管先の具体例 | 保管・公開 | `docs/plan/20261016.md`、AGENTS.md Citation and DOI | DOI が実際に割り当てられるまで metadata に DOI を書かない |
| 検証 Validation | 契約・検証項目・保管条件に対して検査・監査を行い、検証結果を産出する側 | 検証 | `contracts.md` §2.1、`docs/plan/20261016.md` | 収集記録・加工成果物を産出しない。保管物を生成・変更しない |
| 検証結果 Validation Result | 検証が検証項目・保管条件を確認した結果。監査レポート、gate result、freshness check 等を含む | 検証 | `docs/plan/20261016.md` | 検証結果は成果物の source of truth ではない。結果の意味は契約／ゲートに従う |
| 手動検証 Manual Validation | 人間の確認・承認・reviewer 判断を要する検証 | 検証・公開 | `docs/plan/20261016.md`、Publication Gate | 機械検査で代替できない判断を含む。承認者・日時・根拠を記録する |
| 自動検証 Automated Validation | スキーマ検証、hash照合、freshness test、CI等、機械的に実行できる検証 | 検証 | `docs/plan/20261016.md` | 自動検証が通っても手動承認が不要になるとは限らない |
| 納品物 Deliverable | 検証を通過し、出荷・公開・リリース対象になり得る成果物 | 公開・保管・生産 | `docs/plan/20261016.md` | artifact の部分集合。raw や private artifact が常に deliverable になるわけではない |

## 備考（確立済み規則の引用）

- 生産は契約に含まれる検収条件・検証項目を評価するが、判定ルール・判定理由・可否の意味を独自所有しない。検証は検査・監査を行うが、収集記録・加工成果物を産出しない。生産の出力は記録であって解釈ではない（`contracts.md` §3.1 規則 1–3）。
