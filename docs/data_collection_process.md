# Data Collection Process: Automating dm.de Skincare Product Data Collection

## Background and Goal

In the initial analysis ([link: original article]), ingredients (Inhaltsstoffe) for the top
30 products in dm.de's Serum & Kur category were extracted **manually** from product
description text. This document records the process of automating that work.

- Automatically collecting ingredients, price, and rating for all 172 products (the full
  category as of 2026)
- Reducing manual work from "entering ratings" and "extracting ingredients" down to just
  "tagging some skin concerns"

As a result, data collection that originally took several days for 30 out of 179 products
(including manual work) was replaced with roughly 10 minutes of fully automated runtime for
all 172 products.

## Final Architecture

Because dm.de is a single-page application (SPA) that renders content with JavaScript,
directly scraping the HTML did not work. Instead, the pipeline calls two APIs that the site
itself uses internally.

```
1. Listing API (all product IDs, price, and rating within a category)
   GET https://product-search.services.dmtech.com/de/search/static
       ?allCategories.id=020211&pageSize=30&currentPage={0-5}
       &searchType=editorial-search&sort=editorial_relevance
       &type=search-static&enablePharmacy=true

2. Detail API (per-product ingredients and skin type)
   GET https://products.dm.de/product/products/detail/DE/dan/{artikelnummer}
```

The pipeline uses the listing API to get the `artikelnummer` (dan) for all 172 products, then
calls the detail API for each one to fill in the ingredient information.

## Trial and Error Log

### 1. HTML Scraping Failed

Fetching a product page's HTML directly with `requests` + `BeautifulSoup` found no occurrence
of the string "Inhaltsstoffe" at all. The HTML that came back was only 11KB, and even the
`<title>` tag did not reflect the product name. This indicated that dm.de is built as an SPA
that renders its content with JavaScript after the initial page load.

### 2. Discovering the Internal APIs

Using Chrome DevTools' Network tab, along with the `Ctrl+Shift+F` full-text search that
searches across all response bodies, the relevant XHR request was identified by searching for
a known ingredient name ("Glycerin"). This is how the detail API endpoint above was found.

The same technique was applied to the category listing page, which led to discovering the
listing API (`product-search.services.dmtech.com`) as well.

### 3. Verifying Access Was Permitted

- `dm.de/robots.txt`: only disallows `/gift-card-*`, `/search`, `/callback`, `/logout`,
  `/shopping-list`, and `/cart`. No restrictions related to product pages.
- `product-search.services.dmtech.com/robots.txt`: `Disallow:` is empty (no disallowed
  paths) → fully permitted.

Neither domain disallows the endpoints used in this pipeline.

### 4. Identifying the Pagination Parameter

The name of the listing API's pagination parameter was initially unknown. It was identified
as `currentPage` using two clues: the browser URL after clicking the "Mehr laden" (load more)
button on the site (in the form `currentPage0=1`), and the `currentPage` field name present in
the API response.

### 5. Handling Rate Limiting (429)

`429 Too Many Requests` occurred on the listing API starting from page 2. Since the request
URL changed from `/search/static` to `/search/crawl`, it's likely that pages beyond the first
are handled by a different internal route, possibly one with stricter limits.

The fix:
- Extended the interval between requests from 2 seconds to 8 seconds
- Implemented automatic retry (up to 5 attempts) that follows the `Retry-After` header when
  present, or otherwise increases the wait time with each attempt

This resolved the 429 errors and allowed all 172 products to be collected reliably.

### 6. Direct Confirmation of the Pagination Parameter

The `currentPage` parameter name in step 4 above was originally inferred indirectly, from the
browser's address bar rather than the actual network request. Later, the actual XHR request
made by the site (captured via DevTools' "Copy as cURL") was inspected directly, confirming
that `currentPage` is indeed the exact parameter name used by the API. No code changes were
needed, since the pipeline was already using the correct name.

## Data Collected

| Column | Source API | Coverage (of 172) |
|---|---|---|
| artikelnummer, brand, name, price_eur | Listing API | 100% |
| rating_value, rating_count | Listing API | 100% |
| categories | Listing API | 100% |
| hauttyp (skin type) | Detail API | ~80% (remainder not listed on the site) |
| ingredients_raw (raw ingredient text) | Detail API | 100% |

## Known Limitations and Future Work

- `price_eur` is still a German-formatted string (e.g. `"4,95 €"`) and needs to be converted
  to numeric before analysis
- `ingredients_raw` is comma-separated raw text; using ingredient rank as a feature requires
  a separate normalization step
- Neither API provides anything equivalent to a `concern` (skin-concern) tag; whether the
  `categories` column (e.g. "Anti Aging") can serve as a substitute still needs verification
- ~~The listing API's `currentPage` parameter name was inferred from the browser URL rather
  than the actual network request~~ — **resolved**: a later inspection of the actual XHR
  request confirmed `currentPage` is indeed the correct parameter name

## Ethical Considerations

- Both domains' robots.txt files were checked before running, to confirm the endpoints used
  were not disallowed
- Deliberate delays (2-8 seconds) were added between requests to limit server load
- On receiving a 429 error, the implementation retries with an increasing wait time rather
  than retrying immediately
- All data collected falls within information already shown on public product pages
