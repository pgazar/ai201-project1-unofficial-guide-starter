# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

An unofficial **college survival guide for Northeastern University**, built from candid r/NEU threads. It covers the lived-experience knowledge students actually need: which dorms have no AC, whether the meal plan is worth its cost, how an OSCCR conduct hearing really goes, how to sublet a room during co-op, and how to cope as a struggling freshman. This knowledge is valuable because official channels (the university website, housing handbook, orientation materials) present sanitized, policy-focused information, while the honest, specific, experience-based answers live scattered across individual Reddit threads and aren't consolidated or searchable anywhere.

---

## Documents

All 11 documents are individual r/NEU threads (post + comments) scraped via Apify (`trudax/reddit-scraper-lite`) and saved as `.txt` files in `documents/`.

| # | Source (thread title) | Description | URL |
|---|-----------------------|-------------|-----|
| 1 | "Freshman vent" | Lonely/isolated freshman during COVID; replies on adjusting & finding community | https://www.reddit.com/r/NEU/comments/iynjsa/freshman_vent/ |
| 2 | "I've gone to OSCCR six times, this will help you" | First-hand walkthrough of the OSCCR student-conduct hearing process | https://www.reddit.com/r/NEU/comments/83i16g/ive_gone_to_osccr_six_times_this_will_help_you/ |
| 3 | "Res Life and this Covid Shit" | RA's account of COVID quarantine/res-life policy and dorm realities | https://www.reddit.com/r/NEU/comments/s0z8sr/res_life_and_this_covid_shit/ |
| 4 | "NEU Meal Plans are Ridiculously Expensive (No Hungry Huskies)" | Campaign post on meal-plan cost and campus food insecurity | https://www.reddit.com/r/NEU/comments/sy2lcw/neu_meal_plans_are_ridiculously_expensive_but/ |
| 5 | "How do students sublet at Northeastern?" | Q&A on subletting a Boston room during co-op | https://www.reddit.com/r/NEU/comments/1orrryn/how_do_students_sublet_at_northeastern/ |
| 6 | "Achieving resume success" | Long-form resume / job-search / networking advice | https://www.reddit.com/r/NEU/comments/v1xb1u/achieving_resume_success/ |
| 7 | "how are y'all doing" | Cross-Boston mental-health check-in; coping & solidarity | https://www.reddit.com/r/NEU/comments/q9ssun/how_are_yall_doing/ |
| 8 | "OSSCR Being Unbelievably Unfair and Unreasonable" | Student's unfair academic-integrity case; advice in replies | https://www.reddit.com/r/NEU/comments/z2de8l/osscr_being_unbelievably_unfair_and_unreasonable/ |
| 9 | "The Real Issue with the New Meal Plans" | Detailed cost breakdown of block meal plans + dining-dollar tips | https://www.reddit.com/r/NEU/comments/1ef28fy/the_real_issue_with_the_new_meal_plans/ |
| 10 | "Advice for concerned freshmen!" | "Does it get better after freshman year" advice megapost | https://www.reddit.com/r/NEU/comments/829zqe/advice_for_concerned_freshmen/ |
| 11 | "Melvin Hall (Boston)" | First-hand Melvin Hall dorm review (layout, AC, access, bathrooms) | https://www.reddit.com/r/NEU/comments/1suvooa/melvin_hall_boston/ |

