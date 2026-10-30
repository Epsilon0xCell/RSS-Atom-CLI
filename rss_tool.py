#!/usr/bin/env python3
"""RSS-Atom-CLI - a dependency-free RSS/Atom reader for the terminal.

Fetches and parses RSS 2.0 and Atom feeds using only the Python standard
library, and prints the latest items with dates and links.

Usage:
    python3 rss_tool.py https://example.com/feed.xml
    python3 rss_tool.py feed1.xml feed2.xml --limit 5
    python3 rss_tool.py https://blog.example.org/rss --open 2

--open N prints item N's link again on its own line at the end of the
listing. It deliberately does not launch a browser: this tool gets used
over SSH and in scripts, where there may be no browser, and printing the
bare URL lets the caller decide what to do with it.

Exit code is non-zero if every feed fails.
"""
import argparse
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

# I keep the Atom namespace as one prefix string because every Atom
# tag lookup below needs it and I do not want it typed out ten times
# with ten chances to get it wrong.
ATOM = "{http://www.w3.org/2005/Atom}"


def fetch(source):
    # I decide remote versus local by the prefix alone. A path that
    # starts with http is a URL to me, and anything else is a file.
    if source.startswith(("http://", "https://")):
        # I send my own user agent so a feed host can tell this tool
        # apart from a browser, and I set a timeout so a dead host does
        # not hang a run that may have more feeds waiting after it.
        request = urllib.request.Request(
            source, headers={"User-Agent": "RSS-Atom-CLI/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read()
    # I read local files as bytes, same as the remote path returns.
    # The XML parser wants bytes when the file carries an encoding
    # declaration, so I keep both paths returning the same type.
    with open(source, "rb") as fh:
        return fh.read()


def text_of(element, *tags):
    # I try the tags in the order the caller gave me and take the first
    # one that has text. That order is my fallback rule: callers list
    # the tag they prefer first.
    for tag in tags:
        found = element.find(tag)
        if found is not None and found.text:
            # I collapse the whitespace because feed titles often carry
            # newlines and padding from the XML layout itself. I want
            # one clean line per title in the terminal.
            return " ".join(found.text.split())
    return ""


def parse(data):
    root = ET.fromstring(data)
    items = []
    # I spot an Atom feed by the root tag ending in feed. I use the
    # ending and not the full namespaced tag so the check holds even
    # if a feed serves the namespace in a form I did not predict.
    if root.tag.endswith("feed"):  # Atom
        title = text_of(root, f"{ATOM}title")
        for entry in root.iter(f"{ATOM}entry"):
            link = ""
            # An Atom entry can carry several links for different jobs.
            # I take the first one with no rel or with rel alternate,
            # because that is the readable article link. I skip the
            # self and edit links, which point at the feed machinery.
            for lnk in entry.iter(f"{ATOM}link"):
                if lnk.get("rel") in (None, "alternate"):
                    link = lnk.get("href", "")
                    break
            items.append({
                "title": text_of(entry, f"{ATOM}title") or "(untitled)",
                # I ask for updated before published. Updated is the
                # fresher stamp when a feed gives me both.
                "link": link,
                "date": text_of(entry, f"{ATOM}updated", f"{ATOM}published"),
            })
        return title or "Atom feed", items
    channel = root.find("channel")  # RSS 2.0
    # If there is no channel and the root was not a feed, I have a file
    # I do not understand. I raise instead of printing an empty listing
    # that would look like a feed with no posts.
    if channel is None:
        raise ValueError("not an RSS or Atom feed")
    title = text_of(channel, "title") or "RSS feed"
    # I walk items with iter and not findall on direct children because
    # some feeds nest their items deeper than the textbook shape.
    for item in channel.iter("item"):
        items.append({
            "title": text_of(item, "title") or "(untitled)",
            "link": text_of(item, "link"),
            "date": text_of(item, "pubDate"),
        })
    return title, items


def show(source, limit, open_item=None):
    title, items = parse(fetch(source))
    print(f"\n== {title} ({source}) ==")
    if not items:
        print("  (no items)")
    # I slice to the limit before I number the rows, so the numbers a
    # reader sees always start at 1 for the first item I show.
    for i, item in enumerate(items[:limit], 1):
        date = item["date"]
        try:
            # I swap a trailing Z for an offset that fromisoformat can
            # read. Atom dates use that Z form a lot.
            date = datetime.fromisoformat(date.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except ValueError:
            # RSS pubDate uses the RFC 822 shape, which fromisoformat
            # cannot read. I show the first 16 characters instead,
            # because that slice is the weekday and the date, and I
            # would rather show part of the date than drop it.
            date = date[:16]
        print(f"{i:>3}. {item['title']}")
        # I print the link on the date line when I have a date, and on
        # its own line when I do not, so a dateless item does not start
        # with a blank gap.
        if date:
            print(f"     {date}  {item['link']}")
        elif item["link"]:
            print(f"     {item['link']}")
    if open_item is not None:
        # I check the open number against the full item list, not the
        # limited slice above. A caller can ask for a link past the
        # limit they chose for the listing.
        if 1 <= open_item <= len(items):
            print(f"  open[{open_item}]: {items[open_item - 1]['link']}")
        else:
            # I print how many items the feed has when the number is
            # out of range. That tells the caller what range would
            # have worked without making the run a failure.
            print(f"  open[{open_item}]: this feed has {len(items)} item(s)")
    return items


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read RSS/Atom feeds in the terminal.")
    parser.add_argument("feeds", nargs="+", help="feed URLs or local feed files")
    parser.add_argument("--limit", type=int, default=10, help="items per feed (default 10)")
    parser.add_argument("--open", type=int, metavar="N", default=None,
                        help="print item N's link on its own line after the listing")
    args = parser.parse_args(argv)
    failures = 0
    for source in args.feeds:
        try:
            show(source, args.limit, args.open)
        except Exception as exc:
            # I catch per feed and keep going. One bad feed must not
            # kill the rest of a multi feed run, because the feeds do
            # not depend on each other at all.
            failures += 1
            print(f"\n== {source} ==\n  error: {exc}", file=sys.stderr)
    # I only fail the run when every feed failed. A run that got one
    # good listing did its job, so I do not mark it as an error for a
    # script that checks my exit code.
    return 1 if failures == len(args.feeds) else 0


if __name__ == "__main__":
    raise SystemExit(main())
