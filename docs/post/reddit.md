# Reddit launch post — Nisaba

## Suggested subreddits

- **r/Assyriology**: the core audience. Domain experts can judge whether the ledger extraction, date inference and scribe attribution make philological sense. Keep the tone humble and lead with the questions.
- **r/DigitalHumanities**: data-engineering angle (ATF → Parquet/DuckDB), reproducibility, and how to expose a 30-year corpus to SQL.
- **r/DataEngineering**: streaming compiler of a messy legacy text format into columnar storage, constant memory, sharded distribution. Frame it as a "weird dataset" case study.
- **r/DuckDB** (or r/Python): lighter version focused on the stack and the query latencies.
- **r/AncientNearEast** / r/ArtefactPorn (optional): only a short version with the tablet photos, linking to the repo; check self-promotion rules first.

---

**Title:** I compiled the whole CDLI cuneiform corpus (135k tablets, 2.19M lines) into DuckDB/Parquet and built some experimental tools on top: looking for Assyriologists to tell me where it's wrong

---

Hi all,

I've just open-sourced **Nisaba**, a Python toolkit that turns the Cuneiform Digital Library Initiative (CDLI) bulk ATF dump into a queryable columnar database, plus a handful of experimental analysis tools built on that database. I'm a developer, not an Assyriologist, so I'm posting mainly to get critical feedback from people who actually read these texts.

### Why

The CDLI dump is an amazing resource, but it's an ~87 MB ATF text file accumulated over decades, with heterogeneous conventions. Asking even a simple question ("which officials disbursed the most sheep at Puzrish-Dagan, and when?") usually means writing a one-off parser. I wanted a single, lossless, SQL-queryable representation where every result points back to a P-number and a line.

### What it does

1. **Streaming ATF compiler**: lexer + AST parser that keeps damage markers, broken signs and bracket structure, then writes four Parquet tables (`tablets`, `lines`, `signs`, `kmers`) mounted as DuckDB views. Runs in constant memory.
2. **Linter**: bracket parity and sign-token validation.
3. **Ur III ledger extractor**: pattern-based extraction of transfers (`ki X-ta` = from X, `Y i3-dab5` = Y took charge, `ba-zi` = disbursed), with sexagesimal metrology, then per-official net balances.
4. **"Orphan" resolver**: proposes a date range for tablets with a broken year formula by intersecting the attested career windows of the officials named on them, and proposes a scribe from seal legends/colophons (`kiszib3`, `dub-sar`, `dumu`).
5. **Fragment joiner**: token/character 4-mer Jaccard similarity to surface join or duplicate candidates.
6. **Offline HTML browser** with CDLI photos, plus a small FastAPI service.

### Numbers (measured on my machine)

- **Full corpus**: 135,253 tablets, 2,190,263 lines, 6,931,353 signs, 35,081,773 4-mers indexed, in **292 s** (~463 tablets/s). The resulting DuckDB file is ~589 MB, distributed as 15 SHA-256-checked shards.
- **5,000-tablet Ur III sample (P100001–P105000)**: parsed in 6.36 s; typical DuckDB aggregations over the 241,858 signs take ~2–3 ms.
- On that sample the heuristics produce **24,018 transactions / 9,577 accounts**, **2,515 dates read from intact formulas + 1,009 inferred**, and a scribe proposal for **2,048 tablets (41%)**.
- 42 tests in the suite.

### Important caveats (please read)

- **None of the heuristic outputs has been validated against expert ground truth.** The 1,009 inferred dates, the 2,048 scribe attributions and the join candidates are *hypotheses*. I have no precision/recall figures yet, and I'd much rather say so up front.
- The joins shown in the README (e.g. Louvre AO 5521+5522, AAS 102+205) are **already documented in CDLI**. They serve as sanity checks that the similarity measure behaves, not as discoveries.
- Ledger extraction is regex/pattern based and tuned on Ur III administrative formulae. It will miss or misread anything outside those templates (and probably some things inside them).
- Career windows for officials come from the corpus itself, so there's a circularity risk in the date inference that I haven't properly addressed.

### What it is NOT

- Not a translation tool, and not a substitute for an Assyriologist reading the tablet.
- Not a new edition of anything: it only restructures CDLI's transliterations (all credit to CDLI and its contributors).

### Feedback I'm looking for

- **Ledger semantics**: is treating `ki X-ta` / `i3-dab5` / `ba-zi` as debit/credit/clearance too naive? What common formulae am I mangling?
- **Dating**: is prosopographic window intersection a known method with known pitfalls (homonyms, long careers, father/son with the same name)? How should confidence be expressed?
- **Validation data**: is there an existing expert-curated set (dated tablets, known joins, known scribes) I could benchmark against?
- **Data engineering**: anything about the Parquet schema (e.g. how damage is encoded) that would make it more useful to you?

Repo (MIT): https://github.com/silveremartin-dev/Nisaba

Thanks for reading. Harsh but constructive criticism is very welcome.

— Silvère Martin-Michiellot
