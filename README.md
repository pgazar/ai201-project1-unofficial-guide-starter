# The Unofficial Guide — Project 1

A Retrieval-Augmented Generation (RAG) system that answers plain-language questions about surviving Northeastern University using **only** real student-written r/NEU threads, with cited sources.

## Setup & Running

**Requirements:** Python 3.12 and a free [Groq API key](https://console.groq.com) (no credit card required).

```bash
# 1. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Groq API key
cp .env.example .env               # then edit .env: GROQ_API_KEY=your_key_here

# 4. Build the vector store (embeds the 194 chunks into ChromaDB) -- run once
python index.py

# 5. Launch the web app
python app.py                      # then open http://localhost:7860
```

> Step 4 is required on a fresh clone: the `chroma_db/` store is gitignored, so you must build it before the app can answer.

**How to query:** open http://localhost:7860, type a question in the **"Your question"** box (e.g. *"What is Melvin Hall like as a dorm?"* or *"What should I expect from an OSCCR hearing?"*), and press **Ask** (or Enter). The **Answer** box shows the grounded response; **Retrieved from** lists the source thread(s). If the documents don't cover your question, the system replies *"I don't have enough information on that."*

Other entry points:
- `python ingest.py` -- inspect the cleaned chunks (prints count + samples)
- `python query.py` -- run the in-scope / out-of-scope generation test from the command line

---

## Domain

An unofficial **college survival guide for Northeastern University**, built from candid r/NEU threads. It covers the lived-experience knowledge students actually need: which dorms have no AC, whether the meal plan is worth its cost, how an OSCCR conduct hearing really goes, how to sublet a room during co-op, and how to cope as a struggling freshman. This knowledge is valuable because official channels (the university website, housing handbook, orientation materials) present sanitized, policy-focused information, while the honest, specific, experience-based answers live scattered across individual Reddit threads and aren't consolidated or searchable anywhere.

---

## Document Sources

| # | Source (thread title) | Type | URL |
|---|-----------------------|------|-----|
| 1 | "Freshman vent" | Reddit thread (r/NEU) | https://www.reddit.com/r/NEU/comments/iynjsa/freshman_vent/ |
| 2 | "I've gone to OSCCR six times, this will help you" | Reddit thread (r/NEU) | https://www.reddit.com/r/NEU/comments/83i16g/ive_gone_to_osccr_six_times_this_will_help_you/ |
| 3 | "Res Life and this Covid Shit" | Reddit thread (r/NEU) | https://www.reddit.com/r/NEU/comments/s0z8sr/res_life_and_this_covid_shit/ |
| 4 | "NEU Meal Plans are Ridiculously Expensive (No Hungry Huskies)" | Reddit thread (r/NEU) | https://www.reddit.com/r/NEU/comments/sy2lcw/neu_meal_plans_are_ridiculously_expensive_but/ |
| 5 | "How do students sublet at Northeastern?" | Reddit thread (r/NEU) | https://www.reddit.com/r/NEU/comments/1orrryn/how_do_students_sublet_at_northeastern/ |
| 6 | "Achieving resume success" | Reddit thread (r/NEU) | https://www.reddit.com/r/NEU/comments/v1xb1u/achieving_resume_success/ |
| 7 | "how are y'all doing" | Reddit thread (r/NEU) | https://www.reddit.com/r/NEU/comments/q9ssun/how_are_yall_doing/ |
| 8 | "OSSCR Being Unbelievably Unfair and Unreasonable" | Reddit thread (r/NEU) | https://www.reddit.com/r/NEU/comments/z2de8l/osscr_being_unbelievably_unfair_and_unreasonable/ |
| 9 | "The Real Issue with the New Meal Plans" | Reddit thread (r/NEU) | https://www.reddit.com/r/NEU/comments/1ef28fy/the_real_issue_with_the_new_meal_plans/ |
| 10 | "Advice for concerned freshmen!" | Reddit thread (r/NEU) | https://www.reddit.com/r/NEU/comments/829zqe/advice_for_concerned_freshmen/ |
| 11 | "Melvin Hall (Boston)" | Reddit thread (r/NEU) | https://www.reddit.com/r/NEU/comments/1suvooa/melvin_hall_boston/ |

---

## Chunking Strategy

**Chunk size:** 800 characters (~180 tokens)

**Overlap:** 150 characters

**Why these choices fit your documents:**

The corpus mixes many short, self-contained Reddit comments with a few long-form guide posts (the OSCCR walkthrough and the meal-plan breakdown run ~2,500 words). Chunking splits on natural boundaries first — the post body and each individual comment, with long posts split further at paragraph breaks — so one chunk holds one complete thought. Any piece still over 800 characters is then capped, which stops the long guides from becoming diluted multi-topic chunks. 800 characters also stays under `all-MiniLM-L6-v2`'s ~256-token input limit, so every chunk is embedded in full rather than silently truncated. The 150-character overlap preserves advice that spans a paragraph break.

**Preprocessing before chunking:** load the 11 `.txt` files; parse the `Title / URL / POST / COMMENTS` structure into metadata + body; decode HTML entities (`&#39;`, `&quot;`, `&#32;`, `&lt;`, `&gt;`, `&amp;`) with `html.unescape()`; strip the Reddit `submitted by /u/… [link] [comments]` footer; drop `[deleted]` / `[removed]` and empty comments; normalize whitespace. Each chunk keeps its source title and URL as metadata for citations.

**Final chunk count:** 194 chunks across 11 documents (chunk length: min 22, max 799, avg 461 characters). A minimum-length filter of 20 characters drops trivial fragments (e.g. one-word comments).

---

## Sample Chunks

Five representative chunks (each from a different source document), as produced by `ingest.py`:

1. **`11_melvin_hall_boston.txt::4`** -- *Melvin Hall (Boston)* (209 chars)
   > I LOVED living in Melvin on the second floor. I had a single but I know some doubles can be a bit cramped. The location is incredible, I loved being able to walk around the fens and being on the edge of campus

2. **`02_..._osccr_six_times....txt::16`** -- *I've gone to OSCCR six times, this will help you.* (570 chars)
   > ...What is most important is not letting OSCCR hurt the group you are being sent with. When everybody has had their meeting, go out to Cheesecake Factory... I hope this helped, and I wish everyone the best with their OSCCR experiences.

3. **`05_how_do_students_sublet_at_northeastern.txt::0`** -- *How do students sublet at Northeastern?* (518 chars)
   > I just got offered at co-op at HSBC in New York for spring 2026... I need to sublet my room in Boston and find housing in NYC that is affordable. My co-op advisor told me to use Facebook groups... It costs $2400 per month for a shared dorm room. Any advice?

4. **`09_the_real_issue_with_the_new_meal_plans.txt::10`** -- *The Real Issue with the New Meal Plans* (492 chars)
   > ...on these new block meal plans, if you stay over winter break you are very likely to run out of meals before the new plans start... These new meal plans will result in more profit for Northeastern at the expense of the quality of life for the majority of its students.

5. **`10_advice_for_concerned_freshmen.txt::7`** -- *Advice for concerned freshmen!* (377 chars)
   > ...Maybe you're CCIS -- send them that cool script you wrote to automate some task. CSSH or CAMD -- send a piece of your writing or an art project... If you have any other advice, suggestions, or just want to plug your student org, PLEASE DO SO!!

Each chunk carries `{source, title, url, chunk_index}` metadata, which is what makes the citations in answers possible.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` (via `sentence-transformers`). Chosen because it runs locally with no API key or rate limits, is fast, and produces compact 384-dim vectors that work well for short opinion text. Retrieval uses cosine similarity over ChromaDB with **top-k = 5**.

**Production tradeoff reflection:** If deploying for real users with no cost constraint, I'd weigh:
- **Accuracy on domain-specific text** — a larger model (`bge-large-en`, OpenAI `text-embedding-3-large`, Cohere `embed-v3`) better captures sarcasm, slang, and nuance in Reddit opinion text than MiniLM's 384 dims.
- **Context length** — MiniLM truncates at ~256 tokens (the reason chunks are kept ≤800 chars). A long-context embedder could embed a whole long guide post as one unit, preserving cross-paragraph reasoning.
- **Multilingual support** — unnecessary for English r/NEU, but important if the corpus included other languages.
- **Latency & local vs. API** — MiniLM is local, near-instant, and free; API-hosted models add network latency, per-token cost, and rate-limit/availability risk. Local is the right call for a low-traffic demo; production scale shifts the calculus toward hosted infra and batched embedding.

---

## Retrieval Test Results

Three test queries against ChromaDB (cosine distance, top-k=5; top-3 shown):

**Query 1 -- "Why do students say the NEU meal plan is too expensive?"**

| Rank | Distance | Source | Chunk excerpt |
|------|----------|--------|---------------|
| 1 | 0.246 | #4 No Hungry Huskies | "My 2 cents: I'm not so sure guaranteed 3 meals/day is appropriate for all..." |
| 2 | 0.249 | #4 No Hungry Huskies | "Lots of students are on 12 meal/week plans because they can't afford more..." |
| 3 | 0.336 | #9 Real Issue Meal Plans | "...students have been complaining about the meal plans offered by Northeastern..." |

*Why relevant:* all three are from the two meal-plan documents and directly address affordability. Distances of 0.25-0.34 indicate a strong semantic match.

**Query 2 -- "What should I expect from an OSCCR hearing?"**

| Rank | Distance | Source | Chunk excerpt |
|------|----------|--------|---------------|
| 1 | 0.427 | #2 OSCCR guide | "...a hearing advisor prior to the hearing. A list of trained hearing advisors..." |
| 2 | 0.432 | #2 OSCCR guide | "...calmly but firmly state 'would you mind reading all of the report.'..." |
| 3 | 0.436 | #2 OSCCR guide | "Hello r/NEU code of conduct breakers... I have been sent to OSCCR six times..." |

*Why relevant:* all three come from the first-hand OSCCR walkthrough and describe the hearing process itself -- exactly what the query asks.

**Query 3 -- "How can a student sublet their room during co-op?"** (weaker -- see Failure Case)

| Rank | Distance | Source | Chunk excerpt |
|------|----------|--------|---------------|
| 1 | 0.484 | #5 sublet thread | "I just got offered at co-op at HSBC... I need to sublet my room in Boston..." |
| 2 | 0.532 | #10 freshman advice | "...on my first co-op most of my friends did their co-ops out of Boston..." |
| 3 | 0.558 | #10 freshman advice | "...the disruption that comes with co-op..." |

Only the top result is on-target (and it is the question post itself); ranks 2-3 drift off-topic and distances are higher (0.48-0.56). This causes the Q4 failure below.

---

## Grounded Generation

**System prompt grounding instruction:** The Groq model receives a system prompt that says to answer *"using ONLY the numbered context passages below... Do not use any outside knowledge or assumptions,"* and *"If the context does not contain enough information to answer, reply with exactly: 'I don't have enough information on that.'"* It runs at `temperature=0`. The retrieved chunks are formatted as numbered, titled passages in the user message, so the model only ever sees the top-k retrieved text -- never the full corpus or any external source. This is why the out-of-scope "best gym near campus" query returns the refusal instead of a guess.

**How source attribution is surfaced in the response:** Programmatically, not by the model. After generation, `ask()` collects the unique `(title, url)` pairs from the chunks that were actually retrieved and returns them as a `sources` list shown under "Retrieved from." When the model returns the refusal, the sources list is suppressed. Every substantive answer is therefore backed by named source threads.

---

## Example Responses

**In-scope (grounded + cited):**

> **Q:** What should I expect from an OSCCR hearing and how should I handle it?
> **A:** The hearing uses a "preponderance of information" / "more likely than not" standard. Calmly and firmly ask the administrator to read the full report before you speak; the poster's advice is "admit nothing, deny everything." Don't plead your case by email/phone beforehand, don't accept responsibility, and consider a hearing advisor.
> **Retrieved from:** I've gone to OSCCR six times, this will help you. -- https://www.reddit.com/r/NEU/comments/83i16g/ive_gone_to_osccr_six_times_this_will_help_you/

> **Q:** What is Melvin Hall like as a first-year dorm?
> **A:** Melvin Hall is "a pretty good dorm compared to some of the first-year dorms," with a great location near the Fens. Some doubles are cramped. It has semi-private bathrooms, a laundry room, and no AC (heating only). One student described their floor as feeling like "family."
> **Retrieved from:** Melvin Hall (Boston) -- https://www.reddit.com/r/NEU/comments/1suvooa/melvin_hall_boston/

**Out-of-scope (refusal):**

> **Q:** What is the best gym near campus?
> **A:** I don't have enough information on that.
> **Retrieved from:** (none -- the documents don't cover this)

---

## Query Interface

A Gradio web app (`app.py`); run `python app.py` and open http://localhost:7860.

- **Input field:** a single "Your question" text box (submit with the **Ask** button or Enter).
- **Output fields:** an **Answer** box and a **Retrieved from** box listing the source thread(s) with URLs.

Sample interaction transcript:

```
Your question:  What is Melvin Hall like as a first-year dorm?

Answer:         Melvin Hall is "a pretty good dorm compared to some of the first-year
                dorms," with a great location near the Fens. Some doubles are cramped.
                It has semi-private bathrooms, a laundry room, and no AC (heating only).

Retrieved from: - Melvin Hall (Boston) -
                  https://www.reddit.com/r/NEU/comments/1suvooa/melvin_hall_boston/
```

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Why do students say the NEU meal plan is too expensive? | Overpriced: $7,910/yr (~$3,410 above national avg), unused swipes, lower plans raised most, per-meal ~$12-$22.72 (#4, #9) | Correctly explains poor value -- unused swipes, high cost per meal, lower plans raised most, food waste while students cannot afford meals -- but omits the specific figures | Relevant | Partially accurate |
| 2 | What should I expect from an OSCCR hearing and how should I handle it? | Notice to husky.neu.edu; small talk; ask them to read the report first; "admit nothing, deny everything"; sanctions: class/fine/essay/probation (#2) | Accurately lists the preponderance standard, asking them to read the report first, "admit nothing / deny everything," not pleading beforehand, not accepting responsibility, using a hearing advisor | Relevant | Accurate |
| 3 | What is Melvin Hall like as a first-year dorm? | No AC; semi-private bathrooms; small elevator; basement study rooms + laundry; gender-inclusive 5th floor; 90 The Fenway (#11) | Captures location, cramped doubles, semi-private bathrooms, no AC, laundry, the "family" floor; minor imprecision (says "common areas," which the floors lack) | Relevant | Accurate (minor imprecision) |
| 4 | How can a student sublet their room during co-op? | Off-campus housing office (offcampus.housing.northeastern.edu); r/bostonhousing; Facebook groups; EHS for NYC (#5) | Only says "use Facebook groups"; misses the off-campus housing office, r/bostonhousing, and EHS -- the most actionable advice | Partially relevant (off-topic #10 chunks ranked above the answer comments) | Partially accurate |
| 5 | What do upperclassmen tell freshmen who feel lonely? | It gets better; join clubs; study in the library; befriend upperclassmen; drop fake friends (#10, #1) | "It gets better," you are not alone, everyone pretends to love it, it takes time to find friend groups, get involved | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** Q4 -- "How can a student sublet their room during co-op?"

**What the system returned:** Only that a student can sublet "by using Facebook groups, as recommended by a co-op advisor," noting no specific groups were named. It omitted the concrete advice that *is* in the corpus: contacting the off-campus housing office (offcampus.housing.northeastern.edu), posting in r/bostonhousing, and EHS for NYC housing.

**Root cause (retrieval ranking).** For this query, retrieval ranked the original *question* post (`05::0`, distance 0.484) first, then two **off-topic** chunks from a different document (#10, co-op disruption / friends relocating, distances 0.532 and 0.558) above the *answer* comments in #5 that actually contain the housing-office link and the r/bostonhousing tip. Those resource-bearing comments fell outside the top-5, so the model never saw them. The distances here (0.48-0.56) are higher than the meal-plan and OSCCR queries (0.25-0.44): the short, link-heavy answer comments ("Contact the off campus housing office to list your place: <url>") share few words with a natural-language query, so the small embedding model under-ranked them. This is Anticipated Challenge #2/#4 from `planning.md` playing out.

**What you would change to fix it:** (a) raise top-k to ~8-10 so the resource comments are included; (b) add hybrid keyword (BM25) search so exact terms like "housing office" surface the answer comments; (c) prepend the thread title to each comment before embedding so short replies inherit their topic; or (d) keep the question post from competing with its own answers for retrieval slots.

---

## Spec Reflection

**One way the spec helped you during implementation:** Writing the Chunking Strategy section first forced an explicit, justified decision (800 chars / 150 overlap, chosen against all-MiniLM-L6-v2's ~256-token limit) *before* any code existed, so the implementation had a concrete target and the chunk-count range (50-2,000) was a ready-made validation check. The Anticipated Challenges section also paid off: Challenge #2 predicted that meal-plan / multi-comment information could be split or out-ranked -- exactly the Q4 failure that later appeared.

**One way your implementation diverged from the spec, and why:** The spec didn't include a minimum-chunk-length filter. During the Milestone 3 inspection a 4-character fragment appeared, so I added a 20-character minimum (plus a word-boundary snap so chunks don't start mid-word) to drop trivial one-word comments -- a refinement that only became obvious after seeing real output. The final chunk count (194) also came in higher than the ~120-140 estimate, because splitting on every comment boundary produced more short chunks than expected.

---

## AI Usage

**Instance 1 -- ingestion + chunking**

- *What I gave the AI:* the Documents, Chunking Strategy, and Anticipated Challenges sections of `planning.md`, plus the `Title / URL / POST / COMMENTS` file format.
- *What it produced:* `ingest.py` with `load_documents()` (HTML-entity decoding, footer stripping, `[deleted]`/`[removed]` removal, whitespace normalization) and `chunk_documents()` (split on comment/paragraph boundaries, then cap at 800 chars / 150 overlap with metadata).
- *What I changed or overrode:* after inspecting the first run I directed adding a 20-character minimum-length filter (a 4-char fragment had slipped through) and a word-boundary snap so overlap windows don't begin mid-word.

**Instance 2 -- embedding, retrieval, generation**

- *What I gave the AI:* the Retrieval Approach section and the grounding requirement (answer only from retrieved context; refuse otherwise; attach sources).
- *What it produced:* `index.py` (ChromaDB persistent store, cosine, top-k=5) and `query.py` (a strict grounded prompt to Groq `llama-3.3-70b-versatile` plus programmatic source attribution).
- *What I changed or overrode:* a terse test phrasing made the model wrongly refuse; rather than loosening the grounding prompt, I verified against the fuller eval-plan phrasings, kept the strict grounding, and documented the conservative refusal as an honest finding instead of masking it.