**Coverage:** mental health / adjustment (#1, #7, #10), student conduct / OSCCR (#2, #8), res life & dorms (#3, #11), dining / meal plans (#4, #9), off-campus housing & subletting (#5), career / co-op prep (#6).

---

## Chunking Strategy

**Chunk size:** 800 characters (~180 tokens)

**Overlap:** 150 characters

**Reasoning:**

Strategy is *structure-aware splitting first, then a size cap with overlap*:

1. **Split on natural boundaries** — each document breaks at the post body and at every individual comment (files mark these with `POST:` and `[comment by u/...]`); long posts split further at paragraph breaks. One chunk = one self-contained thought (a single comment, or one paragraph of advice).
2. **Size cap** — any piece still longer than 800 characters is split further so no chunk exceeds the cap; short pieces stay whole.
3. **Overlap** — 150 characters between size-capped sub-chunks.

Why these numbers fit this corpus:
- The corpus is **mixed**: mostly short, self-contained opinion comments, plus a few long-form guides (#2 OSCCR walkthrough, #9 meal-plan breakdown are ~2,500-word posts). Splitting on comment/paragraph boundaries keeps one opinion together (good for semantic matching), while the 800-char cap stops the long guides from becoming giant multi-topic chunks too diluted to match a specific query.
- 800 chars stays **under all-MiniLM-L6-v2's ~256-token (~1,000-char) input limit**, so every chunk is embedded in full — nothing past the limit is silently dropped and lost to retrieval. A 1,500-char chunk would have its back half ignored by the model.
- 150-char overlap covers multi-sentence advice that crosses a paragraph boundary in the long posts (e.g. a sanction described across two sentences in #2).
- Sanity check: ~88K characters across 11 docs → roughly **120–140 chunks**, inside the assignment's healthy 50–2,000 range. (Actual count recorded after the pipeline runs in Milestone 3.)

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers` — 384-dim, runs locally with no API key or rate limits, fast. Stored in ChromaDB with cosine similarity.

**Top-k:** 5. The chunks are mostly comment-sized, so 5 pulls in enough corroborating voices (e.g. several students' takes on the meal plan) for the LLM to synthesize a grounded answer. Too few (k=1-2) risks missing the relevant chunk if it ranked just below the top; too many (k=10+) drags in loosely related chunks that dilute the context and pull the answer off-target.

**Production tradeoff reflection:** If cost weren't a constraint:
- **Domain accuracy** — a larger model (`bge-large-en`, OpenAI `text-embedding-3-large`, Cohere `embed-v3`) captures nuance, sarcasm, and slang in opinion text better than MiniLM's 384 dims. Reddit advice is colloquial and ironic, which small models can misread.
- **Context length** — MiniLM truncates at ~256 tokens, which is why we chunk small. A long-context embedder (e.g. OpenAI's 8K-token model) could embed an entire long guide post as one unit, preserving cross-paragraph reasoning in #2/#9.
- **Multilingual** — not needed for English r/NEU, but a multilingual model (e.g. `multilingual-e5`) would matter if the corpus included non-English posts.
- **Latency & cost** — MiniLM is local, ~milliseconds, free. API models add network latency, per-token cost, and rate-limit/dependency risk. For a low-traffic demo, local wins; at production scale you'd weigh a hosted vector DB and batched-embedding costs.

---

## Evaluation Plan

| # | Question | Expected answer (grounded in docs) |
|---|----------|-----------------|
| 1 | Why do students say the NEU meal plan is too expensive / is it worth the cost? | Widely seen as overpriced: $7,910/yr for the 17-meal plan, ~$3,410 above the national average; ~1 in 4 students face food insecurity; new block plans cost ~3% more per meal (lowest plan up 6%), per-meal ~$12–$22.72; "dining dollars" criticized, advice to supplement at local stores not Wally's. (#4, #9) |
| 2 | What should I expect from an OSCCR hearing and how should I handle it? | Notice by email to @husky.neu.edu; officer opens with ~10–15 min small talk to soften you up; ask them to read the full report before you speak; advice is "admit nothing, deny everything," don't accept responsibility; sanctions can include a class, fine, essay, probation/deferred suspension; a hearing advisor is available. (#2) |
| 3 | What is Melvin Hall like as a first-year dorm? | No AC (heating only, on ~late October — bring fans); 5 semi-private single-use bathrooms per floor (~4 showers); one small, occasionally-broken elevator; triples/doubles/singles; no floor common areas but a basement with 3 study rooms, laundry (5 washers/6 dryers), water fountain; room access via Husky Card + last 4 of NU ID; gender-inclusive 5th floor; address 90 The Fenway. (#11) |
| 4 | How can a student sublet their room during co-op? | List the room with the off-campus housing office (offcampus.housing.northeastern.edu); post in r/bostonhousing; use Facebook groups (incl. the NU parents group); for NYC, EHS was recommended. (#5) |
| 5 | What do upperclassmen tell freshmen who feel lonely or like it isn't getting better? | It gets better after freshman year; join clubs (especially non-academic ones); study in the library to be around people; befriend upperclassmen; drop fake friends; consider getting a job. (#10, #1) |

---

## Anticipated Challenges

1. **HTML-entity and boilerplate noise.** Files contain `&#39;` (182x), `&quot;` (39x), `&#32;` (33x), plus the Reddit `submitted by /u/... [link] [comments]` footer on every post. If cleaning doesn't run before chunking, these pollute embeddings and leak into generated answers. (Mitigated by the Milestone 3 cleaning step: `html.unescape` + boilerplate strip.)

2. **Key figures split across chunk boundaries in the meal-plan docs.** #9 contains a dense cost-per-meal table ($21.39, $18.42, $14.49...). At an 800-char cap, table rows can land in different chunks, so a query about one specific plan's cost may retrieve only half the table, or pull the vaguer campaign post (#4) instead of the detailed breakdown (#9). This is the most likely failure case.

3. **Sarcasm and jokes retrieved as if they were advice.** #2 ends with Canada-geese jokes and a "go to Cheesecake Factory" aside; #7 is emotional venting. Semantic search can surface an ironic or joking comment that sounds on-topic, producing a confidently wrong grounded answer.

4. **Short reply comments with no standalone meaning.** Replies like "ill do that" or "totally worth it" embed poorly without their thread topic, causing off-topic or low-value retrievals.

---

## Architecture

```
 [1] DOCUMENT INGESTION                 [2] CHUNKING
 11 r/NEU .txt files          parse Title/URL/POST/COMMENTS -> metadata + body
 (Apify scrape)         -->   clean: html.unescape, strip footer,        -->
 load from documents/         drop [deleted], normalize whitespace
                              split on comment/paragraph boundaries,
                              then cap at 800 chars / 150 overlap
        |                                                                   |
        v                                                                   v
 [3] EMBEDDING + VECTOR STORE            [4] RETRIEVAL              [5] GENERATION
 all-MiniLM-L6-v2 (sentence-      query -> embed -> top-k=5    retrieved chunks ->
 transformers) embeds chunks  --> cosine search over       --> grounded prompt ->
 -> ChromaDB (persistent,         ChromaDB, return chunks      Groq llama-3.3-70b
 stores text + {source,           + source metadata            -> answer + cited
 url, chunk_index})                                            sources   (Gradio UI)
```

Stage -> tool: ingestion/chunking = Python (`html`, custom splitter) - embedding = `sentence-transformers` (all-MiniLM-L6-v2) - vector store = ChromaDB - retrieval = ChromaDB cosine top-k - generation = Groq (`llama-3.3-70b-versatile`) - interface = Gradio.

---

## AI Tool Plan

Tool: **Claude** (via an agentic coding session with terminal access to this repo).

**Milestone 3 - Ingestion and chunking:** Input = the Documents, Chunking Strategy, and Anticipated Challenges sections of this file, plus the `Title/URL/POST/COMMENTS` file format. Expect: a `load_documents()` that parses + cleans (html.unescape, strip footer, drop [deleted], normalize whitespace) and a `chunk_text()` that splits on comment/paragraph boundaries then caps at 800 chars / 150 overlap, attaching {source, url, chunk_index} metadata. Verify: print 5 random chunks (readable, self-contained, no HTML artifacts) and confirm total chunk count is in the 50-2,000 range.

**Milestone 4 - Embedding and retrieval:** Input = the Retrieval Approach section + the architecture diagram. Expect: code that embeds chunks with all-MiniLM-L6-v2, loads them into a persistent ChromaDB collection with metadata, and a `retrieve(query, k=5)` returning chunks + sources + distances. Verify: run 3 eval questions, confirm returned chunks are on-topic and top distances are < 0.5.

**Milestone 5 - Generation and interface:** Input = the grounding requirement (answer only from retrieved context; refuse when context is insufficient) + desired output (answer + source list) + Gradio skeleton. Expect: a grounded prompt template, a Groq call to llama-3.3-70b-versatile, programmatic source attribution, and a minimal Gradio app. Verify: test an in-scope query (answer traceable to chunks, sources cited) and an out-of-scope query (system declines instead of inventing an answer).

> Per the assignment guardrail, the spec above (chunking numbers, retrieval choices, eval questions, risks) was authored by me; AI is used to implement and pressure-test against this spec, and every generated stage is checked at the milestone checkpoints before being relied on.
