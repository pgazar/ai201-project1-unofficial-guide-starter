"""
Milestone 5 - Grounded answer generation over retrieved chunks (Groq llama-3.3-70b).

    ask(question)  ->  {answer, sources}
                       retrieves the top-k chunks, answers ONLY from them,
                       and attaches the source title + URL of each chunk used.

Run directly to test in-scope and out-of-scope queries:  python query.py
"""

import os

from dotenv import load_dotenv
from groq import Groq

from index import retrieve, TOP_K

load_dotenv()
_client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.3-70b-versatile"
NOT_FOUND = "I don't have enough information on that."

SYSTEM = (
    "You are an assistant for an unofficial Northeastern University student survival guide. "
    "Answer the question using ONLY the numbered context passages below, which are excerpts "
    "from student-written Reddit threads. Do not use any outside knowledge or assumptions. "
    f"If the context does not contain enough information to answer, reply with exactly: "
    f"'{NOT_FOUND}' and nothing else. Keep the answer concise and specific."
)


def _format_context(chunks: list[dict]) -> str:
    return "\n\n".join(
        f'[{i}] (from "{c["title"]}")\n{c["text"]}' for i, c in enumerate(chunks, 1)
    )


def ask(question: str, k: int = TOP_K) -> dict:
    """Answer a question grounded only in the top-k retrieved chunks."""
    chunks = retrieve(question, k=k)
    prompt = f"Context:\n{_format_context(chunks)}\n\nQuestion: {question}"

    resp = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=500,
    )
    answer = resp.choices[0].message.content.strip()

    # Source attribution is programmatic: list the unique source threads that were
    # actually retrieved. Skip it when the model reports insufficient information.
    sources = []
    if NOT_FOUND.lower() not in answer.lower():
        seen = set()
        for c in chunks:
            if c["url"] not in seen:
                seen.add(c["url"])
                sources.append(f'{c["title"]} - {c["url"]}')
    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    for q in ["Is the NEU meal plan worth the cost?",   # in-scope
              "What is Melvin Hall like as a dorm?",     # in-scope
              "What's the best gym near campus?"]:        # out-of-scope
        r = ask(q)
        print(f"Q: {q}\nA: {r['answer']}")
        if r["sources"]:
            print("Retrieved from:")
            for s in r["sources"]:
                print(f"  - {s}")
        print("-" * 70)
