"""
dm.de の2つの内部APIを組み合わせて、カテゴリ内の全商品データを自動取得するスクリプト

使っているAPI:
    1. 一覧API (product-search.services.dmtech.com)
       → カテゴリ内の商品一覧・価格・rating を取得(ページング必要)
    2. 詳細API (products.dm.de) ※前回作成済み
       → 各商品の成分(Inhaltsstoffe)・肌タイプを取得

注意:
    一覧APIのページ送りパラメータ名(PAGE_PARAM_NAME)は未確定です。
    DevToolsで2ページ目のURLを確認し、下の PAGE_PARAM_NAME を実際のパラメータ名に
    書き換えてから実行してください(現時点では "page" と仮定しています)。
追記: 
    currentPageというパラメータ名は、当初ブラウザのアドレスバーからの類推でしたが、
    その後実際のXHRリクエスト(DevToolsの「Copy as cURL」)を直接確認し、
    正しいパラメータ名であることが確定しました。(2026/09/24)
"""

import time
import csv
import os
import requests

# --- 一覧API ---------------------------------------------------------------
LIST_URL = "https://product-search.services.dmtech.com/de/search/static"
LIST_PARAMS_BASE = {
    "allCategories.id": "020211",   # Serum & Kur のカテゴリID
    "pageSize": 30,
    "searchType": "editorial-search",
    "sort": "editorial_relevance",
    "type": "search-static",
    "enablePharmacy": "true",
}
# ブラウザURLの "currentPage0=1" というパターンと、JSONレスポンスの "currentPage" という
# フィールド名から、APIパラメータ名は "currentPage" と推測(要検証)
PAGE_PARAM_NAME = "currentPage"

LIST_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "origin": "https://www.dm.de",
    "referer": "https://www.dm.de/",
    "user-agent": "Mozilla/5.0 (research script; contact: your_email@example.com)",
}

# --- 詳細API -----------------------------------------------------------------
DETAIL_URL_TEMPLATE = "https://products.dm.de/product/products/detail/DE/dan/{}"
DETAIL_HEADERS = {
    "accept": "application/json",
    "origin": "https://www.dm.de",
    "referer": "https://www.dm.de/",
    "user-agent": "Mozilla/5.0 (research script; contact: your_email@example.com)",
}

OUTPUT_PATH = "02_clean_data/skincare_dataset_full.csv"
REQUEST_DELAY_SEC = 2.0
LIST_REQUEST_DELAY_SEC = 8.0  # 一覧APIは429が出たため、間隔を長めに取る
MAX_RETRIES = 5


def request_with_retry(url: str, headers: dict, params: dict = None) -> requests.Response:
    """429(Too Many Requests)が出たら待って再試行する"""
    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code != 429:
            resp.raise_for_status()
            return resp

        # Retry-After ヘッダーがあればそれに従い、無ければ指数関数的に待機時間を伸ばす
        wait_sec = int(resp.headers.get("Retry-After", 0)) or (10 * attempt)
        print(f"  429 Too Many Requests。{wait_sec}秒待って再試行します "
              f"({attempt}/{MAX_RETRIES})")
        time.sleep(wait_sec)

    raise RuntimeError(f"{MAX_RETRIES}回リトライしても429が解消しませんでした: {url}")


def fetch_all_listing() -> list[dict]:
    """一覧APIを全ページ叩いて、商品の基本情報+ratingを集める"""
    all_products = []
    page = 0
    total_pages = 1  # 最初は不明なので仮に1にしておき、1ページ目のレスポンスで更新する

    while page < total_pages:
        params = dict(LIST_PARAMS_BASE)
        params[PAGE_PARAM_NAME] = page

        print(f"一覧取得中: page={page}")
        resp = request_with_retry(LIST_URL, LIST_HEADERS, params)
        data = resp.json()

        total_pages = data.get("totalPages", 1)
        returned_page = data.get("currentPage")
        if returned_page != page:
            print(f"  警告: 要求したpage={page} と レスポンスのcurrentPage={returned_page} が一致しません。"
                  f" PAGE_PARAM_NAME が変更されていないか確認してください。")

        for p in data.get("products", []):
            rating = p.get("context", {}).get("rating", {}) or {}
            all_products.append({
                "artikelnummer": p.get("dan"),
                "brand": p.get("brandName"),
                "name": p.get("title"),
                "price_eur": p.get("tileData", {}).get("price", {}).get("price", {}).get("current", {}).get("value"),
                "rating_value": rating.get("ratingValue"),
                "rating_count": rating.get("ratingCount"),
                "categories": ";".join(p.get("tileData", {}).get("trackingData", {}).get("categories", [])),
            })

        page += 1
        time.sleep(LIST_REQUEST_DELAY_SEC)

    print(f"一覧取得完了: {len(all_products)}件")
    return all_products


def find_group(description_groups: list, header_name: str):
    for group in description_groups:
        if group.get("header") == header_name:
            return group
    return None


def fetch_detail(dan: int) -> dict:
    """詳細APIから成分・肌タイプを取得"""
    url = DETAIL_URL_TEMPLATE.format(dan)
    resp = request_with_retry(url, DETAIL_HEADERS)
    data = resp.json()
    groups = data.get("descriptionGroups", [])

    ingredients_raw = None
    ing_group = find_group(groups, "Inhaltsstoffe")
    if ing_group and ing_group.get("contentBlock"):
        texts = ing_group["contentBlock"][0].get("texts", [])
        if texts:
            raw = texts[0]
            ingredients_raw = raw.split(":", 1)[-1].strip() if raw.upper().startswith("INGREDIENTS") else raw

    hauttyp = None
    merkmale_group = find_group(groups, "Produktmerkmale")
    if merkmale_group and merkmale_group.get("contentBlock"):
        for block in merkmale_group["contentBlock"]:
            for item in block.get("descriptionList", []):
                if item.get("title") == "Hauttyp":
                    hauttyp = item.get("description")

    return {"hauttyp": hauttyp, "ingredients_raw": ingredients_raw}


def main():
    listing = fetch_all_listing()

    rows = []
    for i, item in enumerate(listing, start=1):
        dan = item["artikelnummer"]
        print(f"[{i}/{len(listing)}] 詳細取得中: dan={dan}")
        try:
            detail = fetch_detail(dan)
        except requests.RequestException as e:
            print(f"  エラー: dan={dan} -> {e}")
            detail = {"hauttyp": None, "ingredients_raw": None}

        rows.append({**item, **detail})
        time.sleep(REQUEST_DELAY_SEC)

    folder = os.path.dirname(OUTPUT_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)

    fieldnames = ["artikelnummer", "brand", "name", "price_eur", "rating_value",
                  "rating_count", "categories", "hauttyp", "ingredients_raw"]
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"保存しました: {OUTPUT_PATH} ({len(rows)}件)")


if __name__ == "__main__":
    main()
