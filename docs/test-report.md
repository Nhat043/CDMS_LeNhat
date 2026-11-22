# Test Report

## Environment

The stack ran on Windows 11 with Docker Desktop and Docker Compose. It had five containers: two Postgres databases, the inventory emulator, CDMS API, and worker

## Tests

There are 22 tests, run with `uv run pytest -q`. The decision logic is tested with plain functions. Tests that touch the database run against PostgreSQL inside a transaction that's rolled back after each test

I ran two bursts of 200 webhook requests.

- **A – Same event ID:** 200 concurrent requests in 1.98s. One was accepted, the other 199 were duplicates. Only one row was stored
- **B – Same content, different event IDs:** 200 concurrent requests in 2.09s. All had different IDs but the same product content. Only one change was created.

Polling kept running every 30 seconds during both bursts. Afterward, I checked every `product_state`: its hash matched the event that last updated it, and there was no `APPLIED` event with a newer `observed_at` than the state. No lost updates showed up.

Across multiple runs, the database had 2,424 events, 26 changes, and 21 product states

One thing worth mentioning: 506 events ended up as `STALE`. The test deliberately used different `observed_at` values and sent events out of order. The processor rejected older events, leaving the state at the newest version.

## Limits and things that happened

This was all on one machine with one worker. I haven't tested multiple workers running at the same time

The timings above are for short bursts, not a sustained load test. I haven't measured meaningful throughput in requests per second.

During one run, Docker killed the worker because the machine ran out of memory (`exit 137`). There were 402 events still in the inbox. None were lost, and the worker processed all of them after it came back up

That wasn't an intentional test, but it was a useful check: the inbox kept the events while the worker was down.