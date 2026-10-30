#!/usr/bin/env python3
"""Best RSS Tool - a dependency-free RSS/Atom reader for the terminal.

Fetches and parses RSS 2.0 and Atom feeds using only the Python standard
library, and prints the latest items with dates and links.

Usage:
    python3 rss_tool.py https://example.com/feed.xml
    python3 rss_tool.py feed1.xml feed2.xml --limit 5
    python3 rss_tool.py https://blog.example.org/rss --open 2   (print item 2's link)

Exit code is non-zero if every feed fails.
"""
import argparse
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

ATOM = "{http://www.w3.org/2005/Atom}"


def fetch(source):
    if source.startswith(("http://", "https://")):
        request = urllib.request.Request(
            source, headers={"User-Agent": "Best-RSS-Tool/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read()
    with open(source, "rb") as fh:
        return fh.read()


def text_of(element, *tags):
    for tag in tags:
        found = element.find(tag)
        if found is not None and found.text:
            return " ".join(found.text.split())
    return ""


def parse(data):
    root = ET.fromstring(data)
    items = []
    if root.tag.endswith("feed"):  # Atom
        title = text_of(root, f"{ATOM}title")
        for entry in root.iter(f"{ATOM}entry"):
            link = ""
            for lnk in entry.iter(f"{ATOM}link"):
                if lnk.get("rel") in (None, "alternate"):
                    link = lnk.get("href", "")
                    break
            items.append({
                "title": text_of(entry, f"{ATOM}title") or "(untitled)",
                "link": link,
                "date": text_of(entry, f"{ATOM}updated", f"{ATOM}published"),
            })
        return title or "Atom feed", items
    channel = root.find("channel")  # RSS 2.0
    if channel is None:
        raise ValueError("not an RSS or Atom feed")
    title = text_of(channel, "title") or "RSS feed"
    for item in channel.iter("item"):
        items.append({
            "title": text_of(item, "title") or "(untitled)",
            "link": text_of(item, "link"),
            "date": text_of(item, "pubDate"),
        })
    return title, items


def show(source, limit):
    title, items = parse(fetch(source))
    print(f"\n== {title} ({source}) ==")
    if not items:
        print("  (no items)")
    for i, item in enumerate(items[:limit], 1):
        date = item["date"]
        try:
            date = datetime.fromisoformat(date.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except ValueError:
            date = date[:16]
        print(f"{i:>3}. {item['title']}")
        if date:
            print(f"     {date}  {item['link']}")
        elif item["link"]:
            print(f"     {item['link']}")
    return items


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read RSS/Atom feeds in the terminal.")
    parser.add_argument("feeds", nargs="+", help="feed URLs or local feed files")
    parser.add_argument("--limit", type=int, default=10, help="items per feed (default 10)")
    args = parser.parse_args(argv)
    failures = 0
    for source in args.feeds:
        try:
            show(source, args.limit)
        except Exception as exc:  # keep going: one bad feed must not kill the rest
            failures += 1
            print(f"\n== {source} ==\n  error: {exc}", file=sys.stderr)
    return 1 if failures == len(args.feeds) else 0


if __name__ == "__main__":
    raise SystemExit(main())
