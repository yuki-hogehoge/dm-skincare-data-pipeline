# データ収集プロセス: dm.de スキンケア製品データの自動取得

## 背景・目的

初回の分析([リンク: 元記事])では、dm.de の Serum & Kur カテゴリ上位30製品について、成分(Inhaltsstoffe)を製品説明文から**手動で抽出**していた。この記事では、以下を自動化した過程を記録する。

- 全172製品(2026年時点でのカテゴリ全件)の成分・価格・評価(rating)の自動取得
- 手動作業を「rating入力」「成分抽出」から「一部のconcernタグ付けのみ」まで縮小

結果として、初回は179件中30件・手動作業込みで数日かかっていたデータ収集が、172件・完全自動で約10分の実行時間に置き換わった。

## 最終的なアーキテクチャ

dm.de はSPA(JavaScriptで描画するサイト)のため、HTMLを直接スクレイピングする方法は機能しなかった。代わりに、サイトが内部で呼んでいる2つのAPIを直接叩く方式にした。

```
1. 一覧API(カテゴリ内の全製品ID・価格・rating取得)
   GET https://product-search.services.dmtech.com/de/search/static
       ?allCategories.id=020211&pageSize=30&currentPage={0-5}
       &searchType=editorial-search&sort=editorial_relevance
       &type=search-static&enablePharmacy=true

2. 詳細API(製品ごとの成分・肌タイプ取得)
   GET https://products.dm.de/product/products/detail/DE/dan/{artikelnummer}
```

一覧APIで172件全件の `artikelnummer` (dan) を取得し、それぞれについて詳細APIを呼び出して成分情報を補完する、という2段構成になっている。

## 試行錯誤の記録

### 1. HTMLスクレイピングの失敗

`requests` + `BeautifulSoup` で商品ページのHTMLを直接取得したところ、"Inhaltsstoffe" の文字列自体が存在しなかった。取得したHTMLはわずか11KBで、`<title>` タグも商品名を反映していなかった。これはdm.deがJavaScriptでコンテンツを後から描画するSPA構成であることを示していた。

### 2. 内部APIの発見

Chrome DevToolsのNetworkタブと、レスポンス本文を横断検索できる `Ctrl+Shift+F` の全文検索機能を使い、既知の成分名("Glycerin")で検索することで、該当するXHRリクエストを特定した。この方法で、上記の詳細APIのエンドポイントを発見した。

同様の手法をカテゴリ一覧ページに適用し、一覧API(`product-search.services.dmtech.com`)も発見した。

### 3. アクセス許可の確認

- `dm.de/robots.txt`: `/gift-card-*`, `/search`, `/callback`, `/logout`, `/shopping-list`, `/cart` のみ禁止。商品ページ関連の制限なし。
- `product-search.services.dmtech.com/robots.txt`: `Disallow:` が空欄(禁止パス無し) → 全面許可。

いずれのドメインも、今回利用したエンドポイントへのアクセスを禁止していないことを確認した。

### 4. ページングパラメータの特定

一覧APIのページ送りパラメータ名は当初不明だった。サイト上で「Mehr laden」ボタンを押した際のブラウザURL(`currentPage0=1` という形式)と、APIレスポンスに含まれる `currentPage` フィールド名を手がかりに、実際のパラメータ名が `currentPage` であると特定した。

### 5. レート制限(429)への対応

一覧APIの2ページ目以降で `429 Too Many Requests` が発生した。リクエスト先URLが `/search/static` から `/search/crawl` に変わっていたことから、複数ページ目は別の内部経路(より厳格な制限がかかっている可能性がある経路)で処理されていると推測される。

対応として:
- リクエスト間隔を2秒→8秒に延長
- `Retry-After` ヘッダー(存在する場合)に従う、または試行回数に応じて待機時間を伸ばす、自動リトライ機構を実装(最大5回)

これにより、429エラーを解消しつつ全172件のデータを安定して取得できるようになった。

## 取得できたデータ

| 列 | 取得元API | 取得率(172件中) |
|---|---|---|
| artikelnummer, brand, name, price_eur | 一覧API | 100% |
| rating_value, rating_count | 一覧API | 100% |
| categories | 一覧API | 100% |
| hauttyp(肌タイプ) | 詳細API | 約80%(残りはサイト側に表記なし) |
| ingredients_raw(成分・生テキスト) | 詳細API | 100% |

## 既知の制約・今後の課題

- `price_eur` はドイツ語表記の文字列("4,95 €")のまま出力されており、分析前に数値への変換が必要
- `ingredients_raw` はカンマ区切りの生テキストであり、配合順位を特徴量として使うには正規化処理が別途必要
- `concern`(肌悩みタグ)に相当する情報は両APIに存在せず、`categories` 列(例: "Anti Aging")で代替できるかは要検証
- 一覧APIの `currentPage` パラメータ名は実際のNetwork通信ではなくブラウザURLからの類推で特定したため、将来的にAPI仕様が変わった場合は再確認が必要

## 倫理的配慮

- 両ドメインのrobots.txtを確認し、利用したエンドポイントが禁止対象でないことを確認した上で実行した
- サーバー負荷を抑えるため、リクエスト間に意図的な待機時間(2〜8秒)を設けた
- 429エラーを受けた際は、即座にリトライを繰り返すのではなく、待機時間を延ばした上でリトライする実装にした
- 取得したデータはすべて、公開されている製品ページに掲載されている情報の範囲内である
