# Database schema

Two databases. The emulator owns one, CDMS owns the other, and CDMS has no way to read the emulator's tables - PostgreSQL won't join across databases, so it has to go through the HTTP API.

## How data moves

```
inventory.products          the source, as Vietful would have it
        |
        | polling / callback client / spreadsheet
        v
cdms.ingest_event           inbox: every input, whatever the channel
        |
        | worker
        v
cdms.product_state          latest accepted snapshot, used for comparison
cdms.product_change         append-only log of what actually changed
```

## inventory.products

Managed with `create_all()` on startup, not migrations - it stands in for someone else's system.

| Column | Type | |
|---|---|---|
| `product_id` | SERIAL PK | the emulator generates these |
| `partner_sku` | VARCHAR(100) UNIQUE | `GET /Products/{partnerSKU}` looks products up by it |
| `sku`, `product_name` | VARCHAR | |
| `asset_type`, `color`, `size` | VARCHAR(50) | |
| `has_serial`, `has_expiration`, `is_active` | BOOLEAN | |
| `description` | TEXT | |
| `units`, `categories` | JSONB | the API returns nested lists; the emulator doesn't need them normalised |

## cdms.ingest_batch

One ingestion run: a polling cycle or an uploaded file. Webhooks have no batch.

| Column | Type | |
|---|---|---|
| `batch_id` | UUID PK | |
| `channel` | TEXT | CHECK: POLLING or EXCEL |
| `source_name` | TEXT | file name for uploads |
| `created_at` | TIMESTAMPTZ | |

## cdms.ingest_event

The inbox. One row per product snapshot received, whatever the channel.

| Column | Type | |
|---|---|---|
| `event_id` | UUID PK | |
| `batch_id` | UUID FK | null for webhooks |
| `channel` | TEXT | CHECK: WEBHOOK, POLLING or EXCEL |
| `dedup_key` | TEXT **UNIQUE** | `webhook:{sender id}` / `poll:{batch}:{product}` / `excel:{batch}:{row}` |
| `product_id` | INTEGER | null when the row couldn't be read |
| `observed_at` | TIMESTAMPTZ | when the sender read the data, not when it arrived |
| `raw_payload` | JSONB | exactly what came in |
| `payload` | JSONB | normalised, filled by the worker |
| `content_hash` | CHAR(64) | SHA-256 of the normalised payload |
| `status` | TEXT | see below |
| `attempts`, `error_message` | | for a retry mechanism that isn't built yet |
| `received_at`, `processed_at` | TIMESTAMPTZ | |

Index on `(status, received_at)` so the worker can pick up the oldest pending work cheaply.

Statuses: `PENDING`, `APPLIED`, `NO_CHANGE`, `STALE`, `INVALID`, `FAILED`.

## cdms.product_state

The latest accepted snapshot per product. It exists so there is something to compare against - it's a buffer, not the deliverable.

| Column | Type | |
|---|---|---|
| `product_id` | INTEGER PK | Vietful's id, not generated here |
| `payload` | JSONB | normalised |
| `content_hash` | CHAR(64) | |
| `observed_at` | TIMESTAMPTZ | the watermark; anything older is rejected |
| `last_event_id` | UUID | which event produced this state |
| `updated_at` | TIMESTAMPTZ | |

## cdms.product_change

What the service is actually for. Append-only.

| Column | Type | |
|---|---|---|
| `change_id` | UUID PK | |
| `product_id` | INTEGER | |
| `event_id` | UUID FK **UNIQUE** | one event can only ever produce one change |
| `kind` | TEXT | CREATED or UPDATED |
| `diff` | JSONB | only the fields that moved: `{field: {from, to}}` |
| `observed_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |

Index on `(product_id, observed_at)`.

## Idempotency and ordering

| | |
|---|---|
| `ingest_event.dedup_key` UNIQUE | The same input can't enter the inbox twice, even if a sender retries. |
| `product_change.event_id` UNIQUE | One event can't create more than one change record. |
| `observed_at` on both event and state | Compared under `pg_advisory_xact_lock(product_id)`, so an older snapshot can't overwrite a newer one. |

These rules live in the database rather than relying on Python checks alone. That way, they still apply when requests race or multiple workers try to process the same product.