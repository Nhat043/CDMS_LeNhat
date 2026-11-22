# Lessons Learned

## 1. The bug only showed up when I added a second channel

The webhook sent data from the detail endpoint, which uses `isExpiryDate`. Polling used the list endpoint, which returns `hasExpiration`.

I hadn't added `isExpiryDate` to `WebhookProduct`, so Pydantic ignored it. After `model_dump()`, the payload had `hasExpiration: None`.

The normalisation code used:

```python
raw.get("hasExpiration", raw.get("isExpiryDate"))
```

I expected it to fall back to `isExpiryDate`, but `dict.get()` only uses the default when the key is missing. Here, the key existed and its value was `None`.

That made CDMS record a change even though the product hadn't actually changed.

With one channel, everything looked consistent. It was still wrong. The second channel exposed it.

## 2. The seed script ran just by being imported

I put the seed code at module level to keep the script short and left out the `if __name__ == "__main__"` guard.

While checking something else, I ran `import scripts.seed` and it inserted 20 products into the database.

A small shortcut, but one that had a real side effect. Scripts that write to a database shouldn't run just because another module imports them.

## 3. The worker died, but the inbox kept the events

During a test, Docker killed the worker with `exit 137` because my machine ran out of memory.

There were 402 events waiting in the inbox. None of them were lost. When I started the worker again, it picked them up and processed them.

I hadn't planned to test recovery this way. But it was a good reminder of why I put events in the inbox before processing them. The first real failure showed that the approach worked.