"""
172件の自動取得データ(skincare_dataset_full_processed.csv)に、
既存30件の手動データ(concern・product_typeなど)を結合する最終スクリプト。

結合キー: artikelnummer
30件に該当しない142件は、concern系の列がすべて欠損(NaN)のまま出力される。
"""

import pandas as pd

FULL_PATH = "01_raw_data/skincare_dataset_full_processed.csv"
MANUAL_PATH = "02_clean_data/skincare_dataset_dm_serum_top30_artikelnummer.csv"
OUTPUT_PATH = "02_clean_data/skincare_dataset_final.csv"

# 既存30件データのうち、今回追加したい列だけを選ぶ
# (price_eur, rating, number_of_reviews は新しいデータと重複するため、
#  検証用に別名で残す)
MANUAL_COLUMNS = [
    "artikelnummer",
    "product_type",
    "private_label",
    "concern_acne",
    "concern_sensitive",
    "concern_dry",
    "concern_oily",
    "concern_anti_aging",
    "concern_dark_spots",
    "concern_redness",
    "concern_dehydrated",
    "active_ingredient",
    "price_eur",
    "rating",
    "number_of_reviews",
]


def main():
    full_df = pd.read_csv(FULL_PATH)
    manual_df = pd.read_csv(MANUAL_PATH)[MANUAL_COLUMNS]

    manual_df = manual_df.rename(columns={
        "price_eur": "price_eur_manual_check",
        "rating": "rating_manual_check",
        "number_of_reviews": "number_of_reviews_manual_check",
    })

    merged = full_df.merge(manual_df, on="artikelnummer", how="left")

    # どの行が手動データ(30件)由来かを示すフラグ列
    merged["has_manual_annotation"] = merged["product_type"].notna()

    n_matched = merged["has_manual_annotation"].sum()
    print(f"結合結果: {len(merged)}件中 {n_matched}件に手動アノテーションあり")

    # 検証用: 価格・ratingが大きくズレている行がないか一応チェック
    check = merged[merged["has_manual_annotation"]].copy()
    check["price_diff"] = check["price_eur_clean"] - check["price_eur_manual_check"]
    check["rating_diff"] = check["rating_value"] - check["rating_manual_check"]
    big_diff = check[(check["price_diff"].abs() >= 0.5) | (check["rating_diff"].abs() >= 0.2)]
    if len(big_diff) > 0:
        print(f"注意: {len(big_diff)}件で価格またはratingに無視できない差があります")
        print(big_diff[["artikelnummer", "name", "price_diff", "rating_diff"]])
    else:
        print("価格・ratingのズレは許容範囲内でした")

    merged.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"保存しました: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
