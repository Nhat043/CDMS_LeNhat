# Design decisions

## 1. Ordering changes without a version field

The Vietful API has no `updatedAt`, `version` or `etag`, so I use `observed_at` to track when the data was read.

`ingest_event` has this column. Each channel will set it when I implement that part.

An older webhook arriving after a newer poll should be ignored rather than overwrite the newer data. I didn't add a version counter to the emulator because the real API doesn't have one. All senders share the same clock in this setup.

## 2. What counts as a product

I only track the 13 fields from `GET /Products`. Fetching details for every product would mean N+1 requests on each poll.

I still include `units` and `categories` because both can change after creation.

## 3. Storing diffs rather than snapshots

`product_change` stores diffs instead of full snapshots (`{field: {from, to}}`). Nothing writes to it yet.

`product_state` keeps the full snapshot for comparison. Without it, there's nothing to calculate diffs against.

The downside is that rebuilding an older state requires replaying the changes.

## 4. Two databases instead of two schemas

CDMS can't JOIN directly with the emulator's database, so it has to use HTTP.

That's intentional. The exercise is about integrating with an external service, not sharing tables.

Both databases currently run on the same Postgres instance. I'll split them into two containers in the Docker phase.

## 5. Exactly-once handling

Three database-level checks will handle duplicate events and stale data:

- `ingest_event.dedup_key` UNIQUE: prevents duplicate inputs.
- `product_change.event_id` UNIQUE: one event can only create one change.
- `observed_at` on both the event and state: compared under a row lock when the processor is implemented.

These checks live in the database, so they also work with retries and concurrent workers.

## 6. No migrations for the emulator

Only CDMS uses Alembic. The emulator is a stand-in for an external service, so its tables are created at startup with `create_all()`.

## 7. Keeping the API's inconsistencies

I'm keeping the original API behavior rather than cleaning it up:

- `units`: strings in list, objects in details.
- `hasExpiration` vs `isExpiryDate`.
- POST uses numeric `serialType`, responses use boolean `hasSerial`.
- Details use `partnerSKU` (string), updates use `id` (integer).
- List returns an array without a total count.

These are the kinds of issues CDMS needs to handle. I'll normalize each payload before comparing it.

## 8. Normalising before comparing

All payloads are converted to the same shape before hashing.

- `units` and `categories` are sorted because their order has no business meaning. If the API returns them in a different order, that shouldn't count as a change.
- The two expiry flag names are mapped to `hasExpiration`.
- The hash is SHA-256 of the normalised JSON, with `sort_keys=True`. Comparing hashes is simpler than comparing nested JSON directly.
- A test confirms that the same product from the list and detail endpoints produces the same hash.

## 9. Processing one event

There are three possible outcomes: `APPLIED`, `NO_CHANGE`, and `STALE`.

There is no `DUPLICATE` outcome. Duplicate events are rejected at the database level by the unique `dedup_key` constraint, before they reach the processor. The two checks serve different purposes.

- `NO_CHANGE` still advances `observed_at`. Without this, an older event could arrive later and be accepted.
- Processing is serialized with `pg_advisory_xact_lock(product_id)` rather than `SELECT ... FOR UPDATE`. When a product is seen for the first time, there is no state row to lock. Two workers could both try to insert it, causing one to fail on the primary key. The advisory lock works without an existing row.

## 10. Testing

- The decision logic uses pure functions, so it can be tested without a database.
- Database tests run against PostgreSQL, not SQLite. SQLite doesn't support advisory locks or `JSONB`, and handles timezone-aware datetimes differently, which could hide comparison issues.
- Each test runs inside an outer transaction. Since `process()` calls `commit()`, the session uses a savepoint. The outer transaction is rolled back after the test, so no data is left behind.
- There is no separate test database yet. Setting one up is the next step if I need to run tests in parallel.