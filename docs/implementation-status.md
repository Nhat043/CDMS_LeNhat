# Implementation Status

## Done

**Vietful emulator**

Six endpoints, with the awkward parts of the original API kept as they are. Sample data is generated with Faker.

**CDMS schema**

Four tables, managed with Alembic migrations.

**Change detection**

`normalise → hash → decide → diff`. Kept in a standalone module with no database or HTTP dependencies.

**Webhook**

Accepts events into the inbox, deduplicates with a unique constraint, and rejects timestamps without a timezone.

**Polling**

Scheduled full scan. `observed_at` is recorded for each page.

**Excel**

File upload, row-by-row validation, and a batch status endpoint with per-row errors.

**Worker**

One loop handles all three channels. It keeps running if the inventory service is down or an event fails.

**Docker**

Separate Postgres containers for the two databases, plus the inventory emulator, CDMS API, and worker. Migrations run once before the app services start.

**Tests**

22 tests and a script for burst and concurrency checks.

## Not done yet

**No retries for `FAILED` events.**

They stay in that state for now. The table already has `attempts` and `error_message`, but there's no retry or backoff logic.

**No multi-worker test yet.**

The advisory lock and unique constraints are there for concurrency, but I haven't tested multiple workers running together.

**Only 13 fields are tracked.**

These are the fields returned by `GET /Products`. Fields like `taxRate`, `packingNote`, and `productBundles` are only available from the detail endpoint. Tracking them would mean an extra request for every product during each poll.

**No authentication.**

None of the endpoints require authentication yet.

**No separate test database.**

Tests currently use the development PostgreSQL database, with each test running inside a transaction that's rolled back afterward.

**No Docker volumes.**

`docker compose down` removes the data. This is intentional for repeatable demos, but not suitable for production.

**No sustained throughput test.**

So far I've only checked correctness under short bursts.

**The emulator isn't a complete copy of the real API.**

It doesn't include the UOM endpoints, and its PUT endpoint only accepts the fields CDMS tracks.

## About worker recovery

There is no event lease in the current setup. With one worker, processing an event happens inside a database transaction. If the worker is killed before the transaction commits, PostgreSQL rolls it back and the event stays `PENDING`. The worker can pick it up again when it starts.

This doesn't solve event claiming between multiple workers. If I add more workers, I'll need to make that part safe too, so two workers don't pick up the same pending event at once.