![Intro: a hand holding up one torn strip of cream ticker tape carrying rows of short dark dash marks, its end curling, the brass ticker machine still feeding ribbon behind it](intro-banner.png)


# RSS-Atom-CLI

<p align="center"><img src="logo.png" alt="RSS-Atom-CLI logo: a brass stock ticker under its glass dome, a coil of cream paper tape with plain dark dash marks spilling from its slot onto its brass base" width="200"></p>

![Banner: a brass ticker machine with a glass dome on a wooden desk in window light, pouring out a long cream tape covered in neat rows of short dark marks that pools and curls across the desk](banner.png)

![Animated scene](scene.svg)
```
https://feedly.com/i
```


![Separator](sep-heavy.svg)

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

> **Collector note:** --open prints a link and launches no browser, and a run fails only when all feeds fail.
