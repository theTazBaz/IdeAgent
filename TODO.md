# TODO

## 1. Run the P@k evaluation

**Why:** the slides promise P@k against a cosine baseline. The harness is built and tested on synthetic data, but it has never run on real data. Until it does, we don't know whether the query rewrite, the live lookup or the reasoning scorer (R) actually help, and the λ weights (`LAMBDA_COS = 0.4`, `LAMBDA_R = 0.6`) are guesses.

**Why people have to label:** relevance judgements must come from us. If an LLM labels the results, the evaluation is circular and flatters the LLM-based scorer.

### Steps

1. **Review the queries.** Edit [pipeline/eval/queries.json](pipeline/eval/queries.json) (30 starter queries). Keep a mix of:
   - song from a movie or character
   - movie from a movie
   - character from a character
   - open mood questions with no reference
   - references that are *not* in the DB, which test the live lookup

   Replace anything our users wouldn't really ask.
2. **Collect candidates** (about 30+ minutes, because Groq limits `qwen/qwen3.8-27b` to 1,000 output tokens/min; it is cached and resumes if interrupted):
   ```
   my_env/bin/python -m pipeline.eval.make_pool
   ```
   Use `--limit 5` to try a few first. This only reads the database. It writes `pipeline/eval/cache.json` (git-ignored) and `pipeline/eval/pool.json`.
3. **Label.** In [pipeline/eval/pool.json](pipeline/eval/pool.json), set `"relevant": true` or `false` on every candidate (about 15–20 per query).
   - Decide the rule together first, e.g. *"relevant = a creator could sensibly use this for the request"*, so labels are consistent.
   - Have two people label independently, then reconcile, if time allows.
   - Aim for at least 30 queries with at least one `true`.
   - Re-running `make_pool` keeps existing labels.
4. **Run the evaluation** (no DB or LLM calls):
   ```
   my_env/bin/python -m pipeline.eval.run_eval
   ```
   It compares: naive cosine, rewrite, rewrite + live lookup, R only, cos + R. It reports P@1/3/5 and MRR, a bootstrap 95% interval vs naive, and a λ sweep.
5. **Act on the results.**
   - Set `LAMBDA_COS` and `LAMBDA_R` in [pipeline/rag.py](pipeline/rag.py) from the sweep. With ~30 queries the sweep overfits easily, so prefer a round value in a flat region.
   - Put the table in the slides.

### Things to keep in mind
- The DB has duplicate rows. The evaluation de-duplicates by name, but results shown to users can still repeat.
- Items in the top 5 that aren't in `pool.json` count as non-relevant. `run_eval` prints the unlabelled share; if it's high, label more.
- The evaluation ranks **without** the trend term on purpose (`trends=None`). Static labels can't measure trend.
- The `idea` lines in answers are LLM-written and are not evaluated here.

## 2. Open decisions for the team

- **Trend (built, option B: live Last.fm lookup, in-memory cache, no DB writes).** See [pipeline/trend.py](pipeline/trend.py). Songs get `T = 0.35·popularity + 0.65·chart presence` (log-scaled Last.fm listeners, plus rank in Last.fm's current global top 1000). Needs `LASTFM_API_KEY` in `.env`; without it the app just ranks without trend. Open questions for the team:
  - `LAMBDA_T = 0.15` and the 0.35/0.65 split are guesses. Static P@k labels can't test trend, so the team needs another check (e.g. do trending songs rise without hurting fit?).
  - Last.fm popularity is all-time, and only 13% of our songs are in the current chart. Is that enough "trending" for the pitch?
  - Trend is songs-only on purpose (matches the data model slide: only Song has a trend score). A movie trend was considered and dropped: it would favour new releases over better fits, needs DB columns, and can't be evaluated with static labels. Cheap to add later if wanted, since candidates without a trend are ranked neutrally.
  - If we ever store scores in `songs.trend_score`, add the decay `T0·e^(−k·age)`; live lookups don't need it.
- **DB changes (need everyone's agreement, nothing has been run):**
  - UNIQUE constraints on movie title, (movie, character name), (song title, artist), after cleaning up existing duplicates (about 12 duplicated character groups and 108 duplicated song groups at last check).
  - `relationships.raw_facts` column.
  - `songs.gat_embedding` column (needed for HGAF).
- **Groq limits.** The output cap of 1,000 tokens/min allows roughly 1–2 questions per minute. Decide whether to switch model or tier before any demo.

## 3. Still to build

- HGAF (graph attention fusion) and `gat_embedding`.
- Read-side de-duplication of repeated rows in results.
- Production basics: auth and rate limiting on `/api/search`, DB connection pooling, streaming progress to the UI.
- Update README, USER_GUIDE and the slides to match the code (see the issues found in the mid-eval deck review).
