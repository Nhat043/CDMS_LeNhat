# Vietful Products API

Notes after going through the [API docs](https://ext.stg.vnfai.com/doc/index.html) (v1.0) before designing the schema

## Endpoints

| Method | Path |
|---|---|
| GET | `/api/v1/Products` - list (`Keyword`, `PartnerSKUs`, `SKUs`, `PageIndex`, `PageSize`) |
| POST | `/api/v1/Products` - create (accepts an array) |
| GET | `/api/v1/Products/{partnerSKU}` - details |
| PUT | `/api/v1/Products/{id}` - update |
| PUT | `/api/v1/Products/{id}/activate` |
| PUT | `/api/v1/Products/{id}/de-activate` |
| GET/POST/PUT | `/api/v1/Products/units` |

## Things I noticed

- No `updatedAt` or version: I can tell whether a product's content differs from what I stored, but not which version is newer. No date filter either, so polling means scanning the full list every time
- Pagination: `PageIndex` starts at `0`, and `PageSize` defaults to `10`.
- Product fields differ between endpoints: List, details and PUT return different fields (13, ~27, ~37). Even `units` has a different structure in each
- `isActive` isn't in the PUT body: it only changes through `activate` / `de-activate`.
- Inconsistent keys: details are keyed by `partnerSKU` (string), update and activate by `id` (integer)
- `categories` is required in POST and PUT, and units have their own PUT endpoint. Both can also be updated later

The `units` field needs to be normalized before hashing, otherwise the same product could produce different hashes

The list endpoint also misses fields like `taxRate` and `packingNote`. Getting those would mean an extra request per product

For now, I'll stick to the list fields and skip fetching individual product details. `units` and `categories` stay in, since both can change.
