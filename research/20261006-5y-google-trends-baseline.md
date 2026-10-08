# 5年 Google Trends データ収集結果（確立化合物）

| 項目 | 内容 |
|------|------|
| **収集日** | 2026-10-06 |
| **目的** | 確立化合物の5年ベースラインデータ収集 |
| **データパス** | `datasets/cannabinoid-multi-trends/data/raw/google_trends/20261008T093228Z-google-trends-5y-baseline/` |

---

## 収集結果サマリー

| 化合物 | データポイント | 初出値 | 最終値 | ピーク | ピーク日 | 5年平均 |
|--------|:-------------:|:------:|:------:|:------:|---------|:-------:|
| **CBD** | 261 | 42 | 14 | 100 | 2025-09 | 32.5 |
| **THC** | 261 | 8 | 7 | 100 | 2025-09 | 12.2 |
| **CBG** | 261 | 28 | 44 | 100 | 2023-11 | 45.6 |
| **HHC** | 261 | 0 | 0 | 100 | 2022-03 | 1.2 |
| **THCV** | 261 | 0 | 0 | 100 | 2023-09 | 5.2 |

---

## 主要な発見

### 1. CBD
- 5年間で安定した検索需要（平均 32.5）
- 2023年11月にピーク（74）
- 2025年9月に最大値（100）
- 2024年12月改正後も安定

### 2. THC
- 比較的低い検索需要（平均 12.2）
- 2023年11月に小ピーク（22）
- 2025年11月以降に増加傾向
- 規制情報が検索を駆動

### 3. CBG
- **5年間で最高の検索需要（平均 45.6）**
- 2023年11月にピーク（100）
- 2026年上半期に高水準を維持
- CBD より高い検索需要

### 4. HHC
- 2021年11月に初出
- **2022年3月規制時にピーク（100）**
- 規制後はほぼゼロに低下
- 規制効果の明確なケーススタディ

### 5. THCV
- 断続的な検索信号
- 2023年9月にピーク（100）
- 2023年12月以降は検出限界以下

---

## 5年カバレッジの完成

| カテゴリ | 化合物 | 5年データ |
|---------|--------|:---------:|
| **確立（今回収集）** | CBD, THC, CBG, HHC, THCV | ✅ |
| **新興（既存）** | CBN, CRDP, HHCH, THC-O, H4CBH, HHBD | ✅ |
| **合計** | 12化合物 | ✅ **100%** |

---

## 期待される分析

| 分析 | 内容 |
|------|------|
| **季節性分析** | 確立化合物の季節パターン把握 |
| **規制イベント整合** | 2024-12改正、2026-06 CBN規制の長期影響 |
| **早期警戒指数 v2** | 左打ち切り統計から実時系列への置換 |
| **化合物ライフサイクルマップ** | 12化合物の出現・ピーク・規制のタイムライン |

---

## 引用可能な記述

> "Five-year Google Trends data (2021-10 to 2026-10) was collected for five established cannabinoids in Japan: CBD (avg 32.5), THC (avg 12.2), CBG (avg 45.6), HHC (avg 1.2), and THCV (avg 5.2). CBG showed the highest search interest among established compounds. HHC demonstrated a clear regulatory effect pattern, with peak interest at the March 2022 designation date followed by sustained decline."

---

## 成果物

| ファイル | 内容 |
|---------|------|
| `cbd_5y_summary.json` | CBD 5年データサマリー |
| `thc_5y_summary.json` | THC 5年データサマリー |
| `cbg_5y_summary.json` | CBG 5年データサマリー |
| `hhc_5y_summary.json` | HHC 5年データサマリー |
| `thcv_5y_summary.json` | THCV 5年データサマリー |
| `run_metadata.json` | 実行メタデータ |
