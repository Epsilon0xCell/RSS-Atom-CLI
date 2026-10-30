![Banner](banner.png)

# RSS-Atom-CLI
```
https://feedly.com/i
```

## Implementation

This project is complete and runnable. Run it:

```bash
python3 rss_tool.py https://example.com/feed.xml
python3 rss_tool.py feed1.xml feed2.xml --limit 5
python3 rss_tool.py https://example.com/feed.xml --open 2
```

`--open N` prints item N's link on its own line after the listing. It does
not launch a browser, so the tool stays usable over SSH and in scripts.

Standard library only - no dependencies.
