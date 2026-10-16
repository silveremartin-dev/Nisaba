# PROJECT_STATE.md — Nisaba Engineering Session Memory & Asset Registry

## 📌 1. Project Overview & Architectural Mission

* **Repository:** `https://github.com/silveremartin-dev/Nisaba`
* **Local Workspace:** `C:\Silvere\Encours\Developpement\Sumerian`
* **Mission:** High-performance computational engine and data pipeline for Sumerian cuneiform epigraphy, transforming the world's 135,254 CDLI ATF text archives into certified Apache Parquet / DuckDB databases, identifying ancient scribes and authors, resolving undated tablets via prosopography, auditing balanced economic accounts, discovering cross-collection fragment joins, and rendering interactive visual tablet explorers with real museum photos.

---

## 🏛️ 2. The Five Analytical Engines

| Analytical Engine | Module | Primary Class | Real Empirical Capabilities |
| :--- | :--- | :--- | :--- |
| **1. Ur III Economic Ledger** | `src/ledger/` | `LedgerAuditor` | Sexagesimal metrology parsing, double-entry receipts (`ki...-ta` / `i3-dab5` / `ba-zi`), net inventory balance sheets (24,018 real txs audited). |
| **2. Orphan Tablet Resolver** | `src/authors/` + `src/chronos/` | `AuthorIdentifier` & `ChronosSolver` | Seal legend extraction (`@seal`), colophons (`dub-sar`), Bayesian constraint propagation across career windows (1,009 undated tablets dated). |
| **3. Fragment Joiner** | `src/joins/` | `FragmentMatcher` | Token and character $k$-mer Jaccard alignment detecting physical and virtual joins across museum collections. |
| **4. K-mer Parquet Engine** | `src/compiler/` | `ATFParser` & `StorageEngine` | Streaming lexer and AST parser serializing into `tablets.parquet`, `lines.parquet`, `signs.parquet`, `kmers.parquet` mounted inside `nisaba.duckdb`. |
| **5. Tablet Visual Explorer** | `src/browser/` | `TabletBrowserRenderer` | Interactive standalone dark-mode HTML app (`browser.html`) with local cached high-res CDLI photos, color-coded syntax & deep-linking URL hashes. |

---

## 🧪 3. Test Suite Verification

* **Framework:** `pytest`
* **Test Count:** **30 passing tests** across 12 test suites:
  - `tests/test_authors.py` (3 tests: seal extraction, probabilistic attribution, corpus batch)
  - `tests/test_browser.py` (1 test: HTML structure, CDLI photo links, entity highlight spans, hash routing)
  - `tests/test_chronos.py` (2 tests: formula normalization, undated tablet resolution)
  - `tests/test_deep_chronos.py` (2 tests: royal year coverage, disjoint window handling)
  - `tests/test_deep_ledger.py` (2 tests: sexagesimal conversions, multi-commodity balance sheets)
  - `tests/test_deep_linter.py` (3 tests: unmatched angle brackets, unmatched parentheses, multiple sign issues)
  - `tests/test_duckdb_analytics.py` (1 test: multi-table SQL joins, sign type aggregations)
  - `tests/test_joins.py` (2 tests: k-mer Jaccard, fragment join matching)
  - `tests/test_ledger.py` (1 test: transaction extraction and balances)
  - `tests/test_lexer.py` (2 tests: streaming tokens, broken line numbering)
  - `tests/test_linter.py` (3 tests: bracket auditor, sign validator, corpus reporting)
  - `tests/test_parser.py` (2 tests: AST generation, damaged sign preservation)
  - `tests/test_pipeline.py` (2 tests: full pipeline integration and selective tool runs)
  - `tests/test_storage.py` (1 test: Parquet export and DuckDB query execution)
  - `tests/test_taxonomy.py` (3 tests: king codes, catalog uniqueness, metrology)
* **Status:** 100% Green (`30 passed in 4.97s`).

---

## 📊 4. Measured Empirical Benchmarks on Real Archival Corpus

Measured directly on 5,000 authentic Ur III tablets (`P100001` - `P105000`) from the official CDLI dump (`cdliatf_unblocked.atf`):

| Pipeline Stage | Processed Volume | Real Execution Time | Real Throughput |
| :--- | :---: | :---: | :---: |
| **Streaming Lexer & AST Parser** | **5,000 tablets** (78,897 lines, 241,858 signs) | **6.36 s** | **786 tablets/s** (12,401 lines/s) |
| **Columnar Parquet Export** | 4 tables (`tablets`, `lines`, `signs`, `kmers`) | **12.64 s** | Streamed zero-loss serialization |
| **DuckDB Ingestion & Indexing** | Mounted `nisaba.duckdb` | **Instant** | Parquet-backed views |
| **DuckDB Analytical SQL Queries** | Sign and line aggregations | **1.84 - 2.84 ms** | Sub-3ms query latencies |
| **Scribe & Author Attribution** | 5,000 tablets evaluated | **0.82 s** | **2,048 scribes identified** (41.0%) |
| **Chronos Macro-Chronology** | 5,000 tablets dated | **1.23 s** | **2,515 certified + 1,009 inferred** |
| **Ur III Economic Ledger** | 5,000 tablets audited | **2.32 s** | **24,018 transactions, 9,577 accounts** |

---

## 🖼️ 5. Certified Real Visual Assets

| File Path | Description | Visual Source |
| :--- | :--- | :--- |
| `assets/images/real_tablet_joins_showcase.png` | 3-panel real museum join showcase | `P100089` (AAS 102+205), `P131610` (Louvre AO 5521+5522), `P285811` (Geneva MAH 16064 Atrahasis) |
| `assets/images/real_browser_tablet_p100004.png` | Unedited headless Chrome UI screenshot | Tablet `P100004` (AAS 004): real photo, date resolved to AS01..AS08, scribe attributed |
| `assets/images/real_browser_tablet_p100005.png` | Unedited headless Chrome UI screenshot | Tablet `P100005` (AAS 005): real photo with CF 2 mark, candidate join with `P100009` |
| `assets/images/real_ledger_analytics_dashboard.png` | DuckDB SQL shell & ledger balance sheet | Real SQL queries across 241,858 signs, net livestock balance for Abbashaga (-2,840), Inta'ea (+1,110) |

---

## 📁 6. Certified Artifacts on Disk

| File Path | Description |
| :--- | :--- |
| `data/raw/cdliatf_unblocked.atf` | Complete official CDLI bulk dump (86.9 MB, 135,254 tablets) |
| `data/raw/sample_cdli.atf` | 15 authentic CDLI tablets covering all administrative scenarios |
| `data/processed/nisaba.duckdb` | Active embedded DuckDB database |
| `data/processed/tablets.parquet` | Columnar tablet catalog metadata |
| `data/processed/lines.parquet` | Line-by-line normalized text and preservation flags |
| `data/processed/signs.parquet` | Deconstructed sign tokens and classifications |
| `data/processed/kmers.parquet` | 4-mer index for sequence lookups |
| `data/processed/author_attributions.parquet` | Scribe identities, titles, and patronymics |
| `data/processed/chronos_estimates.parquet` | Date resolutions for certified and undated tablets |
| `data/processed/virtual_joins.parquet` | Prospective fragment join matches |
| `data/processed/transactions.parquet` | Extracted economic transaction records |
| `data/processed/officer_balances.parquet` | Net inventory balances per official |
| `data/processed/browser.html` | Self-contained interactive visual tablet explorer |
