# Social Media Data Redistribution Rights Assessment

**Assessment Date:** 2026-10-01
**Purpose:** Evaluate redistribution rights for X (Twitter) and YouTube data collected via Apify

---

## 1. X (Twitter) Data

### 1.1 Data Collected

| 項目 | 内容 |
|------|------|
| データ | 147 unique tweets (text, username, engagement metrics) |
| 期間 | 2026-08-05 ~ 2026-09-08 |
| 取得方法 | Apify Actor `cPYLH3QT9GyzKhB4S` (patient_discovery/twitter-search) |
| ファイル | `datasets/cbx-social-trends/data/processed/x_cbx_202608_summary.csv` |

### 1.2 X Terms of Service (Developer Policy)

X の開発者ポリシーでは、API 経由で取得したデータの再配布に以下の制限がある：

| 制限 | 内容 | 適用 |
|------|------|------|
| **コンテンツ保存** | 保存は最大1,400件（非エンゲージメント）または最大100,000件（エンゲージメント）まで | ✅ 147件は制限内 |
| **再配布** | 公開 API データの再配布は、「コンテンツを表示するための」場合のみ許可 | ⚠️ 要評価 |
| **商用利用** | 通常は非商用用途が推奨されるが、学術・研究用途は例外 | ⚠️ 要評価 |
| **ユーザー ID** | ユーザー名・プロフィール情報の公開は制限の対象 | ⚠️ 要評価 |

### 1.3 評価結果

| 観点 | 判定 | 理由 |
|------|------|------|
| ツイート本文の再配布 | ⚠️ **制限あり** | X TOS はコンテンツの再配布を制限。研究用途でも「学術的引用」に該当するか要確認 |
| ユーザー名の公開 | ⚠️ **制限あり** | 個人情報保護の観点からも非推奨 |
| エンゲージメント統計 | ✅ **許可** | 集計済みデータ（統計値）の再配布は問題なし |
| 週別投稿数 | ✅ **許可** | 集計済みデータの再配布は問題なし |

### 1.4 推奨対応

**DOI アーカイブには以下のみを含める：**

✅ **含めるべき:**
- 週別投稿数（aggregate weekly counts）
- 投稿者別の統計（aggregate statistics）
- コンテンツ分類の集計値
- 収集方法論（methodology）
- run metadata（クエリ条件、取得日時）

**含めるべきでない:**
- ❌ ツイート本文（raw text）
- ❌ ユーザー名（usernames）
- ❌ 個別ツイート URL
- ❌ プロフィール画像

**理由:** X の Developer Policy は、コンテンツの再配布を「表示目的」に限定しており、データセットとしての再配布は想定されていない。研究用途でも、集計済みデータのみを公開し、生データは引用可能な形（URL へのリンク）で提供する方が安全。

---

## 2. YouTube Data

### 2.1 Data Collected

| 項目 | 内容 |
|------|------|
| データ | 24 unique videos (title, channel, views, timestamp) |
| 取得日 | 2026-10-01 |
| 取得方法 | Apify Actor `gJvjeCYNraSfhIaNd` (danek/youtube-search) |
| ファイル | `datasets/cbx-social-trends/data/processed/youtube_filtered_202607/` |

### 2.2 YouTube Terms of Service

YouTube の利用規約では、API 経由で取得したデータの再配布に以下の制限がある：

| 制限 | 内容 | 適用 |
|------|------|------|
| **コンテンツ再配布** | YouTube コンテンツの複製・再配布は原則禁止 | ⚠️ 要評価 |
| **メタデータ** | 動画タイトル、チャンネル名等のメタデータは引用可能 | ✅ 許可 |
| **統計データ** | 再生数等の統計値は集計済みであれば許可 | ✅ 許可 |
| **動画自体** | 動画ファイルの再配布は禁止 | ❌ 禁止 |

### 2.3 評価結果

| 観点 | 判定 | 理由 |
|------|------|------|
| 動画タイトル | ✅ **許可** | メタデータとして引用可能 |
| チャンネル名 | ✅ **許可** | メタデータとして引用可能 |
| 再生数 | ✅ **許可** | 統計値として集計済みデータは許可 |
| 動画 URL | ✅ **許可** | 公開ページへのリンクは許可 |
| 動画ファイル | ❌ **禁止** | YouTube コンテンツの複製・再配布は禁止 |

### 2.4 推奨対応

**DOI アーカイブには以下を含める：**

✅ **含めるべき:**
- 動画タイトル、チャンネル名、再生数（メタデータ）
- 動画 URL（公開ページへのリンク）
- 週別・月別の集計統計
- 収集方法論
- フィルタ基準

**含めるべきでない:**
- ❌ 動画ファイル自体
- ❌ サムネイル画像
- ❌ 字幕・チャプターデータ

---

## 3. 総合推奨

### 3.1 DOI アーカイブに含めるデータ

| データ | X | YouTube | Google Trends | COA |
|--------|---|---------|---------------|-----|
| 集計統計値 | ✅ | ✅ | ✅ | ✅ |
| メタデータ（タイトル等） | ❌ | ✅ | ✅ | ✅ |
| 生データ（本文等） | ❌ | ❌ | ✅ | ✅ |
| 収集方法論 | ✅ | ✅ | ✅ | ✅ |
| run metadata | ✅ | ✅ | ✅ | ✅ |

### 3.2 理由

1. **X:** Developer Policy はコンテンツの再配布を制限。集計済みデータのみを公開し、生データは引用可能な形で提供
2. **YouTube:** メタデータ（タイトル、統計）は引用可能だが、コンテンツ自体の再配布は禁止
3. **Google Trends:** 公開データであり、相対指数として再配布可能
4. **COA:** サプライヤー提供の分析結果。再配布権は契約内容に依存するため、要確認

### 3.3 公開前に確認すべき事項

- [ ] COA PDF の再配布権（サプライヤーとの契約内容）
- [ ] X 集計データの研究用途該当性
- [ ] YouTube メタデータの引用条件

---

## 4. 法的注意

本評価は法的助言ではない。再配布権の最終判断は、各プラットフォームの最新の利用規約と、該当する法域の法規制に基づいて行う必要がある。

**参考資料:**
- X Developer Policy: https://developer.x.com/en/developer-terms/policy
- YouTube ToS: https://www.youtube.com/t/terms
- Google Trends: https://support.google.com/trends/answer/6247921
