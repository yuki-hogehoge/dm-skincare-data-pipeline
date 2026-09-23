# dm.de 製品データ収集パイプライン

dm.de(ドイツの大手ドラッグストア)の製品データ(価格・rating・成分)を自動取得し、
分析可能な形に加工するパイプライン。Serum & Kurカテゴリを対象に構築したが、
他カテゴリにも展開できるように設計している。

## クイックスタート

```bash
pip install requests pandas
```

1. `scripts/scrape_dm_full.py` を実行 → カテゴリ内の全製品データ(生データ)を取得
2. `scripts/process_features.py` を実行 → 価格の数値化・成分の正規化
3. (任意) `scripts/merge_final.py` を実行 → 手動アノテーション(concern等)を結合

各スクリプトの `INPUT_PATH` / `OUTPUT_PATH` は環境に合わせて書き換えてください。

## ドキュメント

- [`docs/data_pipeline.md`](./docs/data_pipeline.md) — API仕様・再利用手順・既知の問題と対処法(**他カテゴリに展開する際はまずここを見る**)
- [`docs/data_collection_process.md`](./docs/data_collection_process.md) — 構築過程の記録(SPA対応・API発見・レート制限対応の経緯)

## ディレクトリ構成

```
.
├── scripts/           # 収集・加工スクリプト
├── docs/               # ドキュメント
├── 01_raw_data/        # 生データ(gitignore対象、ローカルのみ)
└── 02_clean_data/       # 加工後データ(gitignore対象、ローカルのみ)
```

## データの扱いについて

`01_raw_data/` と `02_clean_data/` 配下のCSVは `.gitignore` でリポジトリから除外している。
製品説明文などの著作権・EUデータベース権に配慮し、生データそのものは公開せず、
コード(誰でも同じ手順で再取得できる)のみを公開する方針としている。

## 関連記事

- [Zenn記事(初回): 元記事タイトルをここに]
- [Zenn記事(第2弾): 成分分析編、公開後にリンクを追加]
