# dm.de Product Data Collection Pipeline

A pipeline for automatically collecting and processing product data (price, rating, ingredients)
from dm.de, a major German drugstore chain. Built for the Serum & Kur (serum/treatment) category,
but designed to be reusable for other categories as well.

If you'd prefer to read about this project in Japanese, see the accompanying Zenn article:
[dm.deの製品データ収集パイプラインを作った話](https://zenn.dev/yuki_hogehoge/articles/dm_data_pipeline)

## Disclaimer

This is a personal, educational project built to practice web scraping, API reverse
engineering, and data pipeline design. It is not affiliated with, endorsed by, or
officially supported by dm-drogerie markt.

The pipeline relies on dm.de's internal (undocumented) APIs, discovered through browser
DevTools inspection. These endpoints may change or be restricted at any time without notice,
which could break this pipeline. Use at your own risk, and always re-verify robots.txt and
rate limits before running against the live site.

## Quick Start

```bash
pip install requests pandas
```

1. Run `scripts/scrape_dm_full.py` → fetches raw data for all products in the target category
2. Run `scripts/process_features.py` → converts price to numeric, normalizes ingredient lists
3. (Optional) Run `scripts/merge_final.py` → merges manually annotated data (e.g. skin concern tags)

Update `INPUT_PATH` / `OUTPUT_PATH` in each script to match your local environment.

## Documentation

- [`docs/data_pipeline.md`](./docs/data_pipeline.md) — API specification, steps for reuse, known issues and how they're handled (**start here when adapting this to a new category**)
- [`docs/data_collection_process.md`](./docs/data_collection_process.md) — Build log documenting how the pipeline was developed (handling the SPA, discovering the internal APIs, dealing with rate limits)

## Directory Structure

```
.
├── scripts/           # Collection & processing scripts
├── docs/               # Documentation
├── 01_raw_data/        # Raw data (gitignored, local only)
└── 02_clean_data/       # Processed data (gitignored, local only)
```

## A Note on Data Handling

CSV files under `01_raw_data/` and `02_clean_data/` are excluded from the repository via
`.gitignore`. Out of consideration for copyright and EU database rights around product
descriptions, this repository publishes only the code (which anyone can use to re-collect
the same data), not the raw scraped data itself.

## Related Articles

- [初回のプロトタイプ分析](https://zenn.dev/yuki_hogehoge/articles/98cff955fbba69)
- [スクレイピング試行錯誤の記録](https://zenn.dev/yuki_hogehoge/articles/dm_data_collection_process)
