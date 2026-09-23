"""
skincare_dataset_full.csv (172件) に対して以下を行うスクリプト:
    1. price_eur ("4,95 €" のようなドイツ語表記) を数値に変換
    2. ingredients_raw (カンマ区切りの生テキスト) を、
       注目成分ごとの「配合有無・配合順位・正規化順位」の列に変換

使い方:
    INPUT_PATH を実際のファイルパスに合わせて実行してください。
    出力は OUTPUT_PATH に保存されます(元のファイルは上書きしません)。
"""

import pandas as pd

INPUT_PATH = "02_clean_data/skincare_dataset_full.csv"
OUTPUT_PATH = "02_clean_data/skincare_dataset_full_processed.csv"

# 注目したい成分と、マッチさせるキーワード(小文字で判定するので大文字小文字は気にしなくてOK)
# 必要に応じて増減してください
KEY_INGREDIENT_KEYWORDS = {
    "niacinamide": ["niacinamide"],
    "hyaluronic_acid": ["hyaluronate", "hyaluronic acid"],
    "retinol": ["retinol", "retinal"],
    "vitamin_c": ["ascorbic acid", "ascorbyl"],
    "glycerin": ["glycerin"],
    "alcohol_denat": ["alcohol denat"],
    "fragrance": ["parfum", "fragrance"],
}


def clean_price(price_str) -> float | None:
    """'4,95 €' -> 4.95 に変換"""
    if pd.isna(price_str):
        return None
    cleaned = str(price_str).replace("€", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_ingredients(raw: str) -> list[str]:
    """
    カンマ区切りの生テキストを、成分名のリストに変換(順序=配合順位を維持)

    dm.deはブランドによって成分の区切り文字が統一されておらず、
    カンマ(,)以外に bullet(•)や middle dot(·)、改行区切りのケースがある。
    ここではそれらを一旦カンマに統一してから分割する。
    """
    if pd.isna(raw) or not raw:
        return []

    cleaned = str(raw)
    for bullet_char in ["•", "·", "・"]:
        cleaned = cleaned.replace(bullet_char, ",")
    # 改行区切りのケース(複数バリエーション商品が1欄にまとまっている等)にも対応
    cleaned = cleaned.replace("\n", ",")

    parts = [p.strip(" .*") for p in cleaned.split(",")]

    # 空文字、見出し行(コロンで終わる行)、脚注文言を除外
    skip_prefixes = ("ingredients from", "from natural")
    parts = [
        p for p in parts
        if p and not p.endswith(":") and not p.lower().startswith(skip_prefixes)
    ]

    # 重複除去(順序は維持)。複数バリエーションが混在するケースで同じ成分が
    # 何度も出てくるのを防ぐため
    return list(dict.fromkeys(parts))


def find_rank(ingredient_list: list[str], keywords: list[str]) -> int | None:
    """ingredient_list の中から keywords のいずれかを含む最初の成分の順位(1始まり)を返す"""
    for i, ing in enumerate(ingredient_list, start=1):
        ing_lower = ing.lower()
        if any(kw in ing_lower for kw in keywords):
            return i
    return None


def has_multiple_variants(raw: str) -> bool:
    """
    '〇〇-Kur:' のような見出しが複数含まれる場合、1つの成分欄に
    複数バリエーション商品の成分がまとめて入っている可能性が高い。
    後で人間が確認できるようフラグを立てる。
    """
    if pd.isna(raw):
        return False
    headers = [line for line in str(raw).split("\n") if line.strip().endswith(":")]
    return len(headers) >= 2


def add_ingredient_features(df: pd.DataFrame) -> pd.DataFrame:
    df["ingredients_multi_variant_flag"] = df["ingredients_raw"].apply(has_multiple_variants)
    df["ingredients_list"] = df["ingredients_raw"].apply(parse_ingredients)
    df["ingredient_count"] = df["ingredients_list"].apply(len)

    for key, keywords in KEY_INGREDIENT_KEYWORDS.items():
        rank_col = f"{key}_rank"
        present_col = f"{key}_present"
        rank_norm_col = f"{key}_rank_norm"

        df[rank_col] = df["ingredients_list"].apply(lambda lst: find_rank(lst, keywords))
        df[present_col] = df[rank_col].notna().astype(int)
        df[rank_norm_col] = df[rank_col] / df["ingredient_count"]

    return df


def main():
    df = pd.read_csv(INPUT_PATH)
    print(f"読み込み: {len(df)}件")

    df["price_eur_clean"] = df["price_eur"].apply(clean_price)
    n_price_missing = df["price_eur_clean"].isna().sum()
    print(f"価格変換: 失敗 {n_price_missing}件")

    df = add_ingredient_features(df)
    n_multi = df["ingredients_multi_variant_flag"].sum()
    print(f"複数バリエーション疑いの商品: {n_multi}件(要目視確認)")

    # ingredients_list はリスト型なので、CSV保存用にセミコロン区切りの文字列に変換
    df["ingredients_list_str"] = df["ingredients_list"].apply(lambda lst: ";".join(lst))
    df = df.drop(columns=["ingredients_list"])

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"保存しました: {OUTPUT_PATH}")

    # 簡単な確認表示
    for key in KEY_INGREDIENT_KEYWORDS:
        n_present = df[f"{key}_present"].sum()
        print(f"  {key}: {n_present}/{len(df)}件で配合を確認")


if __name__ == "__main__":
    main()
