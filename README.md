# dm.de Product Data Collection Pipeline

A pipeline for automatically collecting and processing product data (price, rating, ingredients)
from dm.de, a major German drugstore chain. Built for the Serum & Kur (serum/treatment) category,
but designed to be reusable for other categories as well.

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

> Note: the two documents above are currently written in Japanese.

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

- [Zenn article ([dm.de 製品データ収集パイプライン](https://zenn.dev/yuki_hogehoge/articles/dm_data_pipeline))]
