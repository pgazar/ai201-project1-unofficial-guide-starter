"""Milestone 1 — Collect documents.

Pulls the scraped r/NEU dataset(s) (posts + comments) and writes one raw text
file per thread into documents/. Each file = a post and its comments grouped
together. Text is saved RAW (HTML entities and Reddit boilerplate intact);
cleaning happens later in the Milestone 3 pipeline.
"""

import re
import pathlib
import requests

# Apify datasets from the r/NEU survival-topics scrapes (two search runs).
DATASET_URLS = [
    "https://api.apify.com/v2/datasets/wc2KFycG4aLuRA0tw/items"
    "?signature=MC4wLlBTRVMyUDlGQkx0SHptVG9KOUQ&format=json",
    "https://api.apify.com/v2/datasets/DMpKkEnz4LgRfCjc9/items"
    "?signature=MC4wLjFRVVFxTjlDYWduSWowVEJKNzhYNQ&format=json",
]

DOCS_DIR = pathlib.Path("documents")
SKIP_BODIES = {"[removed]", "[deleted]", ""}
MAX_DOCS = 12

# Drop off-topic drama and one disturbing thread; keep practical survival advice.
EXCLUDE = ["r_ping", "frat_guys", "it_s_been_real", "not_a_flex", "vote_no_confidence", "upvote_this_if"]


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:50] or "thread"


def fetch_items():
    items = []
    for url in DATASET_URLS:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        items.extend(resp.json())
    return items


def group_threads(items):
    """Return {post_id: {'post': item, 'comments': {comment_id: item}}}."""
    posts, comments = {}, {}
    for it in items:
        if it.get("dataType") == "post":
            posts[it["id"]] = it
        elif it.get("dataType") == "comment":
            comments.setdefault(it.get("postId"), {})[it["id"]] = it  # dedupe by id
    return {
        pid: {"post": p, "comments": list(comments.get(pid, {}).values())}
        for pid, p in posts.items()
    }


def build_document(thread):
    post = thread["post"]
    lines = [
        f"Title: {post.get('title', '').strip()}",
        f"Subreddit: {post.get('communityName', 'r/NEU')}",
        f"URL: {post.get('url', '')}",
        f"Date: {post.get('createdAt', '')[:10]}",
        "",
        "POST:",
        post.get("body", "").strip(),
    ]
    if thread["comments"]:
        lines += ["", "--- COMMENTS ---"]
        for c in thread["comments"]:
            body = c.get("body", "").strip()
            if body in SKIP_BODIES:
                continue
            lines += ["", f"[comment by u/{c.get('username', 'unknown')}]", body]
    return "\n".join(lines)


def is_usable(thread):
    slug = slugify(thread["post"].get("title", ""))
    if any(bad in slug for bad in EXCLUDE):
        return False
    has_body = thread["post"].get("body", "").strip() not in SKIP_BODIES
    return has_body or len(thread["comments"]) >= 2


def main():
    DOCS_DIR.mkdir(exist_ok=True)
    threads = [t for t in group_threads(fetch_items()).values() if is_usable(t)]
    threads.sort(key=lambda t: len(t["comments"]), reverse=True)
    threads = threads[:MAX_DOCS]

    for i, thread in enumerate(threads, 1):
        text = build_document(thread)
        slug = slugify(thread["post"].get("title", ""))
        fname = DOCS_DIR / f"{i:02d}_{slug}.txt"
        fname.write_text(text, encoding="utf-8")
        print(f"  {fname.name:54s} | {len(thread['comments']):2d} comments | {len(text.split()):4d} words")

    print(f"\nSaved {len(threads)} documents to {DOCS_DIR}/")


if __name__ == "__main__":
    main()
