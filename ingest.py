"""
Milestone 3 - Document ingestion + chunking for the Unofficial Guide
(an unofficial r/NEU college survival guide).

    load_documents()   parse the 11 scraped .txt files into clean, structured docs
    chunk_documents()  split docs into <=800-char chunks (150 overlap) with metadata

Run directly to inspect the chunks:  python ingest.py
"""

import html
import random
import re
from pathlib import Path

DOCS_DIR = Path(__file__).parent / "documents"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
MIN_CHUNK_CHARS = 20   # drop trivial fragments like "lol" / "same"

# The scraper appends a footer to every post body, e.g.
#   "submitted by /u/neu_ydsa [link] [comments]"
_FOOTER_RE = re.compile(r"submitted by\s*/u/\S+.*?\[comments\]", re.IGNORECASE | re.DOTALL)
# Each comment begins with a line like "[comment by u/name]"
_COMMENT_RE = re.compile(r"^\[comment by (u/[^\]]+)\]\s*$", re.IGNORECASE | re.MULTILINE)
_SPACES_RE = re.compile(r"[ \t]+")
_BLANKLINES_RE = re.compile(r"\n{3,}")


def _clean(text: str) -> str:
    """Decode HTML entities, drop the scraper footer, normalize whitespace."""
    text = html.unescape(text)             # &#39; -> '   &#32; -> space   &quot; -> "
    text = _FOOTER_RE.sub("", text)        # remove "submitted by /u/... [comments]"
    text = _SPACES_RE.sub(" ", text)       # collapse runs of spaces/tabs
    text = _BLANKLINES_RE.sub("\n\n", text)  # collapse 3+ newlines to one blank line
    return text.strip()


def _parse_file(path: Path) -> dict:
    """Parse one scraped .txt file into {source, title, url, date, segments}."""
    raw = path.read_text(encoding="utf-8")

    def header(field: str) -> str:
        m = re.search(rf"^{field}:\s*(.+)$", raw, re.MULTILINE)
        return m.group(1).strip() if m else ""

    title, url, date = header("Title"), header("URL"), header("Date")

    # Separate the post body from the comments section.
    post_part, _, comments_part = raw.partition("--- COMMENTS ---")
    post_body = post_part.partition("POST:")[2]

    segments = []
    post_clean = _clean(post_body)
    if post_clean:
        segments.append(post_clean)

    # Split comments on their "[comment by u/...]" headers.
    # re.split with one capture group -> [pre, author1, body1, author2, body2, ...]
    if comments_part:
        for body in _COMMENT_RE.split(comments_part)[2::2]:
            c = _clean(body)
            if c and c.lower() not in ("[deleted]", "[removed]"):
                segments.append(c)

    return {"source": path.name, "title": title, "url": url,
            "date": date, "segments": segments}


def load_documents() -> list[dict]:
    """Load and clean all numbered .txt documents in documents/."""
    files = sorted(DOCS_DIR.glob("[0-9]*.txt"))
    return [_parse_file(f) for f in files]


def _split_long(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split a too-long segment into overlapping windows, breaking on spaces."""
    pieces, start, n = [], 0, len(text)
    while start < n:
        end = min(start + size, n)
        if end < n:                                  # prefer a word boundary
            space = text.rfind(" ", start + size // 2, end)
            if space != -1:
                end = space
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
        nxt = text.find(" ", start)            # start next window on a word boundary
        if nxt != -1 and nxt - start < overlap:
            start = nxt + 1
    return pieces


def chunk_documents(docs: list[dict]) -> list[dict]:
    """Turn structured docs into chunks: {id, text, source, title, url, chunk_index}."""
    chunks = []
    for doc in docs:
        idx = 0
        for segment in doc["segments"]:
            parts = [segment] if len(segment) <= CHUNK_SIZE else _split_long(segment)
            for part in parts:
                if len(part) < MIN_CHUNK_CHARS:   # skip trivial fragments
                    continue
                chunks.append({
                    "id": f"{doc['source']}::{idx}",
                    "text": part,
                    "source": doc["source"],
                    "title": doc["title"],
                    "url": doc["url"],
                    "chunk_index": idx,
                })
                idx += 1
    return chunks


if __name__ == "__main__":
    docs = load_documents()
    chunks = chunk_documents(docs)

    print(f"Loaded {len(docs)} documents")
    print(f"Produced {len(chunks)} chunks (size<={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    lengths = [len(c["text"]) for c in chunks]
    print(f"Chunk length chars: min={min(lengths)}, max={max(lengths)}, avg={sum(lengths)//len(lengths)}")
    print("Chunks per document:")
    for d in docs:
        n = sum(1 for c in chunks if c["source"] == d["source"])
        print(f"  {d['source']:<55} {n:>3}")

    print("\n----- 5 random sample chunks -----")
    random.seed(0)
    for c in random.sample(chunks, 5):
        print(f"\n[{c['id']}]  (\"{c['title']}\")")
        print(c["text"][:600])
